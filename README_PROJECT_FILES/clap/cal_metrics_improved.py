import os
import re
import datetime
import subprocess
import argparse
import json
import logging
import shutil
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Any
import warnings

import torch
import torchaudio
import torchaudio.transforms as T
import pandas as pd
import soundfile as sf
import librosa
import numpy as np
import scipy.linalg
import scipy.stats
from einops import rearrange
from tqdm import tqdm

# Configure logging with more detailed output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cal_metrics_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Optional imports with error handling
try:
    import openl3
    OPENL3_AVAILABLE = True
    logger.info("✅ OpenL3 imported successfully")
except ImportError:
    OPENL3_AVAILABLE = False
    logger.warning("❌ OpenL3 not available. FD metric will be disabled.")

try:
    import laion_clap
    CLAP_AVAILABLE = True
    logger.info("✅ LAION CLAP imported successfully")
except ImportError:
    CLAP_AVAILABLE = False
    logger.warning("❌ LAION CLAP not available. CLAP metric will be disabled.")

try:
    from hear21passt.base import load_model, get_scene_embeddings
    # Import torch to access model logits
    import torch.nn.functional as F
    PASST_AVAILABLE = True
    logger.info("✅ PaSST (hear21passt) imported successfully")
except ImportError:
    PASST_AVAILABLE = False
    logger.warning("❌ PaSST (hear21passt) not available. KL divergence will be disabled.")

try:
    from stable_audio_tools.models import create_model_from_config
    from stable_audio_tools.models.utils import load_ckpt_state_dict, remove_weight_norm_from_model
    from stable_audio_tools.inference.generation import generate_diffusion_cond
    STABLE_AUDIO_AVAILABLE = True
    logger.info("✅ Stable Audio Tools imported successfully")
except ImportError:
    STABLE_AUDIO_AVAILABLE = False
    logger.warning("❌ Stable Audio Tools not available. Audio generation will be disabled.")

# Hardcoded configuration values from original script
CKPT_PATH = "/home/casio/stable-audio-tools/lightning_logs/f1cq7qt1/checkpoints/epoch=7-step=90000.ckpt"
DIT_CONFIG = "/home/casio/stable-audio-tools/configs/diffussion_model_config.json"
VAE_CONFIG = "/home/casio/stable-audio-tools/configs/autoencoder_model_config.json"
VAE_CKPT = 'vae_epoch96_unwrapped.ckpt'
REFERENCE_AUDIO_DIR = "/data/CLAP/audiocaps_raw_audio"
EVAL_CSV_PATH = "eval_prompts.csv"

logger.info(f"📁 Configuration paths:")
logger.info(f"   CKPT_PATH: {CKPT_PATH}")
logger.info(f"   DIT_CONFIG: {DIT_CONFIG}")
logger.info(f"   VAE_CONFIG: {VAE_CONFIG}")
logger.info(f"   VAE_CKPT: {VAE_CKPT}")
logger.info(f"   REFERENCE_AUDIO_DIR: {REFERENCE_AUDIO_DIR}")
logger.info(f"   EVAL_CSV_PATH: {EVAL_CSV_PATH}")

# Generation parameters
GENERATION_PARAMS = {
    "seconds_total": 10,
    "steps": 50,
    "cfg_scale": 6,
    "sigma_min": 0.03,
    "sigma_max": 1000.0,
    "sampler_type": "dpmpp-3m-sde"
}

logger.info(f"🎵 Generation parameters: {GENERATION_PARAMS}")

class AudioEvaluator:
    """
    A comprehensive audio evaluation system for generative models.
    """
    
    def __init__(self):
        logger.info("🚀 Initializing AudioEvaluator...")
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"💻 Using device: {self.device}")
        
        if torch.cuda.is_available():
            logger.info(f"🎮 CUDA device: {torch.cuda.get_device_name()}")
            logger.info(f"🎮 CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        
        # Initialize models
        self.clap_model = None
        self.passt_model = None
        self.dit_model = None
        self.vae_model = None
        self.output_dir = None
        
        logger.info("📂 Setting up output directory...")
        self._setup_output_directory()
        
        logger.info("🤖 Initializing models...")
        self._initialize_models()
        
        logger.info("✅ AudioEvaluator initialization complete")
    
    def _setup_output_directory(self):
        """Setup output directory based on original script logic."""
        logger.info("📂 Setting up output directory...")
        
        # Extract epoch number from checkpoint filename  
        logger.info(f"🔍 Extracting epoch from: {CKPT_PATH}")
        match = re.search(r"epoch=(\d+)", os.path.basename(CKPT_PATH))  
        epoch_num = match.group(1) if match else "0"  
        logger.info(f"📊 Extracted epoch number: {epoch_num}")
        
        self.output_dir = f"/data/epoch_{epoch_num}_eval"  
        logger.info(f"📁 Initial output directory: {self.output_dir}")

        # Avoid overwrite: if output_dir exists, append date/time  
        if os.path.isdir(self.output_dir):  
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")  
            self.output_dir = f"{self.output_dir}_{timestamp}"  
            logger.info(f"⏰ Output directory exists, appending timestamp: {self.output_dir}")
        
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            logger.info(f"✅ Output directory created: {self.output_dir}")
        except Exception as e:
            logger.error(f"❌ Failed to create output directory: {e}")
            raise
    
    def _initialize_models(self):
        """Initialize all required models."""
        logger.info("🤖 Starting model initialization...")
        
        try:
            if CLAP_AVAILABLE:
                logger.info("🎵 Loading CLAP model...")
                self._load_clap_model()
            else:
                logger.warning("⚠️  Skipping CLAP model (not available)")
            
            logger.info("🎵 Loading PaSST model...")
            self._load_passt_model()
            
            if STABLE_AUDIO_AVAILABLE:
                logger.info("🎵 Loading generation models...")
                self._load_generation_models()
            else:
                logger.warning("⚠️  Skipping generation models (not available)")
                
        except Exception as e:
            logger.error(f"❌ Error initializing models: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            raise
    
    def _load_clap_model(self):
        """Load CLAP model and processor."""
        logger.info("🎵 Loading CLAP model...")
        try:
            logger.info("📥 Loading LAION CLAP model...")
            self.clap_model = laion_clap.CLAP_Module(enable_fusion=False)
            logger.info("✅ CLAP model created")
            
            logger.info("📥 Loading CLAP checkpoint...")
            self.clap_model.load_ckpt()  # downloads default checkpoint
            logger.info("✅ CLAP checkpoint loaded")
            
            logger.info("📥 Moving CLAP model to device...")
            self.clap_model = self.clap_model.eval().to(self.device)
            logger.info("✅ CLAP model moved to device")
            
            logger.info("✅ CLAP model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load CLAP model: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            self.clap_model = None
    
    def _load_passt_model(self):
        """Load PaSST model."""
        logger.info("🎵 Loading PaSST model...")
        
        if not PASST_AVAILABLE:
            logger.warning("⚠️  PaSST (hear21passt) not available")
            self.passt_model = None
            return
            
        try:
            logger.info("📥 Loading PaSST model using hear21passt...")
            self.passt_model = load_model().to(self.device)
            self.passt_model.eval()
            logger.info("✅ PaSST model loaded and moved to device")
            logger.info("✅ PaSST model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load PaSST model: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            self.passt_model = None
    
    def _load_generation_models(self):
        """Load stable-audio-tools models for generation."""
        logger.info("🎵 Loading generation models...")
        try:
            # Validate file existence
            logger.info("🔍 Validating model files...")
            for path in [DIT_CONFIG, VAE_CONFIG, CKPT_PATH]:
                if not os.path.exists(path):
                    logger.error(f"❌ Model file not found: {path}")
                    return
                else:
                    logger.info(f"✅ Found: {path}")
            
            logger.info("🔧 Setting up model checkpoints...")
            
            # Unwrap model checkpoint using stable-audio-tools (from original script)
            epoch_num = re.search(r"epoch=(\d+)", os.path.basename(CKPT_PATH)).group(1)
            unwrapped_name = f"vae_epoch{epoch_num}_unwrapped"
            logger.info(f"📦 Unwrapped checkpoint name: {unwrapped_name}")
            
            # Run unwrapping subprocess
            try:
                logger.info("🔧 Running model unwrapping subprocess...")
                logger.info(f"🔧 Command: python unwrap_model.py --ckpt-path {CKPT_PATH} --model-config {DIT_CONFIG} --name {unwrapped_name}")
                
                result = subprocess.run([
                    "python", "unwrap_model.py",
                    "--ckpt-path", CKPT_PATH,
                    "--model-config", DIT_CONFIG,
                    "--name", unwrapped_name
                ], check=True, capture_output=True, text=True)
                
                logger.info("✅ Model unwrapping completed")
                logger.info(f"📝 Unwrap stdout: {result.stdout}")
                
                # Note: flash_attn warning is normal and doesn't affect functionality
                if "flash_attn not installed" in result.stdout:
                    logger.info("ℹ️  Flash Attention not installed - this is normal and won't affect functionality")
                
                # Move the unwrapped checkpoint into the output directory
                unwrapped_ckpt = f"{unwrapped_name}.ckpt"
                target_path = os.path.join(self.output_dir, unwrapped_ckpt)

                if os.path.isfile(unwrapped_ckpt):
                    logger.info(f"📁 Moving unwrapped checkpoint to output directory...")
                    logger.info(f"📁 Source: {os.path.abspath(unwrapped_ckpt)}")
                    logger.info(f"📁 Target: {target_path}")
                    
                    try:
                        shutil.move(unwrapped_ckpt, target_path)
                        logger.info(f"✅ Moved: {unwrapped_ckpt}")
                    except OSError as e:
                        logger.error(f"❌ Failed to move file: {e}")
                        logger.error(f"❌ This might be a cross-device issue. Trying copy + delete...")
                        try:
                            shutil.copy2(unwrapped_ckpt, target_path)
                            os.remove(unwrapped_ckpt)
                            logger.info(f"✅ Copied and deleted: {unwrapped_ckpt}")
                        except Exception as copy_error:
                            logger.error(f"❌ Copy + delete also failed: {copy_error}")
                            logger.error(f"❌ Will try to use the file in its current location")
                            # Update the path to use the current location
                            target_path = unwrapped_ckpt
                else:
                    logger.warning(f"⚠️  Unwrapped checkpoint not found: {unwrapped_ckpt}")
                    logger.warning(f"⚠️  Checking current directory for similar files...")
                    current_files = [f for f in os.listdir('.') if f.endswith('.ckpt')]
                    if current_files:
                        logger.info(f"📁 Found checkpoint files: {current_files}")
                        # Try to use the first checkpoint file found
                        target_path = current_files[0]
                        logger.info(f"📁 Using checkpoint: {target_path}")
                    else:
                        logger.error(f"❌ No checkpoint files found in current directory")
                        return
                
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to unwrap model: {e}")
                logger.error(f"❌ Return code: {e.returncode}")
                logger.error(f"❌ stdout: {e.stdout}")
                logger.error(f"❌ stderr: {e.stderr}")
                return
            except FileNotFoundError:
                logger.error(f"❌ unwrap_model.py not found in current directory")
                return
            
            logger.info("📥 Loading generation models...")
            logger.info(f"📥 Loading DiT model from config: {DIT_CONFIG}")
            self.dit_model = create_model_from_config(DIT_CONFIG)
            logger.info("✅ DiT model created")
            
            logger.info(f"📥 Loading VAE model from config: {VAE_CONFIG}")
            self.vae_model = create_model_from_config(VAE_CONFIG)
            logger.info("✅ VAE model created")
            
            # Load checkpoints
            logger.info(f"📥 Loading DiT checkpoint: {target_path}")
            self.dit_model.load_state_dict(load_ckpt_state_dict(target_path), strict=False)
            logger.info("✅ DiT checkpoint loaded")
            
            logger.info(f"📥 Loading VAE checkpoint: {VAE_CKPT}")
            self.vae_model.load_state_dict(load_ckpt_state_dict(VAE_CKPT), strict=False)
            logger.info("✅ VAE checkpoint loaded")
            
            logger.info("🔧 Removing weight norm from VAE...")
            remove_weight_norm_from_model(self.vae_model)
            logger.info("✅ Weight norm removed")
            
            # Setup for generation (exact same as original)
            logger.info("🔧 Setting up generation pipeline...")
            self.dit_model.pretransform = self.vae_model
            dtype = torch.float16
            self.dit_model.to('cuda', dtype=dtype).eval()
            logger.info("✅ Generation models loaded and configured")
            
            logger.info("✅ Generation models loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load generation models: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            self.dit_model = None
            self.vae_model = None
    
    def compute_clap_similarity(self, audio_path: str, text_prompt: str, 
                               clap_model=None, device=None, target_sr: int = 44100) -> float:
        """
        Compute CLAP audio-text similarity score using laion_clap.
        """
        logger.debug(f"🎵 Computing CLAP similarity for: {audio_path}")
        
        # Use provided model or fall back to instance model
        model = clap_model or self.clap_model
        dev = device or self.device
        
        if not model:
            logger.warning("⚠️  CLAP model not available")
            return 0.0
        
        try:
            # Load and preprocess audio using torchaudio (48kHz as per laion_clap requirements)
            logger.debug(f"📂 Loading audio file: {audio_path}")
            wav, sr = torchaudio.load(audio_path)
            logger.debug(f"📊 Audio loaded: shape={wav.shape}, sr={sr}")
            
            # Convert to mono and resample to 48kHz
            wav = wav.mean(0, keepdim=True)  # mono (1, T)
            if sr != target_sr:
                logger.debug(f"🔄 Resampling from {sr} to {target_sr}")
                wav = torchaudio.functional.resample(wav, sr, target_sr)
            
            # Get audio embedding
            logger.debug(f"🎵 Computing audio embedding...")
            audio_embedding = model.get_audio_embedding_from_data(x=wav.to(dev), use_tensor=True)
            logger.debug(f"📊 Audio embedding shape: {audio_embedding.shape}")
            
            # Get text embedding
            logger.debug(f"🎵 Computing text embedding for: '{text_prompt}'")
            text_embedding = model.get_text_embedding([text_prompt], use_tensor=True)
            logger.debug(f"📊 Text embedding shape: {text_embedding.shape}")
            
            # Compute cosine similarity
            audio_embedding = torch.nn.functional.normalize(audio_embedding, p=2, dim=-1)
            text_embedding = torch.nn.functional.normalize(text_embedding, p=2, dim=-1)
            similarity = (audio_embedding * text_embedding).sum().item()
            
            logger.debug(f"🎵 CLAP similarity: {similarity:.4f}")
            return float(similarity)
            
        except Exception as e:
            logger.error(f"❌ Error computing CLAP similarity for {audio_path}: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return 0.0
    
    def compute_openl3_embeddings(self, file_list: List[str], target_sr: int = 44100,
                                 input_repr: str = "mel128", content_type: str = "env", 
                                 embedding_size: int = 512) -> Optional[np.ndarray]:
        """
        Compute OpenL3 embeddings for audio files.
        """
        logger.info(f"🎵 Computing OpenL3 embeddings for {len(file_list)} files...")
        
        if not OPENL3_AVAILABLE:
            logger.warning("⚠️  OpenL3 not available")
            return None
        
        embeddings = []
        for i, wav_path in enumerate(tqdm(file_list, desc="Computing OpenL3 embeddings")):
            try:
                logger.debug(f"📂 Processing file {i+1}/{len(file_list)}: {wav_path}")
                
                if not os.path.exists(wav_path):
                    logger.warning(f"⚠️  Audio file not found: {wav_path}")
                    continue
                
                wav, sr = sf.read(wav_path)
                logger.debug(f"📊 Audio loaded: shape={wav.shape}, sr={sr}")
                
                if wav.ndim == 2:
                    wav = wav.mean(axis=1)
                    logger.debug("🔄 Converted stereo to mono")
                
                if sr != target_sr:
                    logger.debug(f"🔄 Resampling from {sr} to {target_sr}")
                    wav = librosa.resample(wav, orig_sr=sr, target_sr=target_sr)
                
                logger.debug(f"🎵 Computing OpenL3 embedding...")
                emb, _ = openl3.get_audio_embedding(
                    wav, target_sr,
                    input_repr=input_repr,
                    content_type=content_type,
                    embedding_size=embedding_size,
                    hop_size=0.1,
                    center=True,
                )
                embeddings.append(emb.mean(axis=0))
                logger.debug(f"✅ Embedding computed: shape={emb.mean(axis=0).shape}")
                
            except Exception as e:
                logger.error(f"❌ Error computing OpenL3 embedding for {wav_path}: {e}")
                logger.error(f"❌ Exception type: {type(e).__name__}")
                continue
        
        if not embeddings:
            logger.error("❌ No valid embeddings computed")
            return None
        
        result = np.stack(embeddings)
        logger.info(f"✅ OpenL3 embeddings computed: {result.shape}")
        return result
    
    def compute_frechet_distance(self, emb_real: np.ndarray, emb_gen: np.ndarray) -> float:
        """
        Compute Fréchet distance between real and generated embeddings.
        """
        logger.info(f"📊 Computing Fréchet distance...")
        logger.info(f"📊 Real embeddings shape: {emb_real.shape}")
        logger.info(f"📊 Generated embeddings shape: {emb_gen.shape}")
        
        try:
            mu_r = emb_real.mean(axis=0)
            mu_g = emb_gen.mean(axis=0)
            logger.debug(f"📊 Real mean shape: {mu_r.shape}")
            logger.debug(f"📊 Generated mean shape: {mu_g.shape}")
            
            cov_r = np.cov(emb_real, rowvar=False)
            cov_g = np.cov(emb_gen, rowvar=False)
            logger.debug(f"📊 Real covariance shape: {cov_r.shape}")
            logger.debug(f"📊 Generated covariance shape: {cov_g.shape}")
            
            diff = mu_r - mu_g
            diff_sq = diff.dot(diff)
            logger.debug(f"📊 Mean difference squared: {diff_sq}")
            
            # Compute sqrt of product of covariances
            logger.debug("📊 Computing covariance product...")
            covmean, _ = scipy.linalg.sqrtm(cov_r @ cov_g, disp=False)
            if np.iscomplexobj(covmean):
                covmean = covmean.real
                logger.debug("📊 Converted complex covariance to real")
            
            fd = diff_sq + np.trace(cov_r + cov_g - 2 * covmean)
            logger.info(f"✅ Fréchet distance computed: {fd:.4f}")
            return float(fd)
            
        except Exception as e:
            logger.error(f"❌ Error computing Fréchet distance: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return float('inf')
    
    def compute_passt_logits(self, file_list: List[str], 
                            passt_model=None, device=None, batch_size: int = 8) -> Optional[np.ndarray]:
        """
        Compute PaSST logits for audio files using hear21passt.
        Returns class probabilities for KL divergence computation.
        """
        logger.info(f"🎵 Computing PaSST logits for {len(file_list)} files...")
        
        model = passt_model or self.passt_model
        dev = device or self.device
        
        if not model:
            logger.warning("⚠️  PaSST model not available")
            return None
        
        all_logits = []
        
        for i in tqdm(range(0, len(file_list), batch_size), desc="Computing PaSST logits"):
            try:
                batch_paths = file_list[i:i + batch_size]
                logger.debug(f"📦 Processing batch {i//batch_size + 1}: {len(batch_paths)} files")
                
                valid_paths = []
                for path in batch_paths:
                    if not os.path.exists(path):
                        logger.warning(f"⚠️  Audio file not found: {path}")
                        continue
                    valid_paths.append(path)
                
                if not valid_paths:
                    logger.warning(f"⚠️  No valid audio files in batch {i//batch_size + 1}")
                    continue
                
                # Load audio files for this batch
                batch_audio = []
                for path in valid_paths:
                    try:
                        # Load audio using torchaudio (hear21passt expects 32kHz)
                        wav, sr = torchaudio.load(path)
                        wav = wav.mean(dim=0)  # convert to mono
                        
                        # Resample to 32kHz if needed
                        if sr != 32000:
                            resampler = T.Resample(orig_freq=sr, new_freq=32000)
                            wav = resampler(wav)
                        
                        # Ensure we have at least 1 second of audio (pad if needed)
                        min_length = 32000  # 1 second at 32kHz
                        if len(wav) < min_length:
                            wav = torch.nn.functional.pad(wav, (0, min_length - len(wav)))
                        
                        # Limit to maximum length (e.g., 10 seconds for PaSST)
                        max_length = 32000 * 10  # 10 seconds (PaSST training length)
                        if len(wav) > max_length:
                            wav = wav[:max_length]
                        
                        batch_audio.append(wav)
                        logger.debug(f"📂 Loaded: {path}, shape: {wav.shape}")
                        
                    except Exception as e:
                        logger.error(f"❌ Error loading audio {path}: {e}")
                        continue
                
                if not batch_audio:
                    continue
                
                # Convert to tensor batch
                # Pad all audio to same length
                max_len = max(audio.shape[0] for audio in batch_audio)
                batch_tensor = torch.zeros(len(batch_audio), max_len)
                for j, audio in enumerate(batch_audio):
                    batch_tensor[j, :audio.shape[0]] = audio
                
                batch_tensor = batch_tensor.to(dev)
                logger.debug(f"📦 Batch tensor shape: {batch_tensor.shape}")
                
                # Get logits from PaSST model
                with torch.no_grad():
                    # Use the model to get logits (raw predictions before softmax)
                    model.eval()
                    
                    # Convert audio to spectrograms using PaSST's preprocessing
                    # This is following the hear21passt approach
                    logits = []
                    for audio_tensor in batch_tensor:
                        # Process each audio sample individually
                        audio_input = audio_tensor.unsqueeze(0)  # Add batch dimension
                        
                        # Forward pass through the model to get logits
                        output = model(audio_input)
                        
                        # Extract logits (before softmax activation)
                        if hasattr(output, 'logits'):
                            sample_logits = output.logits
                        else:
                            # If output is directly logits
                            sample_logits = output
                        
                        logits.append(sample_logits)
                    
                    # Stack all logits
                    batch_logits = torch.cat(logits, dim=0)
                    logger.debug(f"📊 Batch logits shape: {batch_logits.shape}")
                
                all_logits.append(batch_logits.cpu().numpy())
                
            except Exception as e:
                logger.error(f"❌ Error processing batch {i}: {e}")
                logger.error(f"❌ Exception type: {type(e).__name__}")
                continue
        
        if not all_logits:
            logger.error("❌ No valid logits computed")
            return None
        
        result = np.concatenate(all_logits, axis=0)
        logger.info(f"✅ PaSST logits computed: {result.shape}")
        return result
    
    def compute_kl_divergence(self, p_ref: np.ndarray, p_gen: np.ndarray, eps: float = 1e-9) -> float:
        """
        Compute KL divergence between reference and generated distributions.
        """
        logger.info(f"📊 Computing KL divergence...")
        logger.info(f"📊 Reference distribution shape: {p_ref.shape}")
        logger.info(f"📊 Generated distribution shape: {p_gen.shape}")
        
        try:
            # Add epsilon and normalize
            p_ref = p_ref + eps
            p_gen = p_gen + eps
            p_ref = p_ref / p_ref.sum()
            p_gen = p_gen / p_gen.sum()
            
            kld = float(np.sum(p_ref * np.log(p_ref / p_gen)))
            logger.info(f"✅ KL divergence computed: {kld:.4f}")
            return kld
            
        except Exception as e:
            logger.error(f"❌ Error computing KL divergence: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return float('inf')
    
    def compute_passt_kld(self, logits_ref: np.ndarray, logits_gen: np.ndarray) -> float:
        """
        Compute KL divergence between reference and generated logits from PaSST.
        Following the Stability AI stable-audio-metrics approach.
        """
        logger.info(f"📊 Computing PaSST KL divergence...")
        logger.info(f"📊 Reference logits shape: {logits_ref.shape}")
        logger.info(f"📊 Generated logits shape: {logits_gen.shape}")
        
        try:
            # Convert logits to probabilities using softmax
            # This is the standard approach for KL divergence with neural network outputs
            
            # Apply softmax to convert logits to probabilities
            probs_ref = F.softmax(torch.from_numpy(logits_ref), dim=-1).numpy()
            probs_gen = F.softmax(torch.from_numpy(logits_gen), dim=-1).numpy()
            
            logger.debug(f"📊 Reference probabilities shape: {probs_ref.shape}")
            logger.debug(f"📊 Generated probabilities shape: {probs_gen.shape}")
            
            # Compute mean probabilities across all samples
            mean_probs_ref = probs_ref.mean(axis=0)
            mean_probs_gen = probs_gen.mean(axis=0)
            
            logger.debug(f"📊 Mean reference probabilities shape: {mean_probs_ref.shape}")
            logger.debug(f"📊 Mean generated probabilities shape: {mean_probs_gen.shape}")
            
            # Add small epsilon to avoid log(0)
            epsilon = 1e-8
            mean_probs_ref = mean_probs_ref + epsilon
            mean_probs_gen = mean_probs_gen + epsilon
            
            # Normalize to ensure they sum to 1
            mean_probs_ref = mean_probs_ref / mean_probs_ref.sum()
            mean_probs_gen = mean_probs_gen / mean_probs_gen.sum()
            
            # Compute KL divergence: KL(P || Q) = sum(P * log(P / Q))
            # Where P is reference (ground truth) and Q is generated
            kl_div = np.sum(mean_probs_ref * np.log(mean_probs_ref / mean_probs_gen))
            
            logger.info(f"✅ PaSST KL divergence computed: {kl_div:.6f}")
            return float(kl_div)
            
        except Exception as e:
            logger.error(f"❌ Error computing PaSST KL divergence: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return float('inf')
    
    def generate_audio(self, prompt: str) -> Tuple[Optional[np.ndarray], int]:
        """
        Generate audio from text prompt using the exact same logic as original script.
        """
        logger.info(f"🎵 Generating audio for prompt: '{prompt}'")
        
        if not self.dit_model:
            logger.warning("⚠️  Generation models not available")
            return None, 0
        
        try:
            conditioning = [{
                "prompt": prompt,
                "seconds_start": 0,
                "seconds_total": GENERATION_PARAMS["seconds_total"]
            }]
            logger.debug(f"🎵 Conditioning: {conditioning}")
            
            with torch.no_grad():
                logger.info("🎵 Running diffusion generation...")
                latent = generate_diffusion_cond(
                    model=self.dit_model,
                    conditioning=conditioning,
                    steps=GENERATION_PARAMS["steps"],
                    cfg_scale=GENERATION_PARAMS["cfg_scale"],
                    sigma_min=GENERATION_PARAMS["sigma_min"],
                    sigma_max=GENERATION_PARAMS["sigma_max"],
                    sampler_type=GENERATION_PARAMS["sampler_type"],
                    device='cuda',
                )
                logger.info(f"✅ Latent generated: shape={latent.shape}")
            
            # Process latent to audio (exact same as original)
            logger.info("🔄 Processing latent to audio...")
            latent = latent[:, :, : 10 * 44100]      # trim just in case
            audio = rearrange(latent, "b d n -> d (b n)").float()
            audio = audio / audio.abs().max().clamp_min(1e-7)       # peak-normalize
            audio = (audio.clamp(-1, 1) * 32767).short().cpu()      # int16 PCM
            
            logger.info(f"✅ Audio generated: shape={audio.shape}, dtype={audio.dtype}")
            return audio.numpy(), 44100
            
        except Exception as e:
            logger.error(f"❌ Error generating audio for prompt '{prompt}': {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return None, 0
    
    def load_audio_48k(self, path):
        """Load audio and resample to 48kHz for CLAP."""
        wav, sr = torchaudio.load(str(path))
        if sr != 44100:
            wav = torchaudio.functional.resample(wav, sr, 44100)
        return wav.mean(0, keepdim=True)  # mono (1, T)
    
    def embed_audio_batch(self, files):
        """Embed a batch of audio files using CLAP."""
        if not self.clap_model:
            logger.warning("⚠️  CLAP model not available for batch embedding")
            return None
        
        try:
            wavs = [self.load_audio_48k(p) for p in files]
            # pad to same length
            max_len = max(w.shape[-1] for w in wavs)
            wavs = [torch.nn.functional.pad(w, (0, max_len - w.shape[-1])) for w in wavs]
            batch = torch.cat(wavs, 0).to(self.clap_model.device)
            return self.clap_model.get_audio_embedding_from_data(x=batch, use_tensor=True)
        except Exception as e:
            logger.error(f"❌ Error in batch audio embedding: {e}")
            return None
    
    def resample_to_44100(self, audio_waveform, orig_sr):
        """Resample a waveform to 44.1 kHz using librosa."""
        logger.debug(f"🔄 Resampling from {orig_sr} to 44100 Hz")
        return librosa.resample(audio_waveform, orig_sr, 44100)
    
    def evaluate_dataset(self) -> Dict[str, float]:
        """
        Evaluate the dataset using exact same logic as original script.
        """
        logger.info("🚀 Starting dataset evaluation...")
        
        # Load the CSV of prompts (same as original)
        logger.info(f"📂 Loading evaluation CSV: {EVAL_CSV_PATH}")
        if not os.path.exists(EVAL_CSV_PATH):
            logger.error(f"❌ Evaluation CSV not found: {EVAL_CSV_PATH}")
            raise FileNotFoundError(f"Evaluation CSV not found: {EVAL_CSV_PATH}")
        
        df = pd.read_csv(EVAL_CSV_PATH)
        logger.info(f"✅ Loaded {len(df)} evaluation prompts")
        logger.info(f"📊 CSV columns: {list(df.columns)}")
        
        generated_files = []
        reference_files = []
        
        # Generate audio for each prompt (same logic as original)
        logger.info("🎵 Starting audio generation...")
        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Generating audio"):
            try:
                prompt_text = row["Most_Similar_Caption"]
                prompt_id = row["Prompt_ID"]
                
                logger.info(f"🎵 Processing prompt {idx+1}/{len(df)}: ID={prompt_id}")
                logger.info(f"🎵 Prompt text: '{prompt_text}'")
                
                # Generate audio for the prompt
                audio_waveform, model_sample_rate = self.generate_audio(prompt_text)
                if audio_waveform is None:
                    logger.warning(f"⚠️  Failed to generate audio for prompt {prompt_id}")
                    continue
                
                gen_filename = f"{prompt_id}.wav"
                gen_path = os.path.join(self.output_dir, gen_filename)
                
                logger.info(f"🔄 Resampling audio...")
                audio_waveform = self.resample_to_44100(audio_waveform, model_sample_rate)
                
                # Save generated audio to file
                logger.info(f"💾 Saving generated audio: {gen_path}")
                sf.write(gen_path, audio_waveform, 44100)
                generated_files.append(gen_path)
                logger.info(f"✅ Generated audio saved: {gen_path}")
                
                # Locate corresponding reference audio file
                youtube_id = row["youtube_id"]
                start_time = str(row["start_time"]).rstrip(".0")  # remove trailing .0 if any
                ref_filename = f"{youtube_id}_{start_time}.wav"
                ref_path = os.path.join(REFERENCE_AUDIO_DIR, ref_filename)
                reference_files.append(ref_path)
                logger.info(f"📂 Reference path: {ref_path}")
                
            except Exception as e:
                logger.error(f"❌ Error processing row {idx}: {e}")
                logger.error(f"❌ Exception type: {type(e).__name__}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                continue
        
        logger.info(f"✅ Audio generation complete: {len(generated_files)} files generated")
        
        # Resample reference files (same as original)
        logger.info("🔄 Processing reference files...")
        resampled_ref_files = []
        for i, ref_path in enumerate(reference_files):
            try:
                logger.info(f"📂 Processing reference file {i+1}/{len(reference_files)}: {ref_path}")
                
                if not os.path.exists(ref_path):
                    logger.warning(f"⚠️  Reference file not found: {ref_path}")
                    continue
                    
                # Load audio
                audio, sr = sf.read(ref_path)
                logger.debug(f"📊 Reference audio loaded: shape={audio.shape}, sr={sr}")
                
                if sr != 44100:
                    logger.info(f"🔄 Resampling reference from {sr} to 44100")
                    audio = self.resample_to_44100(audio, sr)
                
                # Optionally, save the resampled reference to a new file for metrics
                resampled_path = ref_path
                if sr != 44100:
                    resampled_path = os.path.join(self.output_dir, "resampled_" + os.path.basename(ref_path))
                    logger.info(f"💾 Saving resampled reference: {resampled_path}")
                    sf.write(resampled_path, audio, 44100)
                resampled_ref_files.append(resampled_path)
                logger.info(f"✅ Reference processed: {resampled_path}")
                
            except Exception as e:
                logger.error(f"❌ Error processing reference file {ref_path}: {e}")
                logger.error(f"❌ Exception type: {type(e).__name__}")
                continue
        
        logger.info(f"✅ Reference processing complete: {len(resampled_ref_files)} files processed")
        
        # Compute CLAP scores (same as original)
        logger.info("🎵 Computing CLAP scores...")
        clap_scores = []
        for i, row in df.iterrows():
            if i >= len(generated_files):
                logger.warning(f"⚠️  No generated file for row {i}")
                break
            try:
                prompt_text = row["Most_Similar_Caption"]
                gen_audio_path = generated_files[i]
                logger.info(f"🎵 Computing CLAP score for row {i+1}: {gen_audio_path}")
                
                # Compute CLAP cosine similarity between prompt text and generated audio
                similarity = self.compute_clap_similarity(gen_audio_path, prompt_text)
                clap_scores.append(similarity)
                logger.info(f"✅ CLAP score for row {i+1}: {similarity:.4f}")
                
            except Exception as e:
                logger.error(f"❌ Error computing CLAP score for row {i}: {e}")
                logger.error(f"❌ Exception type: {type(e).__name__}")
                continue
        
        clap_score_avg = sum(clap_scores) / len(clap_scores) if clap_scores else 0.0
        logger.info(f"✅ CLAP score average: {clap_score_avg:.4f}")
        
        # Compute OpenL3 embeddings for all audio
        logger.info("🎵 Computing OpenL3 embeddings...")
        gen_embeddings = self.compute_openl3_embeddings(generated_files)
        ref_embeddings = self.compute_openl3_embeddings(resampled_ref_files)
        
        fd_value = float('inf')
        if gen_embeddings is not None and ref_embeddings is not None:
            logger.info("📊 Computing Fréchet distance...")
            fd_value = self.compute_frechet_distance(ref_embeddings, gen_embeddings)
        else:
            logger.warning("⚠️  Skipping Fréchet distance (embeddings not available)")
        
        # Compute PaSST logits and KL divergence
        logger.info("🎵 Computing PaSST logits...")
        gen_logits_passt = self.compute_passt_logits(generated_files)
        ref_logits_passt = self.compute_passt_logits(resampled_ref_files)
        
        passt_kld = float('inf')
        if gen_logits_passt is not None and ref_logits_passt is not None:
            logger.info("📊 Computing PaSST KL divergence...")
            passt_kld = self.compute_passt_kld(ref_logits_passt, gen_logits_passt)
        else:
            logger.warning("⚠️  Skipping PaSST KLD (logits not available)")
        
        # Save metrics to JSON (same as original)
        metrics = {
            "CLAP_score": clap_score_avg,
            "FD_OpenL3": fd_value,
            "PaSST_KLD": passt_kld
        }
        
        metrics_path = os.path.join(self.output_dir, "metrics.json")
        logger.info(f"💾 Saving metrics to: {metrics_path}")
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=4)
        
        logger.info("✅ Evaluation completed")
        logger.info(f"📊 Final metrics: {metrics}")
        
        return metrics


def main():
    """Main function - simplified to match original script structure."""
    logger.info("🚀 Starting cal_metrics_improved.py")
    logger.info("=" * 60)
    
    try:
        logger.info("🤖 Creating AudioEvaluator...")
        evaluator = AudioEvaluator()
        
        logger.info("📊 Running evaluation...")
        metrics = evaluator.evaluate_dataset()
        
        logger.info("🎉 Evaluation completed successfully!")
        print("Evaluation metrics:", metrics)
        
    except Exception as e:
        logger.error(f"❌ Evaluation failed: {e}")
        logger.error(f"❌ Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise


if __name__ == "__main__":
    main() 
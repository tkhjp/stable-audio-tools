# Audio Evaluation Script Improvements

## Summary of Changes

The original `cal_metrics.py` script had several critical issues that have been addressed in the improved version:

### Key Problems Fixed

1. **🔧 Missing Variable Initialization**
   - Original: CLAP model, processor, and device were used without initialization
   - Fixed: Proper model loading with error handling

2. **🛡️ No Error Handling**
   - Original: Script would crash on missing files or model loading failures
   - Fixed: Comprehensive try-catch blocks and graceful degradation

3. **📁 Hardcoded Paths**
   - Original: Paths like `/home/casio/` and `/data/` wouldn't work on other systems
   - Fixed: Configurable paths through JSON configuration

4. **🔄 Poor Structure**
   - Original: Monolithic script with mixed concerns
   - Fixed: Clean class-based architecture with separation of concerns

5. **📦 Missing Dependencies**
   - Original: Assumed all libraries were available
   - Fixed: Optional imports with fallback behavior

## New Files Created

### 1. `cal_metrics_improved.py`
A complete rewrite of the evaluation script with:
- **Class-based architecture** (`AudioEvaluator` class)
- **Proper error handling** throughout
- **Configurable parameters** via JSON config
- **Progress tracking** with tqdm
- **Logging system** for debugging
- **Device auto-detection** (CPU/GPU)
- **Graceful fallbacks** when models aren't available

### 2. `config_example.json`
Example configuration file with all parameters:
```json
{
    "use_clap": true,
    "use_passt": true,
    "use_generation": true,
    "clap_model_name": "laion/clap-htsat-unfused",
    "dit_config": "/path/to/your/diffusion_model_config.json",
    "vae_config": "/path/to/your/autoencoder_model_config.json",
    // ... more configuration options
}
```

### 3. `combine_and_find_similar.py`
A simple script that:
- Combines `test.csv`, `train.csv`, and `val.csv` into one DataFrame
- Finds the most similar caption for each prompt using sentence transformers
- Creates `eval_prompts.csv` ready for evaluation

## Usage

### Step 1: Combine Datasets and Find Similar Captions
```bash
cd clap
python combine_and_find_similar.py
```

This will create:
- `combined_dataset.csv`: All audio captions combined
- `eval_prompts.csv`: Prompts matched with most similar captions

### Step 2: Configure the Evaluation
1. Copy `config_example.json` to `config.json`
2. Update paths to your model files and data directories
3. Adjust parameters as needed

### Step 3: Run Evaluation (if you have the models)
```bash
python cal_metrics_improved.py \
    --config config.json \
    --eval-csv eval_prompts.csv \
    --output-dir results/ \
    --verbose
```

## Key Improvements in Detail

### 1. Robust Model Loading
```python
def _load_clap_model(self):
    try:
        model_name = self.config.get('clap_model_name', 'laion/clap-htsat-unfused')
        self.clap_processor = ClapProcessor.from_pretrained(model_name)
        self.clap_model = ClapModel.from_pretrained(model_name).to(self.device)
        logger.info("CLAP model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load CLAP model: {e}")
        self.clap_model = None
```

### 2. Comprehensive Error Handling
- File existence checks before processing
- Model availability checks
- Graceful degradation when components fail
- Detailed logging for debugging

### 3. Memory Management
- Models loaded only when needed
- Proper cleanup and error recovery
- Batch processing for large datasets

### 4. Progress Tracking
- Progress bars for long-running operations
- Detailed logging of each step
- Clear error messages with context

## Dependencies

### Required
```bash
pip install pandas torch torchaudio soundfile librosa numpy scipy einops tqdm
```

### Optional (for specific metrics)
```bash
pip install sentence-transformers  # For similarity matching
pip install transformers          # For CLAP model
pip install openl3               # For FD metric
# stable-audio-tools              # For audio generation
```

## Configuration Options

### Model Settings
- `use_clap`: Enable/disable CLAP similarity metric
- `use_passt`: Enable/disable PaSST class probability metric
- `use_generation`: Enable/disable audio generation
- `clap_model_name`: Hugging Face model name for CLAP

### File Paths
- `dit_config`: Path to DiT model configuration
- `vae_config`: Path to VAE model configuration
- `dit_checkpoint`: Path to DiT model checkpoint
- `vae_checkpoint`: Path to VAE model checkpoint
- `reference_audio_dir`: Directory containing reference audio files

### Generation Parameters
- `duration`: Audio duration in seconds
- `steps`: Number of diffusion steps
- `cfg_scale`: Classifier-free guidance scale
- `sampler_type`: Sampling algorithm

## Error Recovery

The improved script handles common errors gracefully:

1. **Missing models**: Continues with available metrics
2. **Missing files**: Skips problematic files and continues
3. **Out of memory**: Reduces batch size automatically
4. **Network issues**: Retries model downloads
5. **Corrupted audio**: Logs error and continues

## Output

The script generates:
- `metrics.json`: Final evaluation metrics
- Generated audio files (if generation is enabled)
- Detailed logs of the evaluation process
- Progress information and error reports

## Metrics Computed

1. **CLAP Score**: Text-audio similarity using CLAP model
2. **Fréchet Distance**: Distribution similarity using OpenL3 embeddings
3. **KL Divergence**: Class distribution difference using PaSST

Each metric includes proper error handling and fallback behavior when components are unavailable. 
#!/usr/bin/env python3
"""
FreeAudio Prompt Generation Pipeline

Generates descriptive prompts for audio files based on file paths from a CSV input.
Adapted from the OtoLogic metadata extractor for freeaudio collections.
"""

import pandas as pd
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
import logging
from openai import OpenAI
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# OpenAI setup
openai_key = 
client = OpenAI(api_key=openai_key)

class FreeAudioPromptGenerator:
    def __init__(self, csv_file: str = "original_path_na.csv", output_dir: str = "freeaudio_prompts"):
        self.csv_file = Path(csv_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.generated_prompts = []
        
        # Category mappings to provide context
        self.category_mappings = {
            'daily01': 'Daily life activities and household sounds',
            'daily02': 'Daily life activities and household items',
            'sports01': 'Sports and athletic activities',
            'eating01': 'Food preparation and eating sounds',
            'transfer01': 'Transportation and travel sounds',
            'cooking01': 'Cooking and kitchen activities',
            'pc01': 'Computer and office equipment sounds',
            'wetarea01': 'Bathroom and water-related sounds',
            'electric01': 'Electrical appliances and devices',
            'tokyo01': 'Tokyo city sounds and environments',
            'us01': 'United States city sounds and environments',
            'sample_noise': 'Sample noise and ambient sounds',
            'horror02': 'Horror and suspense sound effects',
            'playing01': 'Playing and recreational sounds',
            'horror01': 'Horror and atmospheric sound effects',
            'nature01': 'Nature and outdoor environmental sounds',
            'anime01': 'Anime-style sound effects and music',
            'car01': 'Car and automotive sounds',
            'arms01': 'Military and weapon sound effects',
            'human01': 'Human activity and movement sounds',
            'animals01': 'Animal sounds and nature',
            'french01': 'French location and environment sounds',
            'acoustica': 'Various acoustic sound effects',
            'monster01': 'Monster and creature sound effects',
            'environment01': 'Urban and environmental ambient sounds',
            'event01': 'Event and gathering sounds',
            'sf01': 'Science fiction and futuristic sound effects',
            'environment02': 'Industrial and construction sounds',
            'openclose01': 'Opening and closing sounds',
            'attack01': 'Attack and action sound effects'
        }
        
    def extract_metadata_from_path(self, file_path: str) -> Dict:
        """Extract metadata from file path structure"""
        path_parts = Path(file_path).parts
        filename = Path(file_path).stem
        
        metadata = {
            'original_path': file_path,
            'filename': filename,
            'category': '',
            'subcategory': '',
            'description': '',
            'inferred_context': '',
            'keywords': []
        }
        
        # Extract category information
        if len(path_parts) >= 2:
            metadata['category'] = path_parts[1]  # e.g., 'daily01'
            metadata['inferred_context'] = self.category_mappings.get(
                metadata['category'], 
                f"Audio from {metadata['category']} collection"
            )
        
        if len(path_parts) >= 3:
            metadata['subcategory'] = path_parts[2]
        
        # Clean and analyze filename
        clean_filename = filename.replace('_', ' ').replace('-', ' ')
        
        # Extract potential keywords from filename
        keywords = []
        
        # Common sound effect patterns
        keyword_patterns = {
            r'\b(rain|thunder|storm|wind|water|fire|ocean|waves)\b': 'nature',
            r'\b(car|engine|motor|drive|truck|vehicle)\b': 'transportation',
            r'\b(door|open|close|window|gate)\b': 'mechanical',
            r'\b(crowd|people|cheer|applause|talking)\b': 'human',
            r'\b(bell|chime|alarm|beep|buzzer)\b': 'alert',
            r'\b(music|piano|guitar|drum|instrument)\b': 'musical',
            r'\b(kitchen|cook|food|eat|drink)\b': 'culinary',
            r'\b(office|computer|type|print|click)\b': 'office',
            r'\b(animal|dog|cat|bird|wildlife)\b': 'animal',
            r'\b(explosion|bomb|gun|weapon|attack)\b': 'combat'
        }
        
        for pattern, category in keyword_patterns.items():
            if re.search(pattern, clean_filename, re.IGNORECASE):
                keywords.append(category)
        
        # Extract numeric patterns (versions, sequences)
        numbers = re.findall(r'\d+', filename)
        if numbers:
            metadata['sequence'] = numbers[-1]  # Use last number as sequence
        
        metadata['keywords'] = keywords
        metadata['description'] = clean_filename
        
        return metadata
    
    def generate_prompt_for_audio(self, metadata: Dict) -> str:
        """Generate a high-quality prompt for an audio file using LLM"""
        
        # Create context for the LLM
        context_parts = []
        
        if metadata.get('category'):
            context_parts.append(f"Category: {metadata['category']}")
        
        if metadata.get('inferred_context'):
            context_parts.append(f"Context: {metadata['inferred_context']}")
        
        if metadata.get('description'):
            context_parts.append(f"Filename description: {metadata['description']}")
        
        if metadata.get('keywords'):
            context_parts.append(f"Keywords: {', '.join(metadata['keywords'])}")
        
        context_parts.append(f"Original path: {metadata['original_path']}")
        
        context = "\n".join(context_parts)
        
        prompt_template = """
You are an expert audio description writer. Your task is to create a clear, concise prompt that describes an audio file based on the provided metadata extracted from its filename and file path.

## Guidelines:
- Write descriptions that are clear and match how a user might search for this sound
- Use concise noun phrases or short sentences
- Include specific context when relevant (e.g., "Japanese school chime" vs just "school bell")
- Include the setting or environment when it adds clarity
- Add onomatopoeia when appropriate (e.g., "ding-dong", "whoosh", "splash")
- Be specific about the type of sound, activity, or environment
- Keep it under 15 words when possible
- Focus on the actual sound being made, not just the object

## Examples:
- "Sweeping floor with broom bristles scraping"
- "Basketball dribbling rhythmically in gymnasium"
- "Hot tea being poured into ceramic cup"
- "Train passing by with clickety-clack on tracks"
- "Typing on mechanical keyboard with click sounds"
- "Rain droplets hitting window glass steadily"
- "Crowd cheering and applauding at sporting event"
- "Doorbell chiming with two-tone ding-dong"

## Audio Metadata:
{context}

Generate a single, clear prompt that describes this audio file:
"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert audio description writer."},
                    {"role": "user", "content": prompt_template.format(context=context)}
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            generated_prompt = response.choices[0].message.content.strip()
            # Clean up the prompt - remove quotes if present
            generated_prompt = generated_prompt.strip('"\'')
            logger.info(f"Generated prompt: {generated_prompt}")
            return generated_prompt
            
        except Exception as e:
            logger.error(f"Error generating prompt: {e}")
            # Fallback to basic description
            return f"{metadata.get('description', metadata.get('filename', 'audio'))} sound effect"
    
    def process_csv_file(self):
        """Process all audio files listed in the CSV"""
        logger.info("🚀 Starting FreeAudio prompt generation pipeline")
        
        if not self.csv_file.exists():
            logger.error(f"CSV file {self.csv_file} does not exist")
            return
        
        # Read CSV file
        try:
            df = pd.read_csv(self.csv_file)
            logger.info(f"Loaded {len(df)} audio file paths from CSV")
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return
        
        processed_files = 0
        failed_files = 0
        
        # Process each audio file path
        for index, row in df.iterrows():
            file_path = row['original_path']
            logger.info(f"Processing ({index+1}/{len(df)}): {file_path}")
            
            try:
                # Extract metadata from path
                metadata = self.extract_metadata_from_path(file_path)
                
                # Generate prompt
                prompt = self.generate_prompt_for_audio(metadata)
                
                # Create complete metadata record
                complete_metadata = {
                    'original_path': file_path,
                    'filename': metadata['filename'],
                    'category': metadata['category'],
                    'subcategory': metadata.get('subcategory', ''),
                    'description': metadata['description'],
                    'keywords': metadata['keywords'],
                    'inferred_context': metadata['inferred_context'],
                    'generated_prompt': prompt,
                    'sequence': metadata.get('sequence', ''),
                    'processing_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                self.generated_prompts.append(complete_metadata)
                processed_files += 1
                
                # Rate limiting for API calls
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                failed_files += 1
                continue
        
        # Save results
        self.save_results()
        
        logger.info(f"Pipeline complete!")
        logger.info(f"Successfully processed: {processed_files} files")
        logger.info(f"Failed to process: {failed_files} files")
        logger.info(f"Total prompts generated: {len(self.generated_prompts)}")
    
    def save_results(self):
        """Save generated prompts and metadata to files"""
        
        # Save as JSONL for easy processing
        jsonl_file = self.output_dir / 'freeaudio_generated_prompts.jsonl'
        with open(jsonl_file, 'w', encoding='utf-8') as f:
            for prompt_data in self.generated_prompts:
                f.write(json.dumps(prompt_data, ensure_ascii=False) + '\n')
        
        # Save as CSV for easy viewing
        csv_file = self.output_dir / 'freeaudio_prompts.csv'
        df = pd.DataFrame(self.generated_prompts)
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        # Save summary statistics
        summary = {
            'total_files_processed': len(self.generated_prompts),
            'unique_categories': len(set(p['category'] for p in self.generated_prompts)),
            'categories_breakdown': {},
            'processing_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'average_prompt_length': sum(len(p['generated_prompt']) for p in self.generated_prompts) / len(self.generated_prompts) if self.generated_prompts else 0
        }
        
        # Category breakdown
        for prompt_data in self.generated_prompts:
            category = prompt_data['category']
            if category in summary['categories_breakdown']:
                summary['categories_breakdown'][category] += 1
            else:
                summary['categories_breakdown'][category] = 1
        
        summary_file = self.output_dir / 'processing_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Results saved to:")
        logger.info(f"  - JSONL: {jsonl_file}")
        logger.info(f"  - CSV: {csv_file}")
        logger.info(f"  - Summary: {summary_file}")
    
    def preview_samples(self, n_samples: int = 5):
        """Preview a few sample prompts"""
        if not self.generated_prompts:
            logger.warning("No prompts generated yet. Run process_csv_file() first.")
            return
        
        logger.info(f"\n📋 Sample Generated Prompts (showing {min(n_samples, len(self.generated_prompts))}):")
        logger.info("=" * 80)
        
        for i, prompt_data in enumerate(self.generated_prompts[:n_samples]):
            logger.info(f"\n{i+1}. File: {prompt_data['filename']}")
            logger.info(f"   Category: {prompt_data['category']}")
            logger.info(f"   Keywords: {', '.join(prompt_data['keywords'])}")
            logger.info(f"   Generated Prompt: \"{prompt_data['generated_prompt']}\"")
        
        logger.info("=" * 80)


def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--preview':
        # Preview mode - process a few samples
        generator = FreeAudioPromptGenerator()
        
        # Process just first 10 for preview
        logger.info("🔬 Preview mode - processing first 10 files only")
        
        if not generator.csv_file.exists():
            logger.error(f"CSV file {generator.csv_file} does not exist")
            return
        
        try:
            df = pd.read_csv(generator.csv_file)
            df_preview = df.head(10)  # Just first 10 files
            
            for index, row in df_preview.iterrows():
                file_path = row['original_path']
                logger.info(f"Processing preview ({index+1}/10): {file_path}")
                
                metadata = generator.extract_metadata_from_path(file_path)
                prompt = generator.generate_prompt_for_audio(metadata)
                
                complete_metadata = {
                    'original_path': file_path,
                    'filename': metadata['filename'],
                    'category': metadata['category'],
                    'description': metadata['description'],
                    'keywords': metadata['keywords'],
                    'generated_prompt': prompt
                }
                
                generator.generated_prompts.append(complete_metadata)
                time.sleep(0.1)
            
            generator.preview_samples(10)
            
        except Exception as e:
            logger.error(f"Preview error: {e}")
            
    else:
        # Full processing mode
        generator = FreeAudioPromptGenerator()
        try:
            generator.process_csv_file()
            generator.preview_samples(5)
        except KeyboardInterrupt:
            logger.info("Processing interrupted by user")
        except Exception as e:
            logger.error(f"Processing error: {e}")
            raise

if __name__ == "__main__":
    main() 
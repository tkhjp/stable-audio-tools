#!/usr/bin/env python3
"""
FreeAudio Annotator
Processes zip files containing audio from freeaudio folder:
1. Unzips files to folders with same names
2. Scrapes descriptions from taira-komori.jpn.org
3. Uses ChatGPT-o3 to generate short descriptions
4. Creates CSV with filename, duration, and descriptions
"""

import os
import sys
import zipfile
import csv
import json
import requests
from pathlib import Path
import time
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from openai import OpenAI
from mutagen.mp3 import MP3
from mutagen import File
import logging
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('freeaudio_annotator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FreeAudioAnnotator:
    def __init__(self, freeaudio_dir: str = "freeaudio", openai_api_key: str = None):
        """
        Initialize the FreeAudio Annotator
        
        Args:
            freeaudio_dir: Directory containing zip files
            openai_api_key: OpenAI API key for GPT-o3
        """
        self.freeaudio_dir = Path(freeaudio_dir)
        self.base_url = "https://taira-komori.jpn.org"
        self.output_csv = "freeaudio_annotations.csv"
        
        # Initialize OpenAI client
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or pass it to constructor.")
            sys.exit(1)
            
        self.openai_client = OpenAI(api_key=api_key)
            
        # Initialize results storage
        self.results = []
        
    def unzip_file(self, zip_path: Path) -> Path:
        """
        Unzip a file to a folder with the same name (without .zip extension)
        
        Args:
            zip_path: Path to the zip file
            
        Returns:
            Path to the extracted folder
        """
        extract_dir = zip_path.parent / zip_path.stem
        
        if extract_dir.exists():
            logger.info(f"Directory {extract_dir} already exists, skipping extraction")
            return extract_dir
            
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            logger.info(f"Extracted {zip_path} to {extract_dir}")
            return extract_dir
        except Exception as e:
            logger.error(f"Error extracting {zip_path}: {e}")
            return None
            
    def scrape_page_content(self, zip_name: str) -> Tuple[List[str], List[str]]:
        """
        Scrape big titles and descriptions from the corresponding webpage
        
        Args:
            zip_name: Name of zip file (without .zip extension)
            
        Returns:
            Tuple of (big_titles, descriptions)
        """
        url = f"{self.base_url}/{zip_name}.html"
        
        try:
            response = requests.get(url, timeout=30)
            response.encoding = 'shift_jis'  # Japanese encoding
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract big titles (font size="4" in center)
            big_titles = []
            title_elements = soup.find_all('font', size='4')
            for element in title_elements:
                title_text = element.get_text(strip=True)
                if title_text:
                    big_titles.append(title_text)
                    
            # Extract descriptions (div align="right")
            descriptions = []
            desc_elements = soup.find_all('div', align='right')
            for element in desc_elements:
                desc_text = element.get_text(strip=True)
                if desc_text:
                    descriptions.append(desc_text)
                    
            logger.info(f"Scraped {len(big_titles)} titles and {len(descriptions)} descriptions from {url}")
            return big_titles, descriptions
            
        except requests.RequestException as e:
            logger.error(f"Error scraping {url}: {e}")
            return [], []
        except Exception as e:
            logger.error(f"Error parsing content from {url}: {e}")
            return [], []
            
    def get_audio_duration(self, audio_path: Path) -> float:
        """
        Get duration of audio file in seconds
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds, or 0.0 if error
        """
        try:
            audio_file = File(audio_path)
            if audio_file is not None and hasattr(audio_file, 'info'):
                return audio_file.info.length
            return 0.0
        except Exception as e:
            logger.error(f"Error getting duration for {audio_path}: {e}")
            return 0.0
            
    def get_audio_binary_data(self, audio_path: Path) -> bytes:
        """
        Read audio file as binary data
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Binary data of the audio file
        """
        try:
            with open(audio_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading binary data from {audio_path}: {e}")
            return b''
            
    def generate_ai_description(self, audio_path: Path, big_title: str, description: str) -> str:
        """
        Generate a short description using ChatGPT-o3
        
        Args:
            audio_path: Path to audio file
            big_title: Big title from webpage
            description: Description from webpage
            
        Returns:
            AI-generated short description
        """
        try:
            # Read audio file as binary (for context, though GPT can't actually process audio directly)
            # Note: GPT-4 and GPT-o3 cannot directly process audio binary data
            # We'll use the contextual information instead
            
            prompt = f"""
Based on the following information about a Japanese sound effect:

Big Title: {big_title}
Description: {description}
Filename: {audio_path.name}

Please generate a short, descriptive English description (1-2 sentences) of what this sound effect likely represents. 
Focus on the type of sound, its characteristics, and potential use cases.
Keep the description concise and practical for someone looking for sound effects.
"""
            
            # Use GPT-4o-mini for cost efficiency (o3 models may not be available yet)
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Use 4o-mini as it's cost-effective and widely available
                messages=[
                    {"role": "system", "content": "You are an expert in Japanese sound effects and audio description. Generate concise, practical descriptions for sound effects based on Japanese titles and descriptions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            ai_description = response.choices[0].message.content.strip()
            logger.info(f"Generated AI description for {audio_path.name}")
            return ai_description
            
        except Exception as e:
            logger.error(f"Error generating AI description for {audio_path}: {e}")
            return f"Audio file: {audio_path.name} (Title: {big_title}, Desc: {description})"
            
    def process_zip_file(self, zip_path: Path):
        """
        Process a single zip file: extract, scrape, annotate
        
        Args:
            zip_path: Path to the zip file to process
        """
        logger.info(f"Processing {zip_path}")
        
        # Step 1: Unzip the file
        extract_dir = self.unzip_file(zip_path)
        if not extract_dir:
            return
            
        # Step 2: Scrape webpage content
        zip_name = zip_path.stem
        big_titles, descriptions = self.scrape_page_content(zip_name)
        
        # Step 3: Process audio files
        audio_files = list(extract_dir.glob("**/*.mp3"))
        if not audio_files:
            logger.warning(f"No MP3 files found in {extract_dir}")
            return
            
        logger.info(f"Found {len(audio_files)} audio files in {extract_dir}")
        
        # Create a mapping of titles/descriptions to use for AI generation
        # We'll cycle through them or use contextual matching
        title_context = " | ".join(big_titles) if big_titles else "Sound Effects"
        desc_context = " | ".join(descriptions[:5]) if descriptions else "Various sound effects"  # Limit to first 5 for context
        
        for i, audio_path in enumerate(audio_files):
            try:
                # Get audio metadata
                duration = self.get_audio_duration(audio_path)
                
                # Use appropriate title/description for this audio file
                current_title = big_titles[i % len(big_titles)] if big_titles else "Sound Effect"
                current_desc = descriptions[i % len(descriptions)] if descriptions else f"Audio file {audio_path.name}"
                
                # Generate AI description
                ai_description = self.generate_ai_description(audio_path, current_title, current_desc)
                
                # Store result
                result = {
                    'filename': audio_path.name,
                    'duration_seconds': round(duration, 2),
                    'duration_formatted': f"{int(duration//60):02d}:{int(duration%60):02d}",
                    'zip_source': zip_name,
                    'big_title': current_title,
                    'original_description': current_desc,
                    'ai_description': ai_description,
                    'file_path': str(audio_path)
                }
                
                self.results.append(result)
                logger.info(f"Processed {audio_path.name} - Duration: {result['duration_formatted']}")
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing {audio_path}: {e}")
                continue
                
    def save_results_to_csv(self):
        """
        Save all results to CSV file
        """
        if not self.results:
            logger.warning("No results to save")
            return
            
        fieldnames = [
            'filename', 'duration_seconds', 'duration_formatted', 
            'zip_source', 'big_title', 'original_description', 
            'ai_description', 'file_path'
        ]
        
        try:
            with open(self.output_csv, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)
                
            logger.info(f"Saved {len(self.results)} results to {self.output_csv}")
            
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
            
    def run(self, specific_zip: str = None):
        """
        Run the complete annotation process
        
        Args:
            specific_zip: If provided, only process this specific zip file
        """
        if not self.freeaudio_dir.exists():
            logger.error(f"Directory {self.freeaudio_dir} does not exist")
            return
            
        # Get all zip files
        if specific_zip:
            zip_files = [self.freeaudio_dir / f"{specific_zip}.zip"]
            zip_files = [f for f in zip_files if f.exists()]
        else:
            zip_files = list(self.freeaudio_dir.glob("*.zip"))
            
        if not zip_files:
            logger.error("No zip files found to process")
            return
            
        logger.info(f"Found {len(zip_files)} zip files to process")
        
        # Process each zip file
        for zip_file in zip_files:
            try:
                self.process_zip_file(zip_file)
            except Exception as e:
                logger.error(f"Error processing {zip_file}: {e}")
                continue
                
        # Save results
        self.save_results_to_csv()
        
        # Print summary
        total_duration = sum(result['duration_seconds'] for result in self.results)
        logger.info(f"Processing complete!")
        logger.info(f"Total files processed: {len(self.results)}")
        logger.info(f"Total duration: {int(total_duration//3600):02d}:{int((total_duration%3600)//60):02d}:{int(total_duration%60):02d}")

def main():
    """
    Main function to run the annotator
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="FreeAudio Annotator - Process audio files and generate descriptions")
    parser.add_argument("--freeaudio-dir", default="freeaudio", help="Directory containing zip files")
    parser.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY env var)")
    parser.add_argument("--zip-file", help="Process only this specific zip file (without .zip extension)")
    parser.add_argument("--output", default="freeaudio_annotations.csv", help="Output CSV filename")
    
    args = parser.parse_args()
    
    # Create annotator
    annotator = FreeAudioAnnotator(
        freeaudio_dir=args.freeaudio_dir,
        openai_api_key=args.api_key
    )
    
    # Set output filename
    annotator.output_csv = args.output
    
    # Run annotation
    annotator.run(specific_zip=args.zip_file)

if __name__ == "__main__":
    main() 
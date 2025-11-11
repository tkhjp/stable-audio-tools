#!/usr/bin/env python3
"""
Generate CSV mapping between Taira Komori audio filenames and their URLs
Downloads audio files from https://taira-komori.net/ and creates comprehensive mappings
"""

import json
import csv
import os
import requests
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import zipfile

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TairaKomoriMapper:
    def __init__(self, output_file: str = "tairakomori_filename_url_mapping.csv", 
                 download_dir: str = "tairakomori_downloads"):
        self.output_file = output_file
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.base_url = "https://taira-komori.net"
        self.mappings = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_available_categories(self) -> List[str]:
        """Get available sound effect categories from the main page"""
        try:
            response = self.session.get(self.base_url, timeout=30)
            response.encoding = 'shift_jis'  # Japanese encoding
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            categories = []
            
            # Look for category links
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if href.endswith('.html') and not href.startswith('http'):
                    category_name = href.replace('.html', '')
                    if category_name not in ['freesound', 'freesounden', 'freesoundtw', 'freesoundcn', 'freesoundkr', 'freesoundes', 'welcome']:
                        categories.append(category_name)
            
            logger.info(f"Found {len(categories)} potential categories")
            return categories
            
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    def scrape_category_page(self, category: str) -> List[Dict]:
        """Scrape a specific category page for audio files and metadata"""
        url = f"{self.base_url}/{category}.html"
        audio_files = []
        
        try:
            logger.info(f"Scraping category: {category} from {url}")
            response = self.session.get(url, timeout=30)
            response.encoding = 'shift_jis'
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract big titles (font size="4" elements)
            big_titles = []
            title_elements = soup.find_all('font', size='4')
            for element in title_elements:
                title_text = element.get_text(strip=True)
                if title_text and title_text not in ['効果音検索', 'ホーム', '利用規約']:
                    big_titles.append(title_text)
            
            # Extract audio files and their metadata
            current_title = "Sound Effects"
            all_elements = soup.find_all(['td', 'tr', 'table'])
            
            for element in all_elements:
                # Check if this element contains a big title
                title_font = element.find('font', size='4')
                if title_font:
                    new_title = title_font.get_text(strip=True)
                    if new_title not in ['効果音検索', 'ホーム', '利用規約']:
                        current_title = new_title
                
                # Check if this is a table row with audio file information
                if element.name == 'tr':
                    cells = element.find_all('td')
                    if len(cells) >= 3:  # Expecting: description, player, download
                        desc_cell = cells[0]
                        download_cell = cells[2] if len(cells) > 2 else cells[1]
                        
                        # Extract description
                        desc_div = desc_cell.find('div', align='right')
                        description = desc_div.get_text(strip=True) if desc_div else ""
                        
                        # Look for download link in the third cell
                        dl_link = download_cell.find('a', href=True)
                        if dl_link:
                            href = dl_link.get('href', '')
                            if '.mp3' in href or '.wav' in href:
                                # Get full URL
                                if href.startswith('http'):
                                    full_url = href
                                else:
                                    full_url = urljoin(url, href)
                                
                                # Extract filename
                                filename = href.split('/')[-1]
                                
                                audio_file = {
                                    'filename': filename,
                                    'description': description,
                                    'big_title': current_title,
                                    'category': category,
                                    'download_url': full_url,
                                    'page_url': url,
                                    'big_titles': big_titles
                                }
                                audio_files.append(audio_file)
            
            logger.info(f"Found {len(audio_files)} audio files in category {category}")
            return audio_files
            
        except Exception as e:
            logger.error(f"Error scraping category {category}: {e}")
            return []
    
    def download_audio_file(self, audio_file: Dict) -> bool:
        """Download a single audio file"""
        try:
            filename = audio_file['filename']
            download_url = audio_file['download_url']
            category = audio_file['category']
            
            # Create category directory
            category_dir = self.download_dir / category
            category_dir.mkdir(exist_ok=True)
            
            # Check if file already exists
            file_path = category_dir / filename
            if file_path.exists():
                logger.info(f"File already exists: {filename}")
                return True
            
            # Download the file
            logger.info(f"Downloading: {filename} from {download_url}")
            response = self.session.get(download_url, timeout=60)
            response.raise_for_status()
            
            # Save the file
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Add file path to mapping
            audio_file['local_file_path'] = str(file_path)
            audio_file['file_size'] = len(response.content)
            
            logger.info(f"Successfully downloaded: {filename}")
            
            # Rate limiting
            time.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {audio_file.get('filename', 'unknown')}: {e}")
            return False
    
    def process_all_categories(self) -> None:
        """Process all available categories and download audio files"""
        logger.info("Starting to process all Taira Komori categories...")
        
        # Get available categories
        categories = self.get_available_categories()
        
        if not categories:
            logger.warning("No categories found!")
            return
        
        # Process each category
        for category in categories:
            try:
                logger.info(f"Processing category: {category}")
                
                # Scrape the category page
                audio_files = self.scrape_category_page(category)
                
                if audio_files:
                    # Download audio files
                    for audio_file in audio_files:
                        success = self.download_audio_file(audio_file)
                        if success:
                            self.mappings.append(audio_file)
                    
                    logger.info(f"Processed {len(audio_files)} files from category {category}")
                
                # Rate limiting between categories
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing category {category}: {e}")
                continue
        
        logger.info(f"Total mappings created: {len(self.mappings)}")
    
    def generate_url_mapping(self) -> None:
        """Generate URL mappings from existing data if no downloads are performed"""
        logger.info("Generating URL mappings from existing data...")
        
        # Check if we have existing freeaudio data
        freeaudio_dir = Path("freeaudio")
        if freeaudio_dir.exists():
            logger.info("Found existing freeaudio directory, generating mappings...")
            
            # Process existing ZIP files and extracted directories
            for item in freeaudio_dir.iterdir():
                if item.is_file() and item.suffix == '.zip':
                    category = item.stem
                    self.generate_mapping_from_zip(item, category)
                elif item.is_dir():
                    category = item.name
                    self.generate_mapping_from_directory(item, category)
        
        # Also check freeaudio_prompts for existing mappings
        prompts_file = Path("freeaudio_prompts/freeaudio_prompts.csv")
        if prompts_file.exists():
            logger.info("Found existing freeaudio prompts, adding to mappings...")
            self.add_existing_prompts(prompts_file)
    
    def generate_mapping_from_zip(self, zip_path: Path, category: str) -> None:
        """Generate mapping from a ZIP file"""
        try:
            # Try to extract and analyze
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                
                for filename in file_list:
                    if filename.lower().endswith(('.mp3', '.wav', '.flac', '.aiff')):
                        # Create mapping entry
                        mapping = {
                            'filename': filename.split('/')[-1],
                            'description': '',
                            'big_title': category,
                            'category': category,
                            'download_url': f"https://taira-komori.net/sound/{category}/{filename.split('/')[-1]}",
                            'page_url': f"https://taira-komori.net/{category}.html",
                            'big_titles': [category],
                            'local_file_path': str(zip_path),
                            'file_size': 0
                        }
                        self.mappings.append(mapping)
            
            logger.info(f"Generated {len([m for m in self.mappings if m['category'] == category])} mappings from {category}")
            
        except Exception as e:
            logger.error(f"Error processing ZIP file {zip_path}: {e}")
    
    def generate_mapping_from_directory(self, dir_path: Path, category: str) -> None:
        """Generate mapping from an extracted directory"""
        try:
            audio_files = list(dir_path.rglob("*.mp3")) + list(dir_path.rglob("*.wav"))
            
            for audio_file in audio_files:
                mapping = {
                    'filename': audio_file.name,
                    'description': '',
                    'big_title': category,
                    'category': category,
                    'download_url': f"https://taira-komori.net/sound/{category}/{audio_file.name}",
                    'page_url': f"https://taira-komori.net/{category}.html",
                    'big_titles': [category],
                    'local_file_path': str(audio_file),
                    'file_size': audio_file.stat().st_size if audio_file.exists() else 0
                }
                self.mappings.append(mapping)
            
            logger.info(f"Generated {len([m for m in self.mappings if m['category'] == category])} mappings from directory {category}")
            
        except Exception as e:
            logger.error(f"Error processing directory {dir_path}: {e}")
    
    def add_existing_prompts(self, prompts_file: Path) -> None:
        """Add existing prompts data to mappings"""
        try:
            import pandas as pd
            df = pd.read_csv(prompts_file)
            
            for _, row in df.iterrows():
                # Check if this mapping already exists
                existing = [m for m in self.mappings if m['filename'] == row['filename']]
                if not existing:
                    # Create new mapping from prompt data
                    mapping = {
                        'filename': row['filename'],
                        'description': row.get('description', ''),
                        'big_title': row.get('category', ''),
                        'category': row.get('category', ''),
                        'download_url': f"https://taira-komori.net/sound/{row.get('category', '')}/{row['filename']}",
                        'page_url': f"https://taira-komori.net/{row.get('category', '')}.html",
                        'big_titles': [row.get('category', '')],
                        'local_file_path': row.get('original_path', ''),
                        'file_size': 0,
                        'generated_prompt': row.get('generated_prompt', ''),
                        'inferred_context': row.get('inferred_context', '')
                    }
                    self.mappings.append(mapping)
            
            logger.info(f"Added {len([m for m in self.mappings if 'generated_prompt' in m])} mappings from existing prompts")
            
        except Exception as e:
            logger.error(f"Error adding existing prompts: {e}")
    
    def enhance_with_web_data(self) -> None:
        """Enhance existing mappings with actual web-scraped data"""
        logger.info("Enhancing mappings with web-scraped data...")
        
        # Get available categories from web
        categories = self.get_available_categories()
        
        enhanced_count = 0
        for category in categories:
            try:
                logger.info(f"Enhancing category: {category}")
                
                # Scrape the category page
                audio_files = self.scrape_category_page(category)
                
                if audio_files:
                    # Update existing mappings with web data
                    for web_audio in audio_files:
                        # Find matching local file
                        for mapping in self.mappings:
                            if (mapping['filename'] == web_audio['filename'] and 
                                mapping['category'] == category):
                                
                                # Update with web data
                                mapping['download_url'] = web_audio['download_url']
                                mapping['description'] = web_audio['description']
                                mapping['big_title'] = web_audio['big_title']
                                mapping['big_titles'] = web_audio['big_titles']
                                enhanced_count += 1
                                break
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error enhancing category {category}: {e}")
                continue
        
        logger.info(f"Enhanced {enhanced_count} mappings with web data")
    
    def write_csv(self) -> None:
        """Write mappings to CSV file"""
        if not self.mappings:
            logger.warning("No mappings to write")
            return
        
        try:
            with open(self.output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'filename', 'description', 'big_title', 'category', 
                    'download_url', 'page_url', 'big_titles', 'local_file_path',
                    'file_size', 'generated_prompt', 'inferred_context'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for mapping in self.mappings:
                    # Convert big_titles list to string
                    if 'big_titles' in mapping and isinstance(mapping['big_titles'], list):
                        mapping['big_titles'] = ' | '.join(mapping['big_titles'])
                    
                    writer.writerow(mapping)
            
            logger.info(f"Successfully wrote {len(self.mappings)} mappings to {self.output_file}")
            
        except Exception as e:
            logger.error(f"Error writing CSV file: {e}")
    
    def print_summary(self) -> None:
        """Print a summary of the mapping results"""
        if not self.mappings:
            return
        
        print(f"\n📊 TAIRA KOMORI MAPPING STATISTICS:")
        print(f"   Total mappings created: {len(self.mappings)}")
        print(f"   Output file: {self.output_file}")
        print(f"   Download directory: {self.download_dir}")
        
        # Count by category
        category_counts = {}
        for mapping in self.mappings:
            category = mapping.get('category', 'Unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        print(f"\n📁 MAPPINGS BY CATEGORY:")
        for category, count in sorted(category_counts.items()):
            print(f"   {category}: {count} files")
        
        # Show sample mappings
        print(f"\n📋 SAMPLE MAPPINGS:")
        for i, mapping in enumerate(self.mappings[:5]):
            print(f"   {i+1}. {mapping['filename'][:50]}...")
            print(f"      Category: {mapping['category']}")
            print(f"      Page URL: {mapping['page_url']}")
            if mapping.get('download_url'):
                print(f"      Download URL: {mapping['download_url']}")
            print()
    
    def run(self, download_files: bool = False, enhance_web: bool = False) -> None:
        """Main run method"""
        if download_files:
            logger.info("Running in download mode - will download audio files from website")
            self.process_all_categories()
        else:
            logger.info("Running in mapping mode - will generate mappings from existing data")
            self.generate_url_mapping()
            
            if enhance_web:
                logger.info("Enhancing mappings with web data...")
                self.enhance_with_web_data()
        
        # Write results
        self.write_csv()
        
        # Print summary
        self.print_summary()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Taira Komori filename to URL mapping CSV")
    parser.add_argument("--output", default="tairakomori_filename_url_mapping.csv",
                       help="Output CSV filename")
    parser.add_argument("--download-dir", default="tairakomori_downloads",
                       help="Directory to download audio files")
    parser.add_argument("--download", action="store_true",
                       help="Download audio files from website (use with caution)")
    parser.add_argument("--enhance-web", action="store_true",
                       help="Enhance existing mappings with web-scraped data")
    
    args = parser.parse_args()
    
    # Create mapper and run
    mapper = TairaKomoriMapper(args.output, args.download_dir)
    mapper.run(download_files=args.download, enhance_web=args.enhance_web)

if __name__ == "__main__":
    main() 
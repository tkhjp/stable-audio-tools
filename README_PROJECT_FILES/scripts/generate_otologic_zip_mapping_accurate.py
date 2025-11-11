#!/usr/bin/env python3
"""
Generate accurate OtoLogic MP3-to-ZIP mapping
Uses actual HTML files to extract exact ZIP naming patterns
"""

import json
import csv
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
import logging
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AccurateOtoLogicZipMapper:
    def __init__(self, output_file: str = "otologic_mp3_to_zip_accurate.csv"):
        self.output_file = output_file
        self.base_url = "https://otologic.jp"
        self.zip_base_url = "https://otologic.jp/sounds/se/mp3-zip"
        self.mappings = []
        self.zip_to_mp3 = {}  # Maps ZIP files to their MP3 contents
        
    def extract_zip_mappings_from_html(self) -> Dict[str, Dict]:
        """Extract ZIP mappings from HTML debug files"""
        zip_mappings = {}
        
        # Scan debug metadata directory
        debug_dir = Path("debug_metadata")
        if debug_dir.exists():
            html_files = list(debug_dir.glob("*.html"))
            logger.info(f"Found {len(html_files)} HTML debug files")
            
            for html_file in html_files:
                try:
                    with open(html_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Extract category from filename
                    category = html_file.stem.replace('debug_', '').replace('.html', '')
                    page_url = f"https://otologic.jp/free/se/{category}.html"
                    
                    # Find all ZIP download links
                    zip_links = soup.find_all('a', href=re.compile(r'mp3-zip/.*\.zip'))
                    
                    for link in zip_links:
                        href = link.get('href', '')
                        if 'mp3-zip' in href:
                            # Extract ZIP filename
                            zip_filename = href.split('/')[-1]
                            full_zip_url = f"{self.zip_base_url}/{zip_filename}"
                            
                            # Find the sound effect title
                            # Look for the sound effect section this ZIP belongs to
                            sound_effect_title = self.extract_sound_effect_title_from_context(link, soup)
                            
                            zip_mappings[zip_filename] = {
                                'zip_filename': zip_filename,
                                'zip_url': full_zip_url,
                                'page_url': page_url,
                                'category': category,
                                'sound_effect_title': sound_effect_title,
                                'mp3_files': []  # Will be populated later
                            }
                
                except Exception as e:
                    logger.warning(f"Error processing HTML file {html_file}: {e}")
        
        logger.info(f"Extracted {len(zip_mappings)} ZIP mappings from HTML files")
        return zip_mappings
    
    def extract_sound_effect_title_from_context(self, zip_link, soup) -> str:
        """Extract the sound effect title from the context around the ZIP link"""
        try:
            # Find the parent table or section
            parent = zip_link.find_parent(['table', 'tr', 'td'])
            if parent:
                # Look for title in nearby elements
                title_elements = parent.find_all(['h1', 'h2', 'h3', 'strong', 'b'])
                for element in title_elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 3:
                        return text
                
                # Look for title in previous elements
                prev_elements = parent.find_previous_siblings()
                for element in prev_elements[:3]:  # Check last 3 siblings
                    if element.name in ['h1', 'h2', 'h3']:
                        return element.get_text(strip=True)
            
            # Fallback: extract from ZIP filename
            zip_filename = zip_link.get('href', '').split('/')[-1]
            return zip_filename.replace('-mp3.zip', '').replace('_', ' ')
            
        except Exception:
            return ""
    
    def map_mp3_files_to_zips(self) -> None:
        """Map individual MP3 files to their corresponding ZIP files"""
        
        # Get ZIP mappings from HTML
        zip_mappings = self.extract_zip_mappings_from_html()
        
        # Scan metadata files to find MP3 files
        metadata_files = self.scan_metadata_files()
        
        for metadata_file in metadata_files:
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                title = data.get('title', '')
                category = data.get('category', '')
                page_url = data.get('page_url', '')
                
                # Find audio files in the directory
                metadata_dir = metadata_file.parent
                audio_files = []
                
                for file_path in metadata_dir.iterdir():
                    if file_path.suffix.lower() in ['.mp3', '.wav']:
                        audio_files.append(file_path)
                
                # Find matching ZIP file
                matching_zip = self.find_matching_zip(title, zip_mappings)
                
                if matching_zip:
                    zip_info = zip_mappings[matching_zip]
                    
                    # Create mappings for each MP3 file
                    for audio_file in audio_files:
                        mapping = {
                            'mp3_filename': audio_file.name,
                            'original_japanese_name': audio_file.name,
                            'sound_effect_title': title,
                            'description': data.get('description', ''),
                            'keywords': ', '.join(data.get('keywords', [])),
                            'category': category,
                            'page_url': page_url,
                            'zip_download_url': zip_info['zip_url'],
                            'zip_filename': zip_info['zip_filename'],
                            'local_file_path': str(audio_file),
                            'file_size': audio_file.stat().st_size if audio_file.exists() else 0,
                            'metadata_source': str(metadata_file)
                        }
                        self.mappings.append(mapping)
                
            except Exception as e:
                logger.warning(f"Error processing metadata {metadata_file}: {e}")
    
    def find_matching_zip(self, title: str, zip_mappings: Dict) -> Optional[str]:
        """Find the ZIP file that matches a sound effect title"""
        if not title:
            return None
        
        # Clean title for matching
        clean_title = title.strip()
        
        # Direct matching
        for zip_filename, zip_info in zip_mappings.items():
            zip_base = zip_filename.replace('-mp3.zip', '')
            
            # Try exact match
            if clean_title in zip_base or zip_base in clean_title:
                return zip_filename
            
            # Try partial matches
            title_parts = clean_title.split()
            for part in title_parts:
                if len(part) > 2 and part in zip_base:
                    return zip_filename
        
        return None
    
    def scan_metadata_files(self) -> List[Path]:
        """Find all metadata.json files"""
        metadata_files = []
        
        otologic_dirs = [
            "otologic_sounds",
            "otologic_sounds_smart",
            "otologic_english_sounds",
            "otologic_sounds_complete"
        ]
        
        for dir_name in otologic_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists():
                found_files = list(dir_path.rglob("metadata.json"))
                metadata_files.extend(found_files)
        
        return metadata_files
    
    def add_csv_mappings_with_zip_lookup(self, zip_mappings: Dict) -> None:
        """Add mappings from CSV with ZIP lookup"""
        csv_file = "otologic_filenames.csv"
        
        if Path(csv_file).exists():
            logger.info(f"Adding mappings from {csv_file} with ZIP lookup")
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        original_filename = row.get('original_filename', '')
                        english_filename = row.get('english_filename', '')
                        
                        if original_filename:
                            # Extract title from filename
                            title = self.extract_title_from_filename(original_filename)
                            
                            # Find matching ZIP
                            matching_zip = self.find_matching_zip(title, zip_mappings)
                            
                            if matching_zip:
                                zip_info = zip_mappings[matching_zip]
                                
                                mapping = {
                                    'mp3_filename': original_filename,
                                    'original_japanese_name': original_filename,
                                    'sound_effect_title': title,
                                    'description': '',
                                    'keywords': '',
                                    'category': zip_info['category'],
                                    'page_url': zip_info['page_url'],
                                    'zip_download_url': zip_info['zip_url'],
                                    'zip_filename': zip_info['zip_filename'],
                                    'local_file_path': f"CSV: {csv_file}",
                                    'file_size': 0,
                                    'metadata_source': csv_file
                                }
                                self.mappings.append(mapping)
            
            except Exception as e:
                logger.error(f"Error reading {csv_file}: {e}")
    
    def extract_title_from_filename(self, filename: str) -> str:
        """Extract base title from filename"""
        # Remove variations and extensions
        title = re.sub(r'-\d*\([^)]*\)\.mp3$', '', filename)
        title = re.sub(r'\.mp3$', '', title)
        
        # Get base name
        match = re.match(r'^([^-]+)', title)
        if match:
            return match.group(1).strip()
        
        return title
    
    def generate_mapping(self) -> None:
        """Generate the accurate ZIP mapping"""
        logger.info("Starting accurate OtoLogic MP3-to-ZIP mapping...")
        
        # Extract ZIP mappings from HTML files
        zip_mappings = self.extract_zip_mappings_from_html()
        
        # Map MP3 files to ZIPs
        self.map_mp3_files_to_zips()
        
        # Add CSV mappings with ZIP lookup
        self.add_csv_mappings_with_zip_lookup(zip_mappings)
        
        # Remove duplicates
        self.remove_duplicates()
        
        logger.info(f"Total accurate ZIP mappings: {len(self.mappings)}")
    
    def remove_duplicates(self) -> None:
        """Remove duplicates"""
        seen = set()
        unique_mappings = []
        
        for mapping in self.mappings:
            key = mapping['mp3_filename']
            if key not in seen:
                seen.add(key)
                unique_mappings.append(mapping)
        
        logger.info(f"Removed {len(self.mappings) - len(unique_mappings)} duplicates")
        self.mappings = unique_mappings
    
    def write_csv(self) -> None:
        """Write the mappings to CSV"""
        if not self.mappings:
            logger.warning("No mappings to write")
            return
        
        try:
            with open(self.output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'mp3_filename', 'original_japanese_name', 'sound_effect_title',
                    'description', 'keywords', 'category', 'page_url', 
                    'zip_download_url', 'zip_filename', 'local_file_path',
                    'file_size', 'metadata_source'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for mapping in self.mappings:
                    writer.writerow(mapping)
            
            logger.info(f"Successfully wrote {len(self.mappings)} accurate mappings to {self.output_file}")
            
        except Exception as e:
            logger.error(f"Error writing CSV file: {e}")
    
    def print_summary(self) -> None:
        """Print summary"""
        if not self.mappings:
            return
        
        print(f"\n📊 ACCURATE OTOLOGIC ZIP MAPPING SUMMARY:")
        print(f"   Total MP3 files mapped: {len(self.mappings)}")
        print(f"   Output file: {self.output_file}")
        
        # Count unique ZIP files
        unique_zips = set(mapping['zip_download_url'] for mapping in self.mappings if mapping['zip_download_url'])
        print(f"   Unique ZIP files: {len(unique_zips)}")
        
        # Show sample mappings
        print(f"\n📋 SAMPLE ACCURATE MAPPINGS:")
        for i, mapping in enumerate(self.mappings[:5]):
            print(f"   {i+1}. MP3: {mapping['mp3_filename'][:40]}...")
            print(f"      ZIP: {mapping['zip_filename']}")
            print(f"      Download: {mapping['zip_download_url']}")
            print()

def main():
    """Main function"""
    mapper = AccurateOtoLogicZipMapper()
    mapper.generate_mapping()
    mapper.write_csv()
    mapper.print_summary()

if __name__ == "__main__":
    main() 
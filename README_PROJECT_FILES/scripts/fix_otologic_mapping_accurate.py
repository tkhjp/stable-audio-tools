#!/usr/bin/env python3
"""
Fix OtoLogic URL mapping using actual metadata from downloaded files
Creates accurate mappings by reading the metadata.json files
"""

import json
import csv
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AccurateOtoLogicMapper:
    def __init__(self, output_file: str = "otologic_accurate_mapping.csv"):
        self.output_file = output_file
        self.base_url = "https://otologic.jp/free/se"
        self.mappings = []
        
    def scan_metadata_files(self) -> List[Path]:
        """Find all metadata.json files in otologic directories"""
        metadata_files = []
        
        # Scan otologic directories
        otologic_dirs = [
            "otologic_sounds",
            "otologic_sounds_smart",
            "otologic_english_sounds",
            "otologic_sounds_complete"
        ]
        
        for dir_name in otologic_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists():
                # Find all metadata.json files
                found_files = list(dir_path.rglob("metadata.json"))
                metadata_files.extend(found_files)
                logger.info(f"Found {len(found_files)} metadata files in {dir_name}")
        
        return metadata_files
    
    def extract_from_metadata(self, metadata_file: Path) -> List[Dict]:
        """Extract accurate mapping from a metadata.json file"""
        mappings = []
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get the page URL (this is the accurate source)
            page_url = data.get('page_url', '')
            title = data.get('title', '')
            description = data.get('description', '')
            keywords = data.get('keywords', [])
            category = data.get('category', '')
            usage_examples = data.get('usage_examples', '')
            creator_comment = data.get('creator_comment', '')
            
            # Get the files list
            files = data.get('files', [])
            
            # Find actual audio files in the same directory
            audio_files = []
            metadata_dir = metadata_file.parent
            
            for file_path in metadata_dir.iterdir():
                if file_path.suffix.lower() in ['.mp3', '.wav', '.flac', '.aiff']:
                    audio_files.append(file_path)
            
            # Create mappings for each audio file
            for audio_file in audio_files:
                # Generate download URL based on actual structure
                download_url = self.generate_download_url(audio_file.name, page_url)
                
                mapping = {
                    'original_filename': audio_file.name,
                    'english_filename': audio_file.name,
                    'title': title,
                    'description': description,
                    'keywords': ', '.join(keywords) if isinstance(keywords, list) else str(keywords),
                    'usage_examples': usage_examples,
                    'category': category,
                    'publish_date': data.get('publish_date', ''),
                    'creator_comment': creator_comment,
                    'generated_prompt': data.get('generated_prompt', ''),
                    'page_url': page_url,
                    'download_url': download_url,
                    'metadata_quality': json.dumps(data.get('metadata_quality', {}), ensure_ascii=False),
                    'file_path': str(audio_file),
                    'directory': metadata_dir.name,
                    'file_size': audio_file.stat().st_size if audio_file.exists() else 0
                }
                mappings.append(mapping)
        
        except Exception as e:
            logger.warning(f"Error processing metadata file {metadata_file}: {e}")
        
        return mappings
    
    def generate_download_url(self, filename: str, page_url: str) -> str:
        """Generate actual download URL based on the page URL pattern"""
        if not page_url:
            return ""
        
        # Extract category from page URL
        # e.g., https://otologic.jp/free/se/instruments-percussion03.html -> instruments-percussion03
        match = re.search(r'/free/se/([^/]+)\.html', page_url)
        if match:
            page_name = match.group(1)
            # The download URL pattern appears to be based on the page structure
            return f"https://otologic.jp/free/se/mp3/{page_name}/{filename}"
        
        return ""
    
    def add_csv_mappings(self) -> None:
        """Add mappings from the existing CSV files"""
        csv_files = [
            "otologic_filenames.csv"
        ]
        
        for csv_file in csv_files:
            if Path(csv_file).exists():
                logger.info(f"Adding mappings from {csv_file}")
                try:
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        
                        for row in reader:
                            original_filename = row.get('original_filename', '')
                            english_filename = row.get('english_filename', '')
                            
                            if original_filename:
                                # Try to determine category from filename
                                category, page_url = self.guess_category_from_filename(original_filename)
                                download_url = self.generate_download_url(original_filename, page_url)
                                
                                mapping = {
                                    'original_filename': original_filename,
                                    'english_filename': english_filename,
                                    'title': '',
                                    'description': '',
                                    'keywords': '',
                                    'usage_examples': '',
                                    'category': category,
                                    'publish_date': '',
                                    'creator_comment': '',
                                    'generated_prompt': '',
                                    'page_url': page_url,
                                    'download_url': download_url,
                                    'metadata_quality': '{}',
                                    'file_path': f"{csv_file}",
                                    'directory': 'csv_source',
                                    'file_size': 0
                                }
                                self.mappings.append(mapping)
                
                except Exception as e:
                    logger.error(f"Error reading {csv_file}: {e}")
    
    def guess_category_from_filename(self, filename: str) -> Tuple[str, str]:
        """Guess category from Japanese filename patterns"""
        filename_lower = filename.lower()
        
        # Japanese filename patterns
        if 'gb' in filename and ('rpg' in filename or 'ゲーム' in filename):
            return 'Game', f"{self.base_url}/game01.html"
        elif 'アクション' in filename or 'action' in filename:
            return 'Game', f"{self.base_url}/game01.html"
        elif 'シューティング' in filename or 'shooting' in filename:
            return 'Game', f"{self.base_url}/game01.html"
        elif 'レース' in filename or 'racing' in filename:
            return 'Game', f"{self.base_url}/game01.html"
        elif '格闘' in filename or 'fighting' in filename:
            return 'Game', f"{self.base_url}/game01.html"
        elif '汎用' in filename or 'general' in filename:
            return 'Game', f"{self.base_url}/game01.html"
        elif 'マルチ' in filename or 'multi' in filename:
            return 'Multi Accent', f"{self.base_url}/multi-accent01.html"
        elif 'シングル' in filename or 'single' in filename:
            return 'Single Accent', f"{self.base_url}/single-accent01.html"
        elif '骨折' in filename or 'fracture' in filename:
            return 'Fracture', f"{self.base_url}/fracture01.html"
        elif 'モーション' in filename or 'motion' in filename:
            return 'Motion Agility', f"{self.base_url}/motion-agility01.html"
        elif '電話' in filename or 'phone' in filename:
            return 'Phone', f"{self.base_url}/phone01.html"
        elif 'pc' in filename or 'パソコン' in filename:
            return 'PC', f"{self.base_url}/pc01.html"
        else:
            return 'Recent', f"{self.base_url}/recent.html"
    
    def remove_duplicates(self) -> None:
        """Remove duplicate mappings based on filename"""
        seen_filenames = set()
        unique_mappings = []
        
        for mapping in self.mappings:
            filename = mapping.get('original_filename', '')
            if filename and filename not in seen_filenames:
                seen_filenames.add(filename)
                unique_mappings.append(mapping)
        
        logger.info(f"Removed {len(self.mappings) - len(unique_mappings)} duplicates")
        self.mappings = unique_mappings
    
    def generate_mapping(self) -> None:
        """Generate the accurate mapping"""
        logger.info("Starting accurate OtoLogic mapping generation...")
        
        # Scan for metadata files
        metadata_files = self.scan_metadata_files()
        
        if metadata_files:
            logger.info(f"Processing {len(metadata_files)} metadata files...")
            
            for metadata_file in metadata_files:
                file_mappings = self.extract_from_metadata(metadata_file)
                self.mappings.extend(file_mappings)
        
        # Add CSV mappings
        self.add_csv_mappings()
        
        # Remove duplicates
        self.remove_duplicates()
        
        logger.info(f"Total accurate mappings: {len(self.mappings)}")
    
    def write_csv(self) -> None:
        """Write the accurate mappings to CSV"""
        if not self.mappings:
            logger.warning("No mappings to write")
            return
        
        try:
            with open(self.output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'original_filename', 'english_filename', 'title', 'description',
                    'keywords', 'usage_examples', 'category', 'publish_date',
                    'creator_comment', 'generated_prompt', 'page_url', 'download_url',
                    'metadata_quality', 'file_path', 'directory', 'file_size'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for mapping in self.mappings:
                    writer.writerow(mapping)
            
            logger.info(f"Successfully wrote {len(self.mappings)} accurate mappings to {self.output_file}")
            
        except Exception as e:
            logger.error(f"Error writing CSV file: {e}")
    
    def print_summary(self) -> None:
        """Print summary of the accurate mapping"""
        if not self.mappings:
            return
        
        print(f"\n📊 ACCURATE OTOLOGIC MAPPING SUMMARY:")
        print(f"   Total accurate mappings: {len(self.mappings)}")
        print(f"   Output file: {self.output_file}")
        
        # Count by category
        category_counts = {}
        for mapping in self.mappings:
            category = mapping.get('category', 'Unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        print(f"\n📁 ACCURATE CATEGORIES:")
        for category, count in sorted(category_counts.items()):
            print(f"   {category}: {count} files")
        
        # Show sample accurate mappings
        print(f"\n📋 SAMPLE ACCURATE MAPPINGS:")
        for i, mapping in enumerate(self.mappings[:5]):
            print(f"   {i+1}. {mapping['original_filename'][:50]}...")
            print(f"      Category: {mapping['category']}")
            print(f"      Page URL: {mapping['page_url']}")
            print(f"      Download URL: {mapping['download_url']}")
            print()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate accurate OtoLogic URL mapping")
    parser.add_argument("--output", default="otologic_accurate_mapping.csv",
                       help="Output CSV filename")
    
    args = parser.parse_args()
    
    # Create mapper
    mapper = AccurateOtoLogicMapper(args.output)
    
    # Generate mapping
    mapper.generate_mapping()
    
    # Write CSV
    mapper.write_csv()
    
    # Print summary
    mapper.print_summary()

if __name__ == "__main__":
    main() 
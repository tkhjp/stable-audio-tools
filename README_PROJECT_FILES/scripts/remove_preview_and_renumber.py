#!/usr/bin/env python3
"""
Remove Preview Files and Renumber Script

This script:
1. Reads the sequential_audio_mapping.csv file
2. Identifies files with 'プレビュー' in their original filename
3. Removes those files from the audio folder
4. Renumbers the remaining files sequentially (sound_1.mp3, sound_2.mp3, etc.)
5. Creates a new mapping CSV with updated sequential numbers
"""

import os
import shutil
import csv
import pandas as pd
from pathlib import Path
from typing import Dict, List
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('remove_preview_and_renumber.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PreviewRemoverAndRenumberer:
    def __init__(self, audio_dir: str = "audio", mapping_csv: str = "sequential_audio_mapping.csv"):
        self.audio_dir = Path(audio_dir)
        self.mapping_csv = Path(mapping_csv)
        self.new_mapping_csv = Path("sequential_audio_mapping_no_preview.csv")
        
        # Storage for mapping data
        self.preview_files = []
        self.non_preview_files = []
        
    def analyze_files(self):
        """Analyze the mapping CSV to identify preview and non-preview files"""
        logger.info("🔍 Analyzing files from mapping CSV")
        
        if not self.mapping_csv.exists():
            logger.error(f"Mapping CSV {self.mapping_csv} does not exist")
            return False
        
        try:
            df = pd.read_csv(self.mapping_csv)
            logger.info(f"Found {len(df)} files in mapping CSV")
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return False
        
        # Separate preview and non-preview files
        for index, row in df.iterrows():
            file_data = {
                'sequential_number': row['sequential_number'],
                'sequential_filename': row['sequential_filename'],
                'original_filename': row['original_filename'],
                'source': row['source'],
                'original_path': row['original_path'],
                'duration_seconds': row['duration_seconds'],
                'duration_minutes': row['duration_minutes'],
                'csv_path': row['csv_path']
            }
            
            if 'プレビュー' in row['original_filename']:
                self.preview_files.append(file_data)
            else:
                self.non_preview_files.append(file_data)
        
        logger.info(f"📊 Found {len(self.preview_files)} preview files to remove")
        logger.info(f"📊 Found {len(self.non_preview_files)} non-preview files to keep")
        
        return True
    
    def remove_preview_files(self):
        """Remove preview files from the audio directory"""
        logger.info("🗑️ Removing preview files from audio directory")
        
        removed_count = 0
        not_found_count = 0
        
        for file_data in self.preview_files:
            file_path = self.audio_dir / file_data['sequential_filename']
            
            if file_path.exists():
                try:
                    os.remove(file_path)
                    removed_count += 1
                    logger.debug(f"Removed: {file_data['sequential_filename']}")
                except Exception as e:
                    logger.error(f"Error removing {file_data['sequential_filename']}: {e}")
            else:
                not_found_count += 1
                logger.warning(f"File not found: {file_data['sequential_filename']}")
        
        logger.info(f"✅ Removed {removed_count} preview files")
        if not_found_count > 0:
            logger.warning(f"⚠️ {not_found_count} preview files were not found")
        
        return removed_count
    
    def renumber_remaining_files(self):
        """Renumber the remaining files sequentially"""
        logger.info("📝 Renumbering remaining files sequentially")
        
        if not self.audio_dir.exists():
            logger.error(f"Audio directory {self.audio_dir} does not exist")
            return False
        
        # Sort non-preview files by their original sequential number
        self.non_preview_files.sort(key=lambda x: x['sequential_number'])
        
        renamed_count = 0
        temp_dir = self.audio_dir / "temp_rename"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # First, move all files to temp directory with new names
            for i, file_data in enumerate(self.non_preview_files, 1):
                old_file_path = self.audio_dir / file_data['sequential_filename']
                new_filename = f"sound_{i}.mp3"
                temp_file_path = temp_dir / new_filename
                
                if old_file_path.exists():
                    try:
                        shutil.move(str(old_file_path), str(temp_file_path))
                        
                        # Update the file data with new sequential number and filename
                        file_data['sequential_number'] = i
                        file_data['sequential_filename'] = new_filename
                        
                        renamed_count += 1
                        
                        if renamed_count % 100 == 0:
                            logger.info(f"Processed {renamed_count} files...")
                    except Exception as e:
                        logger.error(f"Error renaming {file_data['sequential_filename']}: {e}")
                else:
                    logger.warning(f"File not found for renaming: {file_data['sequential_filename']}")
            
            # Move all files back from temp directory to main directory
            for file_path in temp_dir.glob("*.mp3"):
                final_path = self.audio_dir / file_path.name
                shutil.move(str(file_path), str(final_path))
            
            # Remove temp directory
            temp_dir.rmdir()
            
            logger.info(f"✅ Successfully renumbered {renamed_count} files")
            
        except Exception as e:
            logger.error(f"Error during renumbering: {e}")
            # Clean up temp directory if it exists
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            return False
        
        return True
    
    def save_new_mapping_csv(self):
        """Save the updated mapping CSV without preview files"""
        logger.info("📄 Saving new mapping CSV file")
        
        if not self.non_preview_files:
            logger.warning("No non-preview files to save")
            return
        
        # Prepare CSV headers
        headers = [
            'sequential_number',
            'sequential_filename', 
            'original_filename',
            'source',
            'original_path',
            'duration_seconds',
            'duration_minutes',
            'csv_path'
        ]
        
        try:
            # Write the new mapping CSV
            with open(self.new_mapping_csv, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                for file_data in self.non_preview_files:
                    writer.writerow(file_data)
            
            logger.info(f"✅ New mapping CSV saved to {self.new_mapping_csv}")
            
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
            return
    
    def generate_summary(self):
        """Generate a summary of the processing"""
        total_removed = len(self.preview_files)
        total_remaining = len(self.non_preview_files)
        
        if total_remaining == 0:
            logger.warning("No files remain after preview removal")
            return
        
        # Calculate total duration of remaining files
        total_duration = sum(file_data['duration_seconds'] for file_data in self.non_preview_files)
        
        # Convert duration to hours, minutes, seconds
        hours = int(total_duration // 3600)
        minutes = int((total_duration % 3600) // 60)
        seconds = int(total_duration % 60)
        
        print(f"\n{'='*80}")
        print("📋 PREVIEW REMOVAL AND RENUMBERING SUMMARY")
        print(f"{'='*80}")
        print(f"🗑️ Preview files removed: {total_removed}")
        print(f"🎵 Files remaining: {total_remaining}")
        print(f"📁 Files saved to: {self.audio_dir}")
        print(f"📄 New mapping CSV: {self.new_mapping_csv}")
        print(f"🕐 Total duration: {total_duration:.1f} seconds ({hours:02d}:{minutes:02d}:{seconds:02d})")
        
        print(f"\n🔢 New sequential naming:")
        print(f"   📝 Range: sound_1.mp3 to sound_{total_remaining}.mp3")
        
        print(f"\n📝 Sample mappings after renumbering:")
        for i, file_data in enumerate(self.non_preview_files[:5]):
            print(f"   {i+1}. {file_data['sequential_filename']} <- {file_data['original_filename']}")
            print(f"      Source: {file_data['source']}")
        
        if total_remaining > 5:
            print(f"   ... and {total_remaining - 5} more files")
        
        print(f"\n✅ All preview files removed and remaining files renumbered!")
        
        # Show some examples of removed preview files
        print(f"\n🗑️ Examples of removed preview files:")
        for i, file_data in enumerate(self.preview_files[:5]):
            print(f"   - {file_data['original_filename']} (was {file_data['sequential_filename']})")
        
        if total_removed > 5:
            print(f"   ... and {total_removed - 5} more preview files removed")
    
    def run(self):
        """Run the complete preview removal and renumbering process"""
        try:
            # Analyze files
            if not self.analyze_files():
                logger.error("Failed to analyze files")
                return False
            
            # Remove preview files
            removed_count = self.remove_preview_files()
            
            # Renumber remaining files
            if not self.renumber_remaining_files():
                logger.error("Failed to renumber files")
                return False
            
            # Save new mapping CSV
            self.save_new_mapping_csv()
            
            # Generate summary
            self.generate_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in processing pipeline: {e}")
            raise


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove preview files and renumber remaining files")
    parser.add_argument("--audio-dir", default="audio", help="Audio directory containing sound files")
    parser.add_argument("--mapping-csv", default="sequential_audio_mapping.csv", help="Current mapping CSV file")
    
    args = parser.parse_args()
    
    try:
        processor = PreviewRemoverAndRenumberer(
            audio_dir=args.audio_dir,
            mapping_csv=args.mapping_csv
        )
        
        success = processor.run()
        
        if success:
            print("\n🎉 Process completed successfully!")
        else:
            print("\n❌ Process failed!")
            
    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main() 
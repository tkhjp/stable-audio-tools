#!/usr/bin/env python3
"""
Remove Duplicate Files and Renumber Script

This script:
1. Reads the sequential_audio_mapping_no_preview.csv file
2. Identifies duplicate records that point to the same original audio file
3. Keeps only the first occurrence of each unique original file
4. Removes duplicate files from the audio folder
5. Renumbers the remaining files sequentially (sound_1.mp3, sound_2.mp3, etc.)
6. Creates a new mapping CSV with deduplicated and renumbered files
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
        logging.FileHandler('remove_duplicates_and_renumber.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DuplicateRemoverAndRenumberer:
    def __init__(self, audio_dir: str = "audio", mapping_csv: str = "sequential_audio_mapping_no_preview.csv"):
        self.audio_dir = Path(audio_dir)
        self.mapping_csv = Path(mapping_csv)
        self.new_mapping_csv = Path("sequential_audio_mapping_final.csv")
        
        # Storage for mapping data
        self.duplicate_files = []
        self.unique_files = []
        
    def analyze_duplicates(self):
        """Analyze the mapping CSV to identify duplicate and unique files"""
        logger.info("🔍 Analyzing files for duplicates")
        
        if not self.mapping_csv.exists():
            logger.error(f"Mapping CSV {self.mapping_csv} does not exist")
            return False
        
        try:
            df = pd.read_csv(self.mapping_csv)
            logger.info(f"Found {len(df)} total files in mapping CSV")
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return False
        
        # Find duplicates based on original_path (more precise than just filename)
        # Keep the first occurrence, mark others as duplicates
        seen_originals = set()
        
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
            
            # Use original_path as the unique identifier
            original_identifier = row['original_path']
            
            if original_identifier in seen_originals:
                # This is a duplicate
                self.duplicate_files.append(file_data)
                logger.debug(f"Found duplicate: {row['original_filename']} -> {row['sequential_filename']}")
            else:
                # This is the first occurrence - keep it
                seen_originals.add(original_identifier)
                self.unique_files.append(file_data)
        
        logger.info(f"📊 Found {len(self.unique_files)} unique files to keep")
        logger.info(f"📊 Found {len(self.duplicate_files)} duplicate files to remove")
        
        return True
    
    def remove_duplicate_files(self):
        """Remove duplicate files from the audio directory"""
        logger.info("🗑️ Removing duplicate files from audio directory")
        
        removed_count = 0
        not_found_count = 0
        
        for file_data in self.duplicate_files:
            file_path = self.audio_dir / file_data['sequential_filename']
            
            if file_path.exists():
                try:
                    os.remove(file_path)
                    removed_count += 1
                    logger.debug(f"Removed duplicate: {file_data['sequential_filename']}")
                except Exception as e:
                    logger.error(f"Error removing {file_data['sequential_filename']}: {e}")
            else:
                not_found_count += 1
                logger.warning(f"Duplicate file not found: {file_data['sequential_filename']}")
        
        logger.info(f"✅ Removed {removed_count} duplicate files")
        if not_found_count > 0:
            logger.warning(f"⚠️ {not_found_count} duplicate files were not found")
        
        return removed_count
    
    def renumber_remaining_files(self):
        """Renumber the remaining unique files sequentially"""
        logger.info("📝 Renumbering remaining unique files sequentially")
        
        if not self.audio_dir.exists():
            logger.error(f"Audio directory {self.audio_dir} does not exist")
            return False
        
        # Sort unique files by their original sequential number
        self.unique_files.sort(key=lambda x: x['sequential_number'])
        
        renamed_count = 0
        temp_dir = self.audio_dir / "temp_rename"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # First, move all files to temp directory with new names
            for i, file_data in enumerate(self.unique_files, 1):
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
    
    def save_final_mapping_csv(self):
        """Save the final mapping CSV without duplicates"""
        logger.info("📄 Saving final mapping CSV file")
        
        if not self.unique_files:
            logger.warning("No unique files to save")
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
            # Write the final mapping CSV
            with open(self.new_mapping_csv, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                for file_data in self.unique_files:
                    writer.writerow(file_data)
            
            logger.info(f"✅ Final mapping CSV saved to {self.new_mapping_csv}")
            
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
            return
    
    def analyze_duplicates_detail(self):
        """Show detailed analysis of what duplicates were found"""
        if not self.duplicate_files:
            return
        
        print(f"\n🔍 DUPLICATE ANALYSIS:")
        print(f"{'='*60}")
        
        # Group duplicates by original filename for better understanding
        duplicate_groups = {}
        for dup in self.duplicate_files:
            orig_name = dup['original_filename']
            if orig_name not in duplicate_groups:
                duplicate_groups[orig_name] = []
            duplicate_groups[orig_name].append(dup)
        
        print(f"📊 Found {len(duplicate_groups)} unique original files with duplicates:")
        
        # Show top 10 most duplicated files
        sorted_groups = sorted(duplicate_groups.items(), key=lambda x: len(x[1]), reverse=True)
        for i, (orig_name, dups) in enumerate(sorted_groups[:10]):
            print(f"   {i+1}. {orig_name}")
            print(f"      Duplicates: {len(dups)} copies")
            print(f"      Sequential numbers: {', '.join(str(d['sequential_number']) for d in dups)}")
            print()
        
        if len(sorted_groups) > 10:
            print(f"   ... and {len(sorted_groups) - 10} more files with duplicates")
    
    def generate_summary(self):
        """Generate a summary of the processing"""
        total_removed = len(self.duplicate_files)
        total_remaining = len(self.unique_files)
        
        if total_remaining == 0:
            logger.warning("No files remain after duplicate removal")
            return
        
        # Calculate total duration of remaining files
        total_duration = sum(file_data['duration_seconds'] for file_data in self.unique_files)
        
        # Convert duration to hours, minutes, seconds
        hours = int(total_duration // 3600)
        minutes = int((total_duration % 3600) // 60)
        seconds = int(total_duration % 60)
        
        print(f"\n{'='*80}")
        print("📋 DUPLICATE REMOVAL AND RENUMBERING SUMMARY")
        print(f"{'='*80}")
        print(f"🗑️ Duplicate files removed: {total_removed}")
        print(f"🎵 Unique files remaining: {total_remaining}")
        print(f"📁 Files saved to: {self.audio_dir}")
        print(f"📄 Final mapping CSV: {self.new_mapping_csv}")
        print(f"🕐 Total duration: {total_duration:.1f} seconds ({hours:02d}:{minutes:02d}:{seconds:02d})")
        
        print(f"\n🔢 Final sequential naming:")
        print(f"   📝 Range: sound_1.mp3 to sound_{total_remaining}.mp3")
        
        print(f"\n📝 Sample mappings after deduplication:")
        for i, file_data in enumerate(self.unique_files[:5]):
            print(f"   {i+1}. {file_data['sequential_filename']} <- {file_data['original_filename']}")
            print(f"      Source: {file_data['source']}")
        
        if total_remaining > 5:
            print(f"   ... and {total_remaining - 5} more unique files")
        
        print(f"\n✅ All duplicates removed and remaining files renumbered!")
    
    def run(self):
        """Run the complete duplicate removal and renumbering process"""
        try:
            # Analyze for duplicates
            if not self.analyze_duplicates():
                logger.error("Failed to analyze duplicates")
                return False
            
            # Show detailed duplicate analysis
            self.analyze_duplicates_detail()
            
            # Remove duplicate files
            removed_count = self.remove_duplicate_files()
            
            # Renumber remaining files
            if not self.renumber_remaining_files():
                logger.error("Failed to renumber files")
                return False
            
            # Save final mapping CSV
            self.save_final_mapping_csv()
            
            # Generate summary
            self.generate_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in processing pipeline: {e}")
            raise


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove duplicate files and renumber remaining files")
    parser.add_argument("--audio-dir", default="audio", help="Audio directory containing sound files")
    parser.add_argument("--mapping-csv", default="sequential_audio_mapping_no_preview.csv", help="Current mapping CSV file")
    
    args = parser.parse_args()
    
    try:
        processor = DuplicateRemoverAndRenumberer(
            audio_dir=args.audio_dir,
            mapping_csv=args.mapping_csv
        )
        
        success = processor.run()
        
        if success:
            print("\n🎉 Deduplication completed successfully!")
        else:
            print("\n❌ Deduplication failed!")
            
    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main() 
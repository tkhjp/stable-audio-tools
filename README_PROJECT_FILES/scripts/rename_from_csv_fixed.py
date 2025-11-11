#!/usr/bin/env python3
"""
CSV-Based Audio File Renamer (Fixed for ZIP Structure)

This script:
1. Reads the long_audio_files_over_5.0s.csv file
2. Finds each audio file in the original directories (handling ZIP extraction structure)
3. Copies them to a new folder with sequential naming: sound_1.mp3, sound_2.mp3, etc.
4. Creates a mapping CSV file with the renaming information
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
        logging.FileHandler('rename_from_csv_fixed.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CSVBasedRenamerFixed:
    def __init__(self, csv_file: str = "long_audio_files_over_5.0s.csv", output_dir: str = "sequential_audio"):
        self.csv_file = Path(csv_file)
        self.output_dir = Path(output_dir)
        self.mapping_csv = Path("sequential_audio_mapping.csv")
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        # Storage for mapping data
        self.mapping_data = []
        
    def find_audio_file(self, source: str, filename: str, path: str) -> Path:
        """Find the actual audio file based on CSV information, handling ZIP extraction structure"""
        
        # Try different possible locations
        possible_paths = []
        
        # For ZIP-extracted sources, handle the nested directory structure
        if ".zip" in source:
            # Extract the base name without .zip
            zip_base = source.replace(".zip", "")
            
            # The extracted structure is: zip_base/zip_basename/filename
            # For example: freeaudio/anime01/anime01/filename.mp3
            zip_basename = Path(zip_base).name  # Just the last part (e.g., "anime01")
            
            # Try the nested ZIP extraction structure
            nested_path = Path(zip_base) / zip_basename / filename
            possible_paths.append(nested_path)
            
            # Also try without the nested directory (in case some ZIPs extract differently)
            flat_path = Path(zip_base) / filename
            possible_paths.append(flat_path)
            
            # Try using the full path from CSV in the extracted structure
            if path:
                csv_nested_path = Path(zip_base) / path
                possible_paths.append(csv_nested_path)
        else:
            # For non-ZIP sources, use the original logic
            if source and path:
                # Construct full path from source and path
                full_path = Path(source) / path
                possible_paths.append(full_path)
                
                # Also try with just the filename in the source directory
                possible_paths.append(Path(source) / filename)
        
        # Try finding it in subdirectories of the source
        if source:
            source_base = source.replace(".zip", "") if ".zip" in source else source
            source_path = Path(source_base)
            if source_path.exists():
                # Search recursively for the filename
                for audio_file in source_path.glob(f"**/{filename}"):
                    possible_paths.append(audio_file)
        
        # Check each possible path
        for path_option in possible_paths:
            if path_option.exists():
                return path_option
        
        return None
    
    def process_files(self):
        """Process all audio files from the CSV and create sequential copies"""
        logger.info("🚀 Starting CSV-based audio file renaming (Fixed)")
        
        # Check if CSV exists
        if not self.csv_file.exists():
            logger.error(f"CSV file {self.csv_file} does not exist")
            return 0
        
        # Read the CSV file
        logger.info(f"Reading file information from {self.csv_file}")
        
        try:
            df = pd.read_csv(self.csv_file)
            logger.info(f"Found {len(df)} files in CSV")
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return 0
        
        # Process each file
        processed_count = 0
        not_found_count = 0
        
        for index, row in df.iterrows():
            source = row['source']
            filename = row['filename']
            path = row['path'] if 'path' in row else ''
            duration_seconds = row['duration_seconds']
            duration_minutes = row['duration_minutes'] if 'duration_minutes' in row else duration_seconds / 60
            
            # Find the actual audio file
            original_path = self.find_audio_file(source, filename, path)
            
            if original_path is None:
                logger.warning(f"File not found: {filename} (source: {source}, path: {path})")
                not_found_count += 1
                continue
            
            # Create sequential filename
            sequential_number = processed_count + 1
            sequential_filename = f"sound_{sequential_number}.mp3"
            sequential_path = self.output_dir / sequential_filename
            
            try:
                # Copy file with new name
                shutil.copy2(original_path, sequential_path)
                processed_count += 1
                
                # Store mapping information
                mapping_info = {
                    'sequential_number': sequential_number,
                    'sequential_filename': sequential_filename,
                    'original_filename': filename,
                    'source': source,
                    'original_path': str(original_path),
                    'duration_seconds': duration_seconds,
                    'duration_minutes': duration_minutes,
                    'csv_path': path
                }
                
                self.mapping_data.append(mapping_info)
                
                if processed_count % 100 == 0:
                    logger.info(f"Processed {processed_count} files...")
                    
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
                continue
        
        logger.info(f"✅ Successfully processed {processed_count} files")
        logger.info(f"⚠️  Could not find {not_found_count} files")
        return processed_count
    
    def save_mapping_csv(self):
        """Save the mapping information to a CSV file"""
        logger.info("📄 Saving mapping CSV file")
        
        if not self.mapping_data:
            logger.warning("No mapping data to save")
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
            # Write the mapping CSV
            with open(self.mapping_csv, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                for mapping in self.mapping_data:
                    writer.writerow(mapping)
            
            logger.info(f"✅ Mapping CSV saved to {self.mapping_csv}")
            
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
            return
    
    def generate_summary(self):
        """Generate a summary of the processing"""
        total_files = len(self.mapping_data)
        
        if total_files == 0:
            logger.warning("No files were processed")
            return
        
        # Count by source
        source_counts = {}
        total_duration = 0
        
        for mapping in self.mapping_data:
            source = mapping['source']
            source_counts[source] = source_counts.get(source, 0) + 1
            total_duration += mapping['duration_seconds']
        
        # Convert duration to hours, minutes, seconds
        hours = int(total_duration // 3600)
        minutes = int((total_duration % 3600) // 60)
        seconds = int(total_duration % 60)
        
        print(f"\n{'='*80}")
        print("📋 CSV-BASED SEQUENTIAL RENAMING SUMMARY (FIXED)")
        print(f"{'='*80}")
        print(f"🎵 Total files processed: {total_files}")
        print(f"📁 Files saved to: {self.output_dir}")
        print(f"📄 Mapping CSV saved: {self.mapping_csv}")
        print(f"🕐 Total duration: {total_duration:.1f} seconds ({hours:02d}:{minutes:02d}:{seconds:02d})")
        
        print(f"\n📊 Files by source:")
        for source, count in source_counts.items():
            print(f"   📁 {source}: {count} files")
        
        print(f"\n🔢 Sequential naming:")
        print(f"   📝 Range: sound_1.mp3 to sound_{total_files}.mp3")
        
        print(f"\n📝 Sample mappings:")
        for i, mapping in enumerate(self.mapping_data[:5]):
            print(f"   {i+1}. {mapping['sequential_filename']} <- {mapping['original_filename']}")
            print(f"      Source: {mapping['source']}")
        
        if total_files > 5:
            print(f"   ... and {total_files - 5} more files")
        
        print(f"\n✅ All files successfully renamed and mapped!")
    
    def run(self):
        """Run the complete sequential renaming process"""
        try:
            # Process files
            processed_count = self.process_files()
            
            if processed_count > 0:
                # Save mapping CSV
                self.save_mapping_csv()
                
                # Generate summary
                self.generate_summary()
            else:
                logger.error("No files were processed")
                
        except Exception as e:
            logger.error(f"Error in processing pipeline: {e}")
            raise


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Rename audio files sequentially based on CSV (Fixed)")
    parser.add_argument("--csv-file", default="long_audio_files_over_5.0s.csv", help="Input CSV file with file list")
    parser.add_argument("--output-dir", default="sequential_audio", help="Output directory for renamed files")
    
    args = parser.parse_args()
    
    try:
        renamer = CSVBasedRenamerFixed(
            csv_file=args.csv_file,
            output_dir=args.output_dir
        )
        
        renamer.run()
        
    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main() 
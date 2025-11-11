#!/usr/bin/env python3
"""
Generate CSV mapping between Freesound filenames and their URLs
Extracts data from metadata.jsonl and creates a CSV with filename and URL columns
"""

import json
import csv
import os
from pathlib import Path
from typing import Dict, List, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_freesound_mapping(metadata_file: str = "data/metadata.jsonl", 
                             output_file: str = "freesound_filename_url_mapping.csv") -> None:
    """
    Extract filename and URL mapping from Freesound metadata
    
    Args:
        metadata_file: Path to the metadata.jsonl file
        output_file: Output CSV filename
    """
    
    metadata_path = Path(metadata_file)
    if not metadata_path.exists():
        logger.error(f"Metadata file not found: {metadata_file}")
        return
    
    logger.info(f"Processing metadata file: {metadata_file}")
    
    # Store the mappings
    mappings = []
    processed_count = 0
    error_count = 0
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    # Parse JSON line
                    data = json.loads(line.strip())
                    
                    # Extract required fields
                    sound_id = data.get('id', '')
                    filename = data.get('name', '')
                    
                    # Get the main Freesound URL
                    freesound_url = f"https://freesound.org/people/{data.get('username', '')}/sounds/{sound_id}/"
                    
                    # Get preview URLs if available
                    previews = data.get('previews', {})
                    preview_hq_mp3 = previews.get('preview-hq-mp3', '')
                    preview_lq_mp3 = previews.get('preview-lq-mp3', '')
                    
                    # Get additional metadata
                    description = data.get('description', '')
                    tags = ', '.join(data.get('tags', []))
                    category = ' > '.join(data.get('category', []))
                    license_url = data.get('license', '')
                    duration = data.get('duration', 0)
                    filesize = data.get('filesize', 0)
                    username = data.get('username', '')
                    
                    # Create mapping entry
                    mapping = {
                        'sound_id': sound_id,
                        'filename': filename,
                        'freesound_url': freesound_url,
                        'preview_hq_mp3': preview_hq_mp3,
                        'preview_lq_mp3': preview_lq_mp3,
                        'username': username,
                        'description': description,
                        'tags': tags,
                        'category': category,
                        'license': license_url,
                        'duration_seconds': duration,
                        'filesize_bytes': filesize
                    }
                    
                    mappings.append(mapping)
                    processed_count += 1
                    
                    # Log progress every 1000 files
                    if processed_count % 1000 == 0:
                        logger.info(f"Processed {processed_count} files...")
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON decode error at line {line_num}: {e}")
                    error_count += 1
                    continue
                except Exception as e:
                    logger.warning(f"Error processing line {line_num}: {e}")
                    error_count += 1
                    continue
    
    except Exception as e:
        logger.error(f"Error reading metadata file: {e}")
        return
    
    logger.info(f"Successfully processed {processed_count} files")
    if error_count > 0:
        logger.warning(f"Encountered {error_count} errors during processing")
    
    # Write to CSV
    if mappings:
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'sound_id', 'filename', 'freesound_url', 'preview_hq_mp3', 
                    'preview_lq_mp3', 'username', 'description', 'tags', 
                    'category', 'license', 'duration_seconds', 'filesize_bytes'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for mapping in mappings:
                    writer.writerow(mapping)
            
            logger.info(f"Successfully wrote {len(mappings)} mappings to {output_file}")
            
            # Print some statistics
            print(f"\n📊 MAPPING STATISTICS:")
            print(f"   Total files processed: {processed_count}")
            print(f"   Total mappings created: {len(mappings)}")
            print(f"   Errors encountered: {error_count}")
            print(f"   Output file: {output_file}")
            
            # Show sample of the data
            if mappings:
                print(f"\n📋 SAMPLE MAPPINGS:")
                for i, mapping in enumerate(mappings[:5]):
                    print(f"   {i+1}. {mapping['filename'][:50]}...")
                    print(f"      URL: {mapping['freesound_url']}")
                    print(f"      Category: {mapping['category']}")
                    print()
            
        except Exception as e:
            logger.error(f"Error writing CSV file: {e}")
    else:
        logger.warning("No mappings to write")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Freesound filename to URL mapping CSV")
    parser.add_argument("--input", default="data/metadata.jsonl", 
                       help="Input metadata.jsonl file path")
    parser.add_argument("--output", default="freesound_filename_url_mapping.csv",
                       help="Output CSV filename")
    
    args = parser.parse_args()
    
    # Generate the mapping
    extract_freesound_mapping(args.input, args.output)

if __name__ == "__main__":
    main() 
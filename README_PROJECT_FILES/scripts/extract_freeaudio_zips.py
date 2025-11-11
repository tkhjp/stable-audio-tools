#!/usr/bin/env python3
"""
Extract all ZIP files in freeaudio directory

This script extracts all ZIP files in the freeaudio directory,
creating a subdirectory for each ZIP file.
"""

import os
import zipfile
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extract_freeaudio_zips.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def extract_zip_files(freeaudio_dir: str = "freeaudio"):
    """Extract all ZIP files in the freeaudio directory"""
    
    freeaudio_path = Path(freeaudio_dir)
    
    if not freeaudio_path.exists():
        logger.error(f"Directory {freeaudio_dir} does not exist")
        return
    
    # Find all ZIP files
    zip_files = list(freeaudio_path.glob("*.zip"))
    logger.info(f"Found {len(zip_files)} ZIP files to extract")
    
    extracted_count = 0
    skipped_count = 0
    error_count = 0
    
    for zip_file in zip_files:
        # Create directory name (same as ZIP file without .zip extension)
        extract_dir = freeaudio_path / zip_file.stem
        
        # Check if directory already exists and has files
        if extract_dir.exists() and any(extract_dir.iterdir()):
            logger.info(f"⏭️  Skipping {zip_file.name} - directory {extract_dir.name} already exists and has content")
            skipped_count += 1
            continue
        
        try:
            logger.info(f"📦 Extracting {zip_file.name}...")
            
            # Create the directory if it doesn't exist
            extract_dir.mkdir(exist_ok=True)
            
            # Extract the ZIP file
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Count extracted files
            extracted_files = list(extract_dir.rglob("*"))
            file_count = len([f for f in extracted_files if f.is_file()])
            
            logger.info(f"✅ Extracted {zip_file.name} → {extract_dir.name}/ ({file_count} files)")
            extracted_count += 1
            
        except Exception as e:
            logger.error(f"❌ Error extracting {zip_file.name}: {e}")
            error_count += 1
    
    logger.info(f"\n📋 EXTRACTION SUMMARY:")
    logger.info(f"   ✅ Extracted: {extracted_count} ZIP files")
    logger.info(f"   ⏭️  Skipped: {skipped_count} ZIP files (already exist)")
    logger.info(f"   ❌ Errors: {error_count} ZIP files")
    
    return extracted_count

def main():
    """Main function"""
    try:
        extracted_count = extract_zip_files()
        
        if extracted_count > 0:
            logger.info(f"\n🎯 Next step: Re-run the renaming script to process newly extracted files!")
        else:
            logger.info(f"\n✅ All ZIP files were already extracted or skipped")
            
    except Exception as e:
        logger.error(f"Error in extraction pipeline: {e}")
        raise

if __name__ == "__main__":
    main() 
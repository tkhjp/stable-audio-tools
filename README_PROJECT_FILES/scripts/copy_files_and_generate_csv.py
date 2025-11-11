#!/usr/bin/env python3
"""
Script to copy MP3 files to a new folder and generate a CSV with duration information
"""

import os
import shutil
import csv
from pathlib import Path

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3NoHeaderError
except ImportError:
    print("Installing mutagen library...")
    import subprocess
    subprocess.check_call(["pip", "install", "mutagen"])
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3NoHeaderError

def parse_file_list(file_path):
    """Parse the corrected category files list"""
    categories = {}
    current_category = None
    current_files = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        line_original = line
        line = line.strip()
        
        # Skip empty lines and headers
        if not line or line.startswith('=') or line.startswith('OtoLogic') or line.startswith('Total files'):
            continue
            
        # Skip separator lines
        if '----' in line:
            continue
            
        # Skip "Files: X" lines
        if line.startswith('Files:'):
            continue
            
        # Check for category headers (lines that end with parentheses and contain descriptions)
        if '(' in line and line.endswith(')') and not line.endswith('.mp3'):
            # Save previous category
            if current_category and current_files:
                categories[current_category] = current_files
            
            # Start new category - extract the Japanese name before the parentheses
            current_category = line.split(' (')[0].strip()
            current_files = []
        elif line.endswith('.mp3') and current_category:
            # This is an MP3 file - remove leading spaces but preserve the relative path
            file_path = line_original.strip()
            current_files.append(file_path)
    
    # Don't forget the last category
    if current_category and current_files:
        categories[current_category] = current_files
    
    return categories

def get_mp3_duration(file_path):
    """Get duration of MP3 file in seconds"""
    try:
        audio = MP3(file_path)
        return audio.info.length if audio.info.length else 0
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def format_duration(seconds):
    """Format duration as MM:SS"""
    if seconds is None:
        return "N/A"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def copy_files_and_generate_csv():
    """Main function to copy files and generate CSV"""
    
    # Directories
    source_dir = Path("otologic_sounds_smart")
    dest_dir = Path("otologic_duration_analysis")
    
    # Create destination directory if it doesn't exist
    dest_dir.mkdir(exist_ok=True)
    
    if not source_dir.exists():
        print(f"Error: {source_dir} directory not found!")
        return
    
    # Parse the file list
    print("Parsing corrected category files list...")
    categories = parse_file_list("corrected_category_files_list.txt")
    
    # Prepare CSV data
    csv_data = []
    csv_headers = [
        'filename', 'category', 'original_path', 'new_path', 
        'duration_seconds', 'duration_formatted', 'file_size_bytes'
    ]
    
    total_files = sum(len(files) for files in categories.values())
    processed_files = 0
    copied_files = 0
    
    print(f"Processing {total_files} files across {len(categories)} categories...")
    
    for category, file_list in categories.items():
        print(f"\nProcessing category: {category} ({len(file_list)} files)")
        
        # Create category subdirectory
        category_dir = dest_dir / category
        category_dir.mkdir(exist_ok=True)
        
        for relative_path in file_list:
            source_file = source_dir / relative_path
            
            if source_file.exists():
                # Extract filename
                filename = source_file.name
                
                # Create destination path (flatten the structure)
                dest_file = category_dir / filename
                
                # Handle duplicate filenames by adding a counter
                counter = 1
                original_dest = dest_file
                while dest_file.exists():
                    name_parts = original_dest.stem, counter, original_dest.suffix
                    dest_file = original_dest.parent / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                    counter += 1
                
                try:
                    # Copy file
                    shutil.copy2(source_file, dest_file)
                    copied_files += 1
                    
                    # Get duration and file size
                    duration = get_mp3_duration(dest_file)
                    file_size = dest_file.stat().st_size
                    
                    # Add to CSV data
                    csv_data.append({
                        'filename': dest_file.name,
                        'category': category,
                        'original_path': str(relative_path),
                        'new_path': str(dest_file.relative_to(dest_dir)),
                        'duration_seconds': duration if duration is not None else 0,
                        'duration_formatted': format_duration(duration),
                        'file_size_bytes': file_size
                    })
                    
                except Exception as e:
                    print(f"  Error copying {source_file}: {e}")
            else:
                print(f"  File not found: {relative_path}")
            
            processed_files += 1
            
            # Progress indicator
            if processed_files % 100 == 0:
                print(f"  Processed {processed_files}/{total_files} files, copied {copied_files} files")
    
    # Generate CSV file
    csv_file = dest_dir / "mp3_duration_analysis.csv"
    print(f"\nGenerating CSV file: {csv_file}")
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(csv_data)
    
    # Generate summary statistics
    total_duration = sum(row['duration_seconds'] for row in csv_data if row['duration_seconds'])
    total_size = sum(row['file_size_bytes'] for row in csv_data)
    
    # Summary report
    print(f"\n" + "="*60)
    print("COPY AND ANALYSIS SUMMARY")
    print(f"="*60)
    print(f"Total files processed: {processed_files}")
    print(f"Total files copied: {copied_files}")
    print(f"Total duration: {format_duration(total_duration)} ({total_duration/3600:.1f} hours)")
    print(f"Total file size: {total_size/1024/1024:.1f} MB")
    print(f"Files copied to: {dest_dir}")
    print(f"CSV analysis saved to: {csv_file}")
    
    # Category summary
    print(f"\nCategory breakdown:")
    for category in categories.keys():
        category_files = [row for row in csv_data if row['category'] == category]
        category_duration = sum(row['duration_seconds'] for row in category_files)
        category_size = sum(row['file_size_bytes'] for row in category_files)
        print(f"  {category}: {len(category_files)} files, {format_duration(category_duration)}, {category_size/1024/1024:.1f} MB")

if __name__ == "__main__":
    copy_files_and_generate_csv() 
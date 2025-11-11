#!/usr/bin/env python3
"""
Analyze duration distribution of all audio files in freeaudio directory
"""

import os
import zipfile
from pathlib import Path
from mutagen import File
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict
import time

def get_audio_duration(audio_path):
    """Get duration of audio file in seconds"""
    try:
        audio_file = File(audio_path)
        if audio_file is not None and hasattr(audio_file, 'info'):
            return audio_file.info.length
        return 0.0
    except Exception as e:
        print(f"❌ Error getting duration for {audio_path}: {e}")
        return 0.0

def analyze_zip_file(zip_path):
    """Analyze audio files within a ZIP file"""
    durations = []
    files_info = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            mp3_files = [f for f in zip_ref.namelist() if f.endswith('.mp3')]
            print(f"📦 {zip_path.name}: {len(mp3_files)} MP3 files")
            
            for mp3_file in mp3_files:
                try:
                    # Extract to temp location and analyze
                    temp_dir = Path("temp_audio_analysis")
                    temp_dir.mkdir(exist_ok=True)
                    
                    zip_ref.extract(mp3_file, temp_dir)
                    temp_file_path = temp_dir / mp3_file
                    
                    duration = get_audio_duration(temp_file_path)
                    durations.append(duration)
                    files_info.append({
                        'source': zip_path.name,
                        'filename': Path(mp3_file).name,
                        'duration': duration,
                        'type': 'zip'
                    })
                    
                    # Clean up temp file
                    temp_file_path.unlink()
                    
                except Exception as e:
                    print(f"  ❌ Error processing {mp3_file}: {e}")
    
    except Exception as e:
        print(f"❌ Error processing ZIP {zip_path}: {e}")
    
    return durations, files_info

def analyze_extracted_directory(dir_path):
    """Analyze audio files in an extracted directory"""
    durations = []
    files_info = []
    
    mp3_files = list(dir_path.glob("**/*.mp3"))
    print(f"📁 {dir_path.name}: {len(mp3_files)} MP3 files")
    
    for mp3_file in mp3_files:
        duration = get_audio_duration(mp3_file)
        durations.append(duration)
        files_info.append({
            'source': dir_path.name,
            'filename': mp3_file.name,
            'duration': duration,
            'type': 'extracted'
        })
    
    return durations, files_info

def create_duration_distribution_plot(all_durations, all_files_info):
    """Create plots showing duration distribution"""
    
    # Create DataFrame for easier analysis
    df = pd.DataFrame(all_files_info)
    
    # Print statistics
    print("\n" + "="*60)
    print("📊 DURATION DISTRIBUTION ANALYSIS")
    print("="*60)
    print(f"Total audio files analyzed: {len(df)}")
    print(f"Total duration: {df['duration'].sum():.1f} seconds ({df['duration'].sum()/3600:.1f} hours)")
    print(f"Average duration: {df['duration'].mean():.2f} seconds")
    print(f"Median duration: {df['duration'].median():.2f} seconds")
    print(f"Min duration: {df['duration'].min():.2f} seconds")
    print(f"Max duration: {df['duration'].max():.2f} seconds")
    
    # Duration categories for analysis
    categories = {
        "Very Short (0-5s)": (0, 5),
        "Short (5-15s)": (5, 15),
        "Medium (15-30s)": (15, 30),
        "Long (30-60s)": (30, 60),
        "Very Long (60s+)": (60, float('inf'))
    }
    
    print(f"\n📈 DURATION CATEGORIES:")
    for category, (min_dur, max_dur) in categories.items():
        if max_dur == float('inf'):
            count = len(df[df['duration'] >= min_dur])
        else:
            count = len(df[(df['duration'] >= min_dur) & (df['duration'] < max_dur)])
        percentage = (count / len(df)) * 100
        print(f"  {category}: {count} files ({percentage:.1f}%)")
    
    # Token limit analysis (estimate based on 91s = 1.7M tokens)
    token_rate = 1700000 / 91  # tokens per second (rough estimate)
    print(f"\n🔍 TOKEN LIMIT ANALYSIS (128k limit):")
    safe_threshold = 128000 / token_rate  # seconds that would be safe
    print(f"  Estimated safe duration threshold: {safe_threshold:.1f} seconds")
    
    risky_files = df[df['duration'] > safe_threshold]
    print(f"  Files likely to exceed token limit: {len(risky_files)} ({len(risky_files)/len(df)*100:.1f}%)")
    
    # Top sources by file count
    print(f"\n📦 TOP SOURCES BY FILE COUNT:")
    source_counts = df['source'].value_counts().head(10)
    for source, count in source_counts.items():
        avg_duration = df[df['source'] == source]['duration'].mean()
        print(f"  {source}: {count} files (avg: {avg_duration:.1f}s)")
    
    # Files that would definitely cause token issues
    problem_files = df[df['duration'] > 30]  # Conservative threshold
    if len(problem_files) > 0:
        print(f"\n⚠️  FILES LIKELY TO CAUSE TOKEN ISSUES (>30s):")
        for _, file_info in problem_files.head(20).iterrows():
            print(f"  {file_info['source']}/{file_info['filename']}: {file_info['duration']:.1f}s")
        if len(problem_files) > 20:
            print(f"  ... and {len(problem_files) - 20} more")

def main():
    """Main analysis function"""
    freeaudio_dir = Path("freeaudio")
    
    if not freeaudio_dir.exists():
        print("❌ freeaudio directory not found!")
        return
    
    print("🔍 Analyzing audio file duration distribution in freeaudio directory...")
    print("="*80)
    
    all_durations = []
    all_files_info = []
    
    # Create temp directory for analysis
    temp_dir = Path("temp_audio_analysis")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Analyze ZIP files
        zip_files = list(freeaudio_dir.glob("*.zip"))
        print(f"Found {len(zip_files)} ZIP files to analyze...")
        
        for i, zip_file in enumerate(zip_files, 1):
            print(f"\n[{i}/{len(zip_files)}] Processing {zip_file.name}...")
            durations, files_info = analyze_zip_file(zip_file)
            all_durations.extend(durations)
            all_files_info.extend(files_info)
        
        # Analyze extracted directories
        extracted_dirs = [d for d in freeaudio_dir.iterdir() if d.is_dir()]
        print(f"\nFound {len(extracted_dirs)} extracted directories to analyze...")
        
        for i, dir_path in enumerate(extracted_dirs, 1):
            print(f"\n[{i}/{len(extracted_dirs)}] Processing {dir_path.name}...")
            durations, files_info = analyze_extracted_directory(dir_path)
            all_durations.extend(durations)
            all_files_info.extend(files_info)
        
        # Create analysis and plots
        create_duration_distribution_plot(all_durations, all_files_info)
        
        # Save detailed results to CSV
        df = pd.DataFrame(all_files_info)
        output_file = "freeaudio_duration_analysis.csv"
        df.to_csv(output_file, index=False)
        print(f"\n💾 Detailed results saved to: {output_file}")
        
    finally:
        # Clean up temp directory
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main() 
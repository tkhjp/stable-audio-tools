#!/usr/bin/env python3
"""
Analyze duration of audio files containing 'プレビュー' (preview) in otologic_sounds_smart directory
"""

from pathlib import Path
from mutagen import File
import sys

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

def find_preview_files(base_dir):
    """Find all audio files containing 'プレビュー' in their names"""
    preview_files = []
    
    # Search for all audio files recursively
    audio_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
    
    for ext in audio_extensions:
        for audio_file in base_dir.glob(f"**/*{ext}"):
            if 'プレビュー' in audio_file.name:
                preview_files.append(audio_file)
    
    return preview_files

def analyze_preview_files():
    """Main analysis function"""
    base_dir = Path("otologic_duration_analysis")
    
    if not base_dir.exists():
        print("❌ otologic_sounds_smart directory not found!")
        return
    
    print("🔍 Searching for audio files containing 'プレビュー' in otologic_sounds_smart...")
    print("="*80)
    
    # Find all preview files
    preview_files = find_preview_files(base_dir)
    
    if not preview_files:
        print("❌ No audio files containing 'プレビュー' found!")
        return
    
    print(f"📁 Found {len(preview_files)} preview files:")
    print()
    
    total_duration = 0.0
    successful_files = 0
    
    for i, file_path in enumerate(preview_files, 1):
        duration = get_audio_duration(file_path)
        
        if duration > 0:
            total_duration += duration
            successful_files += 1
            
        # Show relative path from otologic_sounds_smart
        relative_path = file_path.relative_to(base_dir)
        
        print(f"{i:3d}. {relative_path}")
        print(f"     Duration: {duration:.2f} seconds ({int(duration//60):02d}:{int(duration%60):02d})")
        print()
    
    # Summary
    print("="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"Total files found: {len(preview_files)}")
    print(f"Successfully analyzed: {successful_files}")
    print(f"Failed to analyze: {len(preview_files) - successful_files}")
    print()
    
    # Duration summary
    total_hours = int(total_duration // 3600)
    total_minutes = int((total_duration % 3600) // 60)
    total_seconds = int(total_duration % 60)
    
    print(f"🕐 TOTAL DURATION:")
    print(f"  {total_duration:.2f} seconds")
    print(f"  {total_hours:02d}:{total_minutes:02d}:{total_seconds:02d} (HH:MM:SS)")
    print(f"  {total_duration/60:.2f} minutes")
    print(f"  {total_duration/3600:.2f} hours")
    
    # Average duration
    if successful_files > 0:
        avg_duration = total_duration / successful_files
        print(f"\n📈 AVERAGE DURATION:")
        print(f"  {avg_duration:.2f} seconds per file")
        print(f"  {int(avg_duration//60):02d}:{int(avg_duration%60):02d} (MM:SS)")

if __name__ == "__main__":
    analyze_preview_files() 
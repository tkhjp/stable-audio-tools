#!/usr/bin/env python3
"""
Analyze duration of audio files over 5 seconds in both otologic_sounds_smart and freeaudio directories
"""

import zipfile
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

def analyze_extracted_directory(dir_path, min_duration=5.0):
    """Analyze audio files in an extracted directory"""
    long_files = []
    total_duration = 0.0
    
    # Search for all audio files recursively
    audio_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
    
    for ext in audio_extensions:
        for audio_file in dir_path.glob(f"**/*{ext}"):
            duration = get_audio_duration(audio_file)
            if duration > min_duration:
                relative_path = audio_file.relative_to(dir_path)
                long_files.append({
                    'path': relative_path,
                    'full_path': audio_file,
                    'duration': duration,
                    'source_type': 'extracted'
                })
                total_duration += duration
    
    return long_files, total_duration

def analyze_zip_file(zip_path, min_duration=5.0):
    """Analyze audio files within a ZIP file"""
    long_files = []
    total_duration = 0.0
    
    try:
        # Create temp directory for analysis
        temp_dir = Path("temp_audio_analysis")
        temp_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            audio_files = [f for f in zip_ref.namelist() 
                          if any(f.endswith(ext) for ext in ['.mp3', '.wav', '.m4a', '.flac', '.ogg'])]
            
            for audio_file in audio_files:
                try:
                    # Extract to temp location and analyze
                    zip_ref.extract(audio_file, temp_dir)
                    temp_file_path = temp_dir / audio_file
                    
                    duration = get_audio_duration(temp_file_path)
                    
                    if duration > min_duration:
                        long_files.append({
                            'path': audio_file,
                            'full_path': temp_file_path,
                            'duration': duration,
                            'source_type': 'zip'
                        })
                        total_duration += duration
                    
                    # Clean up temp file
                    temp_file_path.unlink()
                    
                except Exception as e:
                    print(f"  ❌ Error processing {audio_file}: {e}")
    
    except Exception as e:
        print(f"❌ Error processing ZIP {zip_path}: {e}")
    
    # Clean up temp directory
    if temp_dir.exists():
        import shutil
        shutil.rmtree(temp_dir)
    
    return long_files, total_duration

def analyze_directory_comprehensive(base_dir, dir_name, min_duration=5.0):
    """Analyze a directory comprehensively (both extracted dirs and ZIP files)"""
    print(f"\n🔍 Analyzing {dir_name}...")
    print("="*60)
    
    all_long_files = []
    total_duration = 0.0
    
    if not base_dir.exists():
        print(f"❌ {dir_name} directory not found!")
        return all_long_files, total_duration
    
    # Analyze extracted directories first
    extracted_dirs = [d for d in base_dir.iterdir() if d.is_dir()]
    if extracted_dirs:
        print(f"📁 Found {len(extracted_dirs)} extracted directories...")
        
        for i, dir_path in enumerate(extracted_dirs, 1):
            print(f"  [{i}/{len(extracted_dirs)}] Processing {dir_path.name}...")
            long_files, duration_sum = analyze_extracted_directory(dir_path, min_duration)
            
            for file_info in long_files:
                file_info['source'] = f"{dir_name}/{dir_path.name}"
                all_long_files.append(file_info)
            
            total_duration += duration_sum
            print(f"    Found {len(long_files)} files over {min_duration}s (total: {duration_sum:.1f}s)")
    
    # Analyze ZIP files
    zip_files = list(base_dir.glob("*.zip"))
    if zip_files:
        print(f"\n📦 Found {len(zip_files)} ZIP files...")
        
        for i, zip_file in enumerate(zip_files, 1):
            print(f"  [{i}/{len(zip_files)}] Processing {zip_file.name}...")
            long_files, duration_sum = analyze_zip_file(zip_file, min_duration)
            
            for file_info in long_files:
                file_info['source'] = f"{dir_name}/{zip_file.name}"
                all_long_files.append(file_info)
            
            total_duration += duration_sum
            print(f"    Found {len(long_files)} files over {min_duration}s (total: {duration_sum:.1f}s)")
    
    print(f"\n📊 {dir_name} Summary:")
    print(f"  Total files over {min_duration}s: {len(all_long_files)}")
    print(f"  Total duration: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
    
    return all_long_files, total_duration

def main():
    """Main analysis function"""
    min_duration = 5.0
    
    print(f"🔍 Analyzing audio files over {min_duration} seconds in both directories...")
    print("="*80)
    
    all_files = []
    grand_total_duration = 0.0
    
    # Analyze otologic_sounds_smart
    otologic_dir = Path("otologic_sounds_smart")
    otologic_files, otologic_duration = analyze_directory_comprehensive(
        otologic_dir, "otologic_sounds_smart", min_duration
    )
    all_files.extend(otologic_files)
    grand_total_duration += otologic_duration
    
    # Analyze freeaudio
    freeaudio_dir = Path("freeaudio")
    freeaudio_files, freeaudio_duration = analyze_directory_comprehensive(
        freeaudio_dir, "freeaudio", min_duration
    )
    all_files.extend(freeaudio_files)
    grand_total_duration += freeaudio_duration
    
    # Final Summary
    print("\n" + "="*80)
    print("🎯 FINAL SUMMARY")
    print("="*80)
    print(f"📁 otologic_sounds_smart: {len(otologic_files)} files, {otologic_duration:.1f}s ({otologic_duration/60:.1f} min)")
    print(f"📁 freeaudio: {len(freeaudio_files)} files, {freeaudio_duration:.1f}s ({freeaudio_duration/60:.1f} min)")
    print()
    print(f"🎵 TOTAL FILES OVER {min_duration}s: {len(all_files)}")
    print(f"🕐 TOTAL DURATION: {grand_total_duration:.1f} seconds")
    print(f"   = {grand_total_duration/60:.1f} minutes")
    print(f"   = {grand_total_duration/3600:.2f} hours")
    
    # Convert to HH:MM:SS format
    total_hours = int(grand_total_duration // 3600)
    total_minutes = int((grand_total_duration % 3600) // 60)
    total_seconds = int(grand_total_duration % 60)
    print(f"   = {total_hours:02d}:{total_minutes:02d}:{total_seconds:02d} (HH:MM:SS)")
    
    # Show longest files
    if all_files:
        print(f"\n🏆 TOP 10 LONGEST FILES:")
        sorted_files = sorted(all_files, key=lambda x: x['duration'], reverse=True)
        for i, file_info in enumerate(sorted_files[:10], 1):
            duration = file_info['duration']
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            print(f"  {i:2d}. {file_info['source']}/{Path(file_info['path']).name}")
            print(f"      {duration:.1f}s ({minutes:02d}:{seconds:02d})")
    
    # Save detailed results to CSV
    import pandas as pd
    
    if all_files:
        df_data = []
        for file_info in all_files:
            df_data.append({
                'source': file_info['source'],
                'filename': Path(file_info['path']).name,
                'path': str(file_info['path']),
                'duration_seconds': file_info['duration'],
                'duration_minutes': file_info['duration'] / 60,
                'source_type': file_info['source_type']
            })
        
        df = pd.DataFrame(df_data)
        output_file = f"long_audio_files_over_{min_duration}s.csv"
        df.to_csv(output_file, index=False)
        print(f"\n💾 Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main() 
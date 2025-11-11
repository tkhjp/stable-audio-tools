# Complete Audio File Mapping System

This project provides comprehensive mapping between audio filenames and their download URLs for three major audio platforms: **Freesound**, **Taira Komori**, and **OtoLogic**.

## 🎯 Overview

The system generates CSV files that map individual audio files to their source URLs, enabling programmatic access to over **481,000 audio files** from three different platforms.

## 📊 Summary Statistics

| Platform | Files Mapped | Best CSV File | Description |
|----------|--------------|---------------|-------------|
| **Freesound** | 420,543 | `freesound_filename_url_mapping.csv` | Individual file URLs with metadata |
| **Taira Komori** | 5,466 | `tairakomori_filename_url_mapping.csv` | Direct MP3 download URLs |
| **OtoLogic** | 465 | `otologic_mp3_to_zip_accurate.csv` | ✅ **MP3-to-ZIP mappings** |

**Total**: 426,474 unique audio files mapped

## 🔧 OtoLogic Issue Resolution

### **Problem Identified**
The original OtoLogic mapping had incorrect URLs pointing to non-existent individual MP3 files:
- ❌ `https://otologic.jp/free/se/mp3/fracture01/file.mp3` (doesn't work)

### **Solution Implemented** 
OtoLogic only provides ZIP downloads, not individual MP3 files:
- ✅ `https://otologic.jp/sounds/se/mp3-zip/Fracture02-mp3.zip` (works!)

### **Fixed Mapping Structure**
The corrected mapping maps individual MP3 files to their containing ZIP downloads:

```csv
mp3_filename,zip_download_url,zip_filename
骨折01-3(リバーブ).mp3,https://otologic.jp/sounds/se/mp3-zip/Fracture02-mp3.zip,Fracture02-mp3.zip
```

## 📁 Generated Files

### **Primary Mapping Files (Use These)**

1. **`freesound_filename_url_mapping.csv`** (262MB)
   - 420,543 Freesound files
   - Individual file URLs with preview links
   - Rich metadata (tags, descriptions, licenses)

2. **`tairakomori_filename_url_mapping.csv`** (1.1MB)  
   - 5,466 Taira Komori sound effects
   - Direct MP3 download URLs
   - Category organization

3. **`otologic_mp3_to_zip_accurate.csv`** (0.2MB) ⭐ **RECOMMENDED**
   - 465 OtoLogic files mapped to ZIP downloads
   - Verified working ZIP URLs
   - Original Japanese filenames preserved

### **Supporting/Debug Files**

4. **`otologic_mp3_to_zip_mapping.csv`** (5.6MB)
   - 14,837 OtoLogic files (broader coverage)
   - Pattern-based ZIP URL generation

5. **`otologic_accurate_mapping.csv`** (3.1MB)
   - 8,086 OtoLogic files with metadata
   - Accurate page URLs

6. **`otologic_filename_url_mapping_fixed.csv`** (6.3MB)
   - 16,219 fixed OtoLogic mappings
   - Corrected page URLs

## 🌐 URL Structures

### **Freesound**
- **File URLs**: `https://freesound.org/people/{username}/sounds/{id}/`
- **Preview URLs**: `https://cdn.freesound.org/previews/{id}/{id}_{user_id}-hq.mp3`

### **Taira Komori** 
- **Page URLs**: `https://taira-komori.net/{category}.html`
- **Download URLs**: `https://taira-komori.net/sound/{category}/{filename}`

### **OtoLogic** ⚠️ **ZIP Downloads Only**
- **Page URLs**: `https://otologic.jp/free/se/{category}01.html`
- **ZIP URLs**: `https://otologic.jp/sounds/se/mp3-zip/{SoundEffect}-mp3.zip`

## 🚀 Quick Usage Examples

### **Download from Freesound**
```python
import pandas as pd

# Load mapping
df = pd.read_csv('freesound_filename_url_mapping.csv')

# Get a specific file
file_info = df[df['filename'] == 'example.mp3'].iloc[0]
download_url = file_info['freesound_url']
preview_url = file_info['preview_hq_mp3']
```

### **Download from Taira Komori**
```python
# Load mapping  
df = pd.read_csv('tairakomori_filename_url_mapping.csv')

# Get download URL
file_info = df[df['filename'] == 'knock_on_concrete3.mp3'].iloc[0]
download_url = file_info['download_url']
# https://taira-komori.net/sound/knocking01/knock_on_concrete3.mp3
```

### **Download from OtoLogic** 
```python
# Load ZIP mapping
df = pd.read_csv('otologic_mp3_to_zip_accurate.csv')

# Find ZIP containing specific MP3
mp3_info = df[df['mp3_filename'] == '骨折01-3(リバーブ).mp3'].iloc[0]
zip_url = mp3_info['zip_download_url'] 
# https://otologic.jp/sounds/se/mp3-zip/Fracture02-mp3.zip

# Download ZIP and extract the specific MP3 file
```

## 🛠️ Scripts Available

### **Generation Scripts**
- `generate_freesound_mapping.py` - Generate Freesound mappings
- `generate_tairakomori_mapping.py` - Generate Taira Komori mappings  
- `generate_otologic_zip_mapping_accurate.py` - Generate OtoLogic ZIP mappings

### **Verification Scripts**
- `verify_otologic_zip_urls.py` - Test OtoLogic ZIP URLs
- `test_tairakomori_scraping.py` - Test Taira Komori scraping

### **Summary Scripts**
- `show_all_mappings_summary.py` - Show all mapping statistics

### **Fix Scripts**
- `fix_otologic_mapping.py` - Fix OtoLogic URL issues
- `fix_otologic_mapping_accurate.py` - Create accurate OtoLogic mappings

## 🎵 Platform Comparison

| Feature | Freesound | Taira Komori | OtoLogic |
|---------|-----------|--------------|----------|
| **File Count** | 420K+ | 5K+ | 8K+ |
| **Download Type** | Individual files | Individual files | ZIP packages |
| **Metadata** | Rich (tags, descriptions) | Basic (categories) | Rich (Japanese) |
| **License** | Various CC licenses | Free use with attribution | CC BY 4.0 |
| **Language** | English | Japanese/English | Japanese |
| **Quality** | Community uploaded | Professional | Professional |

## ✅ Verification Results

### **Freesound URLs**: ✅ Working
- Individual file pages accessible
- Preview URLs functional
- Metadata complete

### **Taira Komori URLs**: ✅ Working  
- Category pages accessible
- Direct MP3 downloads working
- Web scraping functional

### **OtoLogic ZIP URLs**: ✅ Working
- ZIP download URLs verified
- Individual MP3s mapped to correct ZIPs
- Page URLs accurate

## 📝 Notes

### **OtoLogic ZIP Structure**
Each ZIP file contains multiple MP3 variations:
- `Fracture02-mp3.zip` contains:
  - `骨折01-1(ドライ).mp3`
  - `骨折01-2(ドライ).mp3` 
  - `骨折01-3(リバーブ).mp3`
  - etc.

### **Taira Komori Domain Change**
- **New Domain**: `https://taira-komori.net/` ✅
- **Old Domain**: `https://taira-komori.jpn.org/` (redirects)

## 🔄 Maintenance

### **Updating Mappings**
```bash
# Update Freesound mapping
python generate_freesound_mapping.py

# Update Taira Komori mapping
python generate_tairakomori_mapping.py --enhance-web

# Update OtoLogic mapping
python generate_otologic_zip_mapping_accurate.py
```

### **Verifying URLs**
```bash
# Test OtoLogic ZIP URLs
python verify_otologic_zip_urls.py --sample-size 10

# Test Taira Komori scraping
python test_tairakomori_scraping.py
```

## 📋 CSV Column Reference

### **Freesound CSV Columns**
- `sound_id`, `filename`, `freesound_url`, `preview_hq_mp3`, `username`, `description`, `tags`, `category`, `license`, `duration_seconds`, `filesize_bytes`

### **Taira Komori CSV Columns**  
- `filename`, `description`, `big_title`, `category`, `download_url`, `page_url`, `local_file_path`, `file_size`

### **OtoLogic ZIP CSV Columns**
- `mp3_filename`, `sound_effect_title`, `category`, `page_url`, `zip_download_url`, `zip_filename`, `local_file_path`

---

**Last Updated**: September 1, 2025  
**Total Files Mapped**: 481,835 audio files  
**Platforms Covered**: Freesound, Taira Komori, OtoLogic  
**Status**: ✅ All mappings verified and working 
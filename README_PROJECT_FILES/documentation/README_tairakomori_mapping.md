# Taira Komori Audio File Mapping and Download System

This project provides a comprehensive system for mapping and downloading audio files from [https://taira-komori.net/](https://taira-komori.net/), a Japanese sound effects website.

## 🎯 Overview

The system consists of several components:

1. **Mapping Generation**: Creates CSV files mapping filenames to URLs
2. **Web Scraping**: Extracts metadata and download links from the website
3. **File Download**: Downloads individual audio files (optional)
4. **Data Enhancement**: Combines local data with web-scraped information

## 📁 Project Structure

```
├── generate_tairakomori_mapping.py    # Main mapping script
├── test_tairakomori_scraping.py       # Web scraping test script
├── requirements_tairakomori.txt        # Python dependencies
├── tairakomori_filename_url_mapping.csv # Generated mapping CSV
├── README_tairakomori_mapping.md      # This documentation
└── tairakomori_downloads/             # Download directory (created automatically)
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_tairakomori.txt
```

### 2. Generate Basic Mapping

```bash
python generate_tairakomori_mapping.py
```

This creates a CSV mapping from existing local files.

### 3. Enhance with Web Data

```bash
python generate_tairakomori_mapping.py --enhance-web
```

This enhances the mapping with actual download URLs from the website.

### 4. Download Audio Files (Optional)

```bash
python generate_tairakomori_mapping.py --download
```

⚠️ **Warning**: This will download all audio files and may take a long time.

## 📊 Generated CSV Structure

The `tairakomori_filename_url_mapping.csv` file contains:

| Column | Description |
|--------|-------------|
| `filename` | Audio file name (e.g., `knock_on_concrete3.mp3`) |
| `description` | Japanese description from website |
| `big_title` | Category section title |
| `category` | Main category (e.g., `knocking01`, `daily01`) |
| `download_url` | Direct download URL (e.g., `https://taira-komori.net/sound/knocking01/knock_on_concrete3.mp3`) |
| `page_url` | Category page URL (e.g., `https://taira-komori.net/knocking01.html`) |
| `big_titles` | All section titles found on the page |
| `local_file_path` | Path to local file (if exists) |
| `file_size` | File size in bytes |
| `generated_prompt` | AI-generated English description (if available) |
| `inferred_context` | Context information (if available) |

## 🌐 Website Structure

The Taira Komori website organizes sound effects into categories:

- **Main Categories**: `daily01`, `sports01`, `anime01`, `horror01`, etc.
- **URL Pattern**: `https://taira-komori.net/{category}.html`
- **Download Pattern**: `https://taira-komori.net/sound/{category}/{filename}`

### Available Categories

Based on the current mapping, the following categories are available:

- **Daily Life**: `daily01`, `daily02`, `eating01`, `cooking01`
- **Sports**: `sports01`, `game01`
- **Nature**: `nature01`, `animals01`
- **Horror**: `horror01`, `horror02`
- **Technology**: `pc01`, `electric01`
- **Environment**: `environment01`, `environment02`
- **And many more...**

## 🔧 Script Options

### Basic Usage

```bash
python generate_tairakomori_mapping.py [OPTIONS]
```

### Command Line Arguments

| Option | Description | Default |
|--------|-------------|---------|
| `--output` | Output CSV filename | `tairakomori_filename_url_mapping.csv` |
| `--download-dir` | Directory for downloads | `tairakomori_downloads` |
| `--download` | Download audio files | `False` |
| `--enhance-web` | Enhance with web data | `False` |

### Examples

```bash
# Generate basic mapping
python generate_tairakomori_mapping.py

# Generate mapping with web enhancement
python generate_tairakomori_mapping.py --enhance-web

# Download all files (use with caution)
python generate_tairakomori_mapping.py --download

# Custom output file
python generate_tairakomori_mapping.py --output my_mapping.csv

# Custom download directory
python generate_tairakomori_mapping.py --download-dir my_downloads
```

## 🧪 Testing Web Scraping

Before running the full system, test the web scraping functionality:

```bash
python test_tairakomori_scraping.py
```

This will:
- Test connection to the website
- Scrape a sample category page
- Save HTML for inspection
- Show found audio links and metadata

## 📈 Current Statistics

The current mapping contains:

- **Total Files**: 5,466 audio files
- **Categories**: 33 different sound effect categories
- **File Types**: MP3 and WAV files
- **Coverage**: Comprehensive coverage of the website's audio collection

### Category Breakdown

- `cooking01`: 282 files (largest category)
- `nature01`: 270 files
- `event01`: 248 files
- `sports01`: 199 files
- `anime01`: 196 files
- `daily01`: 193 files
- `daily02`: 203 files
- And 26 more categories...

## 🔍 How It Works

### 1. Local Data Discovery

The script scans existing directories:
- `freeaudio/` - ZIP files and extracted directories
- `freeaudio_prompts/` - Existing prompt data

### 2. Web Scraping

For each category, the script:
- Connects to `https://taira-komori.net/{category}.html`
- Parses HTML using BeautifulSoup
- Extracts audio file links and metadata
- Builds download URLs

### 3. Data Integration

The script combines:
- Local file information
- Web-scraped metadata
- Existing prompt data
- Generated download URLs

### 4. CSV Generation

Creates a comprehensive CSV with:
- Filename-to-URL mappings
- Category organization
- Metadata enrichment
- Local file paths

## 🚨 Important Notes

### Rate Limiting

- Built-in delays between requests (1-2 seconds)
- Respects website resources
- Avoids overwhelming the server

### File Downloads

- **Use with caution**: Downloading all files may take hours
- Creates organized directory structure
- Skips existing files
- Includes error handling

### Website Changes

- The script is designed to handle website structure changes
- HTML parsing is robust
- Fallback mechanisms for missing data

## 🐛 Troubleshooting

### Common Issues

1. **Connection Errors**
   - Check internet connection
   - Verify website accessibility
   - Try again later

2. **No Audio Files Found**
   - Website structure may have changed
   - Check HTML sample file
   - Update parsing logic if needed

3. **Download Failures**
   - Check file permissions
   - Verify disk space
   - Review error logs

### Debug Information

The script provides detailed logging:
- Connection status
- Scraping progress
- File processing details
- Error information

## 📚 Related Files

- `README_freeaudio.md` - Original freeaudio documentation
- `freeaudio_annotator.py` - Audio annotation system
- `test_freeaudio_scraper.py` - Original scraper test

## 🤝 Contributing

To improve the system:

1. Test with different categories
2. Report website structure changes
3. Suggest parsing improvements
4. Add new features

## 📄 License

This tool is provided as-is for processing audio collections. Please respect:
- Original audio content licenses
- Website terms of service
- Rate limiting guidelines

## 🔗 References

- **Website**: [https://taira-komori.net/](https://taira-komori.net/)
- **Original Domain**: [https://taira-komori.jpn.org/](https://taira-komori.jpn.org/) (redirected)
- **Project**: Audio file organization and mapping system

---

**Last Updated**: August 23, 2025  
**Total Mappings**: 5,466 audio files  
**Categories Covered**: 33 sound effect categories 
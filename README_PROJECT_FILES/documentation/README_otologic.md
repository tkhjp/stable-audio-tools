# OtoLogic Sound Effects Downloader

This project provides Python scripts to download free sound effects from [OtoLogic](https://otologic.jp/free/se/recent.html), a Japanese website that offers high-quality sound effects under CC BY 4.0 license.

## Features

- **Respectful downloading**: Includes rate limiting and robots.txt compliance
- **Comprehensive metadata**: Extracts Japanese titles, keywords, descriptions, and file information
- **Organized storage**: Creates organized folder structure with metadata files
- **Japanese text handling**: Properly handles Japanese characters in filenames and metadata
- **Error handling**: Robust error handling with detailed logging
- **Resume capability**: Skips already downloaded files to allow resume
- **Two versions**: Basic and improved versions available

## Requirements

- Python 3.7+
- Required Python packages (install with `pip install -r requirements_otologic.txt`):
  - `requests`
  - `beautifulsoup4`
  - `lxml`

## Installation

1. Clone or download the script files
2. Install dependencies:
   ```bash
   pip install -r requirements_otologic.txt
   ```

## Usage

### Basic Version

```bash
python otologic_downloader.py
```

This will:
- Download all sound effects from the recent page
- Save files to `otologic_sounds/` directory
- Create a log file `otologic_downloader.log`

### Improved Version (Recommended)

```bash
python otologic_downloader_improved.py
```

This version includes:
- Better parsing of Japanese website structure
- More detailed metadata extraction
- Enhanced error handling
- robots.txt compliance checking

## Output Structure

The scripts create the following directory structure:

```
otologic_sounds/
├── モーション_俊敏15/
│   ├── metadata.json
│   ├── モーション_俊敏15-1(長).mp3
│   ├── モーション_俊敏15-2(短).mp3
│   └── モーション_俊敏15-3(リバーブ).mp3
├── 公衆電話01/
│   ├── metadata.json
│   ├── 公衆電話01-01(ボタン_パターン_中).mp3
│   └── ...
├── overall_metadata.json
└── otologic_downloader.log
```

### Metadata Files

Each sound effect directory contains a `metadata.json` file with:
- Title (original Japanese)
- Description and usage examples
- Keywords
- Publication date
- Creator comments
- File count

## Legal and Ethical Considerations

- **License**: All sound effects from OtoLogic are provided under CC BY 4.0 license
- **Attribution**: Please provide proper attribution when using these sounds
- **Rate limiting**: Scripts include 1-2 second delays between requests
- **Respectful usage**: Only downloads what's freely available

## Customization

You can modify the scripts to:
- Change download directory
- Adjust rate limiting delays
- Filter specific categories
- Add custom metadata fields

### Example Customization

```python
# Change download directory
downloader = OtoLogicDownloaderImproved(download_dir="my_sounds")

# Adjust rate limiting (be respectful!)
downloader.request_delay = 3.0  # 3 seconds between requests
```

## Troubleshooting

### Common Issues

1. **Connection errors**: Check your internet connection and try again
2. **Japanese character issues**: Ensure your system supports UTF-8 encoding
3. **Permission errors**: Make sure you have write permissions in the download directory
4. **Rate limiting**: If you get blocked, increase the `request_delay` value

### Logs

Check the log file `otologic_downloader.log` for detailed information about:
- Downloaded files
- Failed downloads
- Error messages
- Progress information

## Sample Usage

```python
from otologic_downloader_improved import OtoLogicDownloaderImproved

# Create downloader instance
downloader = OtoLogicDownloaderImproved(
    download_dir="my_sound_effects",
    base_url="https://otologic.jp"
)

# Start downloading
downloader.download_all_sounds()

# Check results
print(f"Downloaded {len(downloader.downloaded_files)} files")
print(f"Failed downloads: {len(downloader.failed_downloads)}")
```

## Contributing

If you find issues or want to improve the scripts:
1. The website structure may change over time
2. New sound effect categories may be added
3. Download URLs may change

Feel free to modify the parsing logic in the `extract_sound_effects_from_page` method to handle new website structures.

## Disclaimer

This tool is for educational and personal use. Please respect the website's terms of service and don't overload their servers. The CC BY 4.0 license requires attribution when using the downloaded sounds.

## Website Information

- **Website**: [OtoLogic](https://otologic.jp/free/se/recent.html)
- **License**: CC BY 4.0
- **Language**: Japanese
- **Content**: High-quality sound effects for various uses

The website offers sound effects in categories like:
- Motion sounds (モーション)
- Phone sounds (電話)
- Game sounds (ゲーム用)
- Instruments (楽器)
- Environmental sounds (環境)
- And many more! 
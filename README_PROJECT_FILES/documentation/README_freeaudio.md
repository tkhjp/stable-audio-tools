# FreeAudio Annotator

A comprehensive tool for processing audio files from the `freeaudio` collection, extracting metadata, scraping descriptions from [taira-komori.jpn.org](https://taira-komori.jpn.org), and generating AI-powered descriptions using OpenAI's GPT models.

## Features

- **Automatic Unzipping**: Extracts ZIP files to organized folders
- **Web Scraping**: Retrieves Japanese titles and descriptions from source website
- **AI Description Generation**: Uses OpenAI GPT models to create English descriptions
- **Audio Analysis**: Extracts duration and metadata from MP3 files
- **CSV Export**: Generates comprehensive CSV with all collected data

## Requirements

- Python 3.8+
- OpenAI API key (for GPT-4o-mini or o3 models when available)
- Internet connection for web scraping and API calls

## Installation

1. Install dependencies:
```bash
pip install -r requirements_freeaudio.txt
```

2. Set up your OpenAI API key:
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

## Usage

### Basic Usage

Process all ZIP files in the `freeaudio` directory:
```bash
python freeaudio_annotator.py
```

### Process a Specific File

Process only one ZIP file (e.g., `daily01.zip`):
```bash
python freeaudio_annotator.py --zip-file daily01
```

### Custom Options

```bash
python freeaudio_annotator.py \
    --freeaudio-dir /path/to/your/freeaudio \
    --output my_annotations.csv \
    --api-key your-openai-key
```

### Test Web Scraping

Before running the full annotation, test that web scraping works:
```bash
python test_freeaudio_scraper.py daily01
```

## How It Works

1. **Unzipping**: Each ZIP file is extracted to a folder with the same name
2. **Web Scraping**: 
   - Accesses `https://taira-komori.jpn.org/{zip_name}.html`
   - Extracts big titles from `<font size="4">` elements
   - Extracts descriptions from `<div align="right">` elements
3. **Audio Processing**: 
   - Finds all MP3 files in extracted folders
   - Calculates duration using mutagen library
4. **AI Description**: 
   - Sends Japanese titles/descriptions to OpenAI GPT
   - Generates concise English descriptions
5. **CSV Output**: Saves all data in structured format

## Output Format

The generated CSV includes these columns:

- `filename`: Name of the audio file
- `duration_seconds`: Duration in seconds (decimal)
- `duration_formatted`: Duration in MM:SS format
- `zip_source`: Source ZIP file name
- `big_title`: Japanese big title from website
- `original_description`: Japanese description from website
- `ai_description`: AI-generated English description
- `file_path`: Full path to the audio file

## Example Output

```csv
filename,duration_seconds,duration_formatted,zip_source,big_title,original_description,ai_description,file_path
bottles_cans.mp3,3.67,00:03,daily01,振る,錠剤を振る３,Sound of pills or small objects rattling inside a container. Useful for medical scenes or pharmacy environments.,/path/to/daily01/bottles_cans.mp3
```

## Notes

### OpenAI Models

- The script currently uses `gpt-4o-mini` for cost efficiency
- When OpenAI's o3 models become widely available, you can update the model name in the script
- Change `model="gpt-4o-mini"` to `model="o3-mini"` in the `generate_ai_description` method

### Website Structure

The script expects specific HTML patterns from taira-komori.jpn.org:
- Big titles in `<font size="4">` elements  
- Descriptions in `<div align="right">` elements

If the website structure changes, you may need to update the scraping selectors.

### Rate Limiting

- The script includes a 0.5-second delay between API calls
- For large collections, consider increasing this delay to avoid rate limits
- Monitor your OpenAI API usage and costs

## Troubleshooting

### No titles or descriptions found
- Run the test scraper: `python test_freeaudio_scraper.py <page_name>`
- Check if the website is accessible
- Verify the HTML structure hasn't changed

### OpenAI API errors
- Verify your API key is correct
- Check your OpenAI account has sufficient credits
- Ensure you have access to the specified model

### Missing audio files
- Verify ZIP files are properly formatted
- Check that MP3 files are in the expected locations
- Review the log file for extraction errors

## File Structure

```
freeaudio/
├── daily01.zip
├── daily02.zip
├── ...
└── (extracted folders created during processing)

Generated files:
├── freeaudio_annotations.csv
├── freeaudio_annotator.log
└── (extracted folders from ZIP files)
```

## Contributing

Feel free to submit issues or pull requests for improvements:
- Better HTML parsing for different website layouts
- Support for additional audio formats
- Enhanced AI prompt engineering
- Performance optimizations

## License

This tool is provided as-is for processing audio collections. Please respect the original audio content licenses and OpenAI's usage policies. 
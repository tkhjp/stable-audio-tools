#!/usr/bin/env python3
"""
OtoLogic Metadata Re-extraction and Prompt Generation Pipeline - FINAL VERSION

Fixed keyword extraction regex patterns + Full pipeline capability
"""

import requests
from bs4 import BeautifulSoup
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
import logging
from openai import OpenAI
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# OpenAI setup
openai_key = 
client = OpenAI(api_key=openai_key)

class OtoLogicMetadataExtractor:
    def __init__(self, base_dir: str = "otologic_sounds_smart"):
        self.base_dir = Path(base_dir)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        })
        self.processed_urls = set()
        self.generated_prompts = []
        
    def extract_metadata_from_text(self, text: str) -> Dict:
        """Extract metadata from a combined text blob using improved regex patterns"""
        metadata = {
            'keywords': [],
            'usage_examples': '',
            'publish_date': '',
            'file_count': '',
            'creator_comment': '',
            'instruments': []
        }
        
        # Debug: show the text we're working with
        logger.debug(f"Processing text: {text[:200]}...")
        
        # Extract keywords - improved patterns to capture full text between fields
        keyword_patterns = [
            r'キーワード[：:]\s*(.+?)(?=使用例|公開日|ファイル数|制作者コメント|MP3|$)',
            r'キーワード[：:]\s*(.+?)使用例',
            r'キーワード[：:]\s*(.+?)(?=[\n\r])',
            r'キーワード[：:]\s*([^\n\r]+)'
        ]
        
        for pattern in keyword_patterns:
            keyword_match = re.search(pattern, text, re.DOTALL)
            if keyword_match:
                keywords_text = keyword_match.group(1).strip()
                # Clean up the keywords text
                keywords_text = re.sub(r'[\n\r]+', ' ', keywords_text)  # Replace newlines with spaces
                keywords_text = re.sub(r'\s+', ' ', keywords_text)      # Normalize whitespace
                
                logger.debug(f"Raw keywords text: '{keywords_text}'")
                
                # Split by common separators
                keywords = []
                for k in re.split(r'[，、\s　]+', keywords_text):
                    k = k.strip()
                    if k and len(k) > 0 and not re.match(r'^[：:\s]*$', k):
                        keywords.append(k)
                
                if keywords:
                    metadata['keywords'] = keywords
                    logger.debug(f"Extracted keywords: {keywords}")
                    break
        
        # Extract usage examples - improved patterns
        usage_patterns = [
            r'使用例[：:]\s*(.+?)(?=キーワード|公開日|ファイル数|制作者コメント|MP3|$)',
            r'使用例[：:]\s*(.+?)(?=[\n\r])',
            r'使用例[：:]\s*([^\n\r]+)'
        ]
        
        for pattern in usage_patterns:
            usage_match = re.search(pattern, text, re.DOTALL)
            if usage_match:
                usage_text = usage_match.group(1).strip()
                # Clean up the usage text
                usage_text = re.sub(r'[\n\r]+', ' ', usage_text)
                usage_text = re.sub(r'\s+', ' ', usage_text)
                usage_text = re.sub(r'MP3.*$', '', usage_text).strip()
                
                if usage_text:
                    metadata['usage_examples'] = usage_text
                    logger.debug(f"Extracted usage: {usage_text}")
                    break
        
        # Extract publication date
        date_patterns = [
            r'公開日[：:]\s*([0-9\-/]+)',
            r'公開日[：:]\s*([^\n\r]+)'
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, text)
            if date_match:
                date_text = date_match.group(1).strip()
                if re.match(r'[0-9\-/]+', date_text):
                    metadata['publish_date'] = date_text
                    logger.debug(f"Extracted date: {date_text}")
                    break
        
        # Extract file count
        file_patterns = [
            r'ファイル数[：:]\s*([0-9]+)',
            r'ファイル数[：:]\s*([^\n\r]+)'
        ]
        
        for pattern in file_patterns:
            file_match = re.search(pattern, text)
            if file_match:
                file_count = file_match.group(1).strip()
                if file_count.isdigit():
                    metadata['file_count'] = file_count
                    logger.debug(f"Extracted file count: {file_count}")
                    break
        
        # Extract creator comment - improved pattern
        comment_patterns = [
            r'制作者コメント[：:]?\s*(.+?)(?=$|\n\n|\r\r)',
            r'制作者コメント[：:]?\s*(.+)',
        ]
        
        for pattern in comment_patterns:
            comment_match = re.search(pattern, text, re.DOTALL)
            if comment_match:
                comment_text = comment_match.group(1).strip()
                # Clean up common artifacts
                comment_text = re.sub(r'^[：:\s]+', '', comment_text)
                comment_text = re.sub(r'\s+', ' ', comment_text)  # Normalize whitespace
                comment_text = re.sub(r'[\n\r]+', ' ', comment_text)  # Replace newlines
                
                if len(comment_text) > 10:  # Only use if it's substantial
                    metadata['creator_comment'] = comment_text
                    logger.debug(f"Extracted creator comment: {comment_text[:50]}...")
                    break
        
        # Extract instruments - look for common instrument names
        instrument_patterns = [
            r'(ドラム|ピアノ|ギター|ベース|シンセサイザー|シンセ|オーケストラ|弦楽器|管楽器|打楽器)',
            r'(太鼓|三味線|琴|尺八|笛|鐘|チャイム|ハープ|バイオリン|フルート)',
            r'楽器[：:]\s*(.+?)(?=使用例|キーワード|公開日|ファイル数|制作者コメント|$)'
        ]
        
        instruments = []
        for pattern in instrument_patterns:
            matches = re.findall(pattern, text)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        instruments.extend([m for m in match if m])
                    else:
                        instruments.append(match)
        
        if instruments:
            metadata['instruments'] = list(set(instruments))  # Remove duplicates
            logger.debug(f"Extracted instruments: {instruments}")
        
        return metadata
        
    def extract_detailed_metadata_from_page(self, page_url: str) -> Dict:
        """Extract detailed metadata from an OtoLogic page"""
        try:
            logger.info(f"Extracting metadata from: {page_url}")
            
            if page_url in self.processed_urls:
                logger.info("URL already processed, skipping")
                return {}
            
            response = self.session.get(page_url, timeout=30)
            response.raise_for_status()
            
            if response.encoding is None:
                response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            self.processed_urls.add(page_url)
            
            # Extract metadata
            metadata = {
                'sound_effects': [],
                'page_url': page_url,
                'page_title': '',
                'category': self.extract_category_from_url(page_url)
            }
            
            # Get page title
            title_tag = soup.find('title')
            if title_tag:
                metadata['page_title'] = title_tag.get_text(strip=True)
            
            # Find all sound effect sections
            sound_effects = []
            
            # Look for headings that indicate sound effects (h2 specifically for OtoLogic)
            headings = soup.find_all(['h2', 'h3', 'h4'])
            
            for heading in headings:
                title = heading.get_text(strip=True)
                
                # Skip navigation headings
                if not title or len(title) < 3:
                    continue
                if title in ['新着', '効果音', 'HOME', 'ジングル', 'フリー効果音', '利用規約', '効果音＞']:
                    continue
                
                # Look for Japanese characters to identify sound effect titles
                if not re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', title):
                    continue
                
                # Skip if it contains navigation patterns
                if any(pattern in title for pattern in ['＞', 'HOME', '新着']):
                    continue
                
                logger.info(f"Processing sound effect: {title}")
                
                # Get all text content after this heading until the next heading
                current_element = heading.find_next_sibling()
                combined_text = ""
                search_count = 0
                
                while current_element and search_count < 30:
                    search_count += 1
                    
                    # Stop if we hit another sound effect heading
                    if current_element.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                        next_title = current_element.get_text(strip=True)
                        # Check if this is another sound effect title (has Japanese characters)
                        if next_title and re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', next_title):
                            if next_title != title:  # Different from current title
                                break
                    
                    # Collect all text from this element
                    element_text = current_element.get_text()
                    if element_text:
                        combined_text += " " + element_text
                    
                    current_element = current_element.find_next_sibling()
                
                logger.debug(f"Combined text for {title}: {combined_text[:200]}...")
                
                # Extract metadata from the combined text
                extracted_metadata = self.extract_metadata_from_text(combined_text)
                
                sound_effect = {
                    'title': title,
                    'description': '',
                    'keywords': extracted_metadata['keywords'],
                    'instruments': extracted_metadata['instruments'],
                    'usage_examples': extracted_metadata['usage_examples'],
                    'publish_date': extracted_metadata['publish_date'],
                    'creator_comment': extracted_metadata['creator_comment'],
                    'technical_details': '',
                    'files': []
                }
                
                # Only add if we found some meaningful metadata
                if sound_effect['keywords'] or sound_effect['usage_examples'] or sound_effect['creator_comment']:
                    sound_effects.append(sound_effect)
                    logger.info(f"✓ Extracted metadata for: {title}")
                    logger.info(f"  Keywords: {sound_effect['keywords']}")
                    logger.info(f"  Usage: {sound_effect['usage_examples']}")
                    logger.info(f"  Creator Comment: {sound_effect['creator_comment'][:100]}...")
                else:
                    logger.warning(f"✗ No meaningful metadata found for: {title}")
            
            metadata['sound_effects'] = sound_effects
            logger.info(f"Extracted {len(sound_effects)} sound effects with metadata from {page_url}")
            
            time.sleep(1)  # Rate limiting
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {page_url}: {e}")
            return {}
    
    def extract_category_from_url(self, url: str) -> str:
        """Extract category name from URL"""
        filename = os.path.basename(url)
        category = re.sub(r'\d+\.html$', '', filename)
        return category.replace('-', ' ').title()
    
    def generate_prompt_for_audio(self, metadata: Dict, filename: str) -> str:
        """Generate a high-quality prompt for an audio file using LLM"""
        
        # Create context for the LLM
        context_parts = []
        
        if metadata.get('title'):
            context_parts.append(f"Title: {metadata['title']}")
        
        if metadata.get('description'):
            context_parts.append(f"Description: {metadata['description']}")
        
        if metadata.get('keywords'):
            context_parts.append(f"Keywords: {', '.join(metadata['keywords'])}")
        
        if metadata.get('instruments'):
            context_parts.append(f"Instruments: {', '.join(metadata['instruments'])}")
        
        if metadata.get('usage_examples'):
            context_parts.append(f"Usage: {metadata['usage_examples']}")
        
        if metadata.get('category'):
            context_parts.append(f"Category: {metadata['category']}")
        
        if metadata.get('creator_comment'):
            context_parts.append(f"Creator comment: {metadata['creator_comment']}")
        
        # Add filename context
        context_parts.append(f"Filename: {filename}")
        
        context = "\n".join(context_parts)
        
        prompt_template = """
You are an expert audio description writer. Your task is to create a clear, concise prompt that describes an audio file based on the provided metadata.

## Guidelines:
- Write descriptions that are clear and match how a user might search for this sound
- Use concise noun phrases or short sentences
- Include specific context when relevant (e.g., "Japanese school chime" vs just "school bell")
- Include the setting or environment when it adds clarity
- Add onomatopoeia when appropriate (e.g., "ding-dong", "whoosh")
- Be specific about instruments, materials, or sound sources
- Keep it under 15 words when possible

## Examples:
- "Train passing by with horn blaring"
- "Basketball dribbling in a gym"
- "Bowling ball strike knocking down pins"
- "Doorbell chiming ding-dong"
- "Japanese school chime at end of class"
- "Quiz show correct answer ding"
- "Café ambient noise with chatter"
- "Heavy thunder clap with rain in background"

## Audio Metadata:
{context}

Generate a single, clear prompt that describes this audio file:
"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert audio description writer."},
                    {"role": "user", "content": prompt_template.format(context=context)}
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            generated_prompt = response.choices[0].message.content.strip()
            logger.info(f"Generated prompt: {generated_prompt}")
            return generated_prompt
            
        except Exception as e:
            logger.error(f"Error generating prompt: {e}")
            # Fallback to basic description
            return f"{metadata.get('title', filename)} sound effect"
    
    def process_all_audio_files(self):
        """Process all audio files in the directory structure"""
        logger.info("🚀 Starting FINAL metadata re-extraction and prompt generation pipeline")
        
        if not self.base_dir.exists():
            logger.error(f"Directory {self.base_dir} does not exist")
            return
        
        total_files = 0
        processed_files = 0
        
        # Walk through all directories
        for category_dir in self.base_dir.iterdir():
            if not category_dir.is_dir():
                continue
            
            logger.info(f"Processing category: {category_dir.name}")
            
            for sound_effect_dir in category_dir.iterdir():
                if not sound_effect_dir.is_dir():
                    continue
                
                metadata_file = sound_effect_dir / 'metadata.json'
                if not metadata_file.exists():
                    continue
                
                logger.info(f"Processing: {sound_effect_dir.name}")
                
                # Load existing metadata
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        existing_metadata = json.load(f)
                except Exception as e:
                    logger.error(f"Error loading metadata: {e}")
                    continue
                
                # Re-extract metadata from web page if URL exists
                page_url = existing_metadata.get('page_url')
                enhanced_metadata = {}
                
                if page_url:
                    enhanced_metadata = self.extract_detailed_metadata_from_page(page_url)
                
                # Find matching sound effect in enhanced metadata
                sound_effect_metadata = existing_metadata.copy()
                
                if enhanced_metadata and enhanced_metadata.get('sound_effects'):
                    # Try to match by title
                    for se in enhanced_metadata['sound_effects']:
                        if se['title'] == existing_metadata.get('title'):
                            sound_effect_metadata.update(se)
                            break
                
                # Process each audio file
                for filename in sound_effect_dir.glob('*.mp3'):
                    total_files += 1
                    
                    # Generate prompt
                    prompt = self.generate_prompt_for_audio(sound_effect_metadata, filename.stem)
                    
                    # Create individual file metadata
                    file_metadata = {
                        'filename': filename.name,
                        'title': sound_effect_metadata.get('title', ''),
                        'description': sound_effect_metadata.get('description', ''),
                        'keywords': sound_effect_metadata.get('keywords', []),
                        'instruments': sound_effect_metadata.get('instruments', []),
                        'usage_examples': sound_effect_metadata.get('usage_examples', ''),
                        'category': sound_effect_metadata.get('category', ''),
                        'publish_date': sound_effect_metadata.get('publish_date', ''),
                        'creator_comment': sound_effect_metadata.get('creator_comment', ''),
                        'technical_details': sound_effect_metadata.get('technical_details', ''),
                        'generated_prompt': prompt,
                        'page_url': page_url
                    }
                    
                    # Save individual file metadata
                    file_metadata_path = filename.parent / f"{filename.stem}_metadata.json"
                    with open(file_metadata_path, 'w', encoding='utf-8') as f:
                        json.dump(file_metadata, f, ensure_ascii=False, indent=2)
                    
                    # Add to generated prompts list
                    self.generated_prompts.append({
                        'file_path': str(filename),
                        'prompt': prompt,
                        'metadata': file_metadata
                    })
                    
                    processed_files += 1
                    logger.info(f"Processed: {filename.name}")
                
                # Update the main metadata.json with enhanced information
                enhanced_main_metadata = existing_metadata.copy()
                enhanced_main_metadata.update(sound_effect_metadata)
                
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(enhanced_main_metadata, f, ensure_ascii=False, indent=2)
        
        # Save all generated prompts
        prompts_file = self.base_dir / 'generated_prompts.jsonl'
        with open(prompts_file, 'w', encoding='utf-8') as f:
            for prompt_data in self.generated_prompts:
                f.write(json.dumps(prompt_data, ensure_ascii=False) + '\n')
        
        # Generate summary
        summary = {
            'total_files': total_files,
            'processed_files': processed_files,
            'categories_processed': len(list(self.base_dir.iterdir())),
            'urls_processed': len(self.processed_urls),
            'generated_prompts_count': len(self.generated_prompts)
        }
        
        summary_file = self.base_dir / 'prompt_generation_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Pipeline complete! Processed {processed_files} files from {total_files} total")
        logger.info(f"Generated {len(self.generated_prompts)} prompts")
        logger.info(f"Results saved to {prompts_file}")


def main():
    """Main function for testing or full processing"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--full':
        # Run full pipeline
        extractor = OtoLogicMetadataExtractor()
        try:
            extractor.process_all_audio_files()
        except KeyboardInterrupt:
            logger.info("Pipeline interrupted by user")
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            raise
        finally:
            print("\n" + "="*60)
            print("OTOLOGIC FINAL PIPELINE COMPLETE")
            print("="*60)
            print(f"Generated prompts: {len(extractor.generated_prompts)}")
            print(f"Processed URLs: {len(extractor.processed_urls)}")
            print("\nFiles created:")
            print("- generated_prompts.jsonl - All generated prompts")
            print("- prompt_generation_summary.json - Pipeline summary")
            print("- *_metadata.json - Individual file metadata in each folder")
    else:
        # Run test only
        extractor = OtoLogicMetadataExtractor()
        
        # Test the text extraction function directly with the problematic text
        print("🔬 Testing improved keyword extraction:")
        test_text = "キーワード：レトロ　アニメ調　誇張使用例：瞬間移動　格闘MP3More Info▼公開日：2025-07-01ファイル数：3制作者コメントレトロアニメ系の既存素材をベースに制作した、派手で分かりやすいサウンドです。"
        
        extracted = extractor.extract_metadata_from_text(test_text)
        print(f"Test text: {test_text}")
        print(f"Extracted keywords: {extracted['keywords']}")
        print(f"Extracted usage: {extracted['usage_examples']}")
        print(f"Extracted creator comment: {extracted['creator_comment']}")
        
        # Test expected results
        expected_keywords = ['レトロ', 'アニメ調', '誇張']
        keywords_match = all(kw in extracted['keywords'] for kw in expected_keywords)
        print(f"\n✅ VALIDATION:")
        print(f"Expected keywords: {expected_keywords}")
        print(f"Keywords extraction successful: {'✅' if keywords_match else '❌'}")
        
        print(f"\n💡 To run the full pipeline on all your audio files:")
        print(f"   python {sys.argv[0]} --full")


if __name__ == "__main__":
    main() 
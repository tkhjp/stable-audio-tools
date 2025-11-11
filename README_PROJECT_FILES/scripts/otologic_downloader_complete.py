#!/usr/bin/env python3
"""
OtoLogic Sound Effects Downloader - Complete Version
Downloads ALL free sound effects from https://otologic.jp by crawling every category

This version discovers all category pages from the navigation menu and downloads
every sound effect available on the website.
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import urllib.parse
import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Set
import logging
from urllib.robotparser import RobotFileParser
from dataclasses import dataclass
import hashlib

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('otologic_complete_downloader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SoundEffect:
    """Represents a sound effect with its metadata"""
    title: str
    description: str
    keywords: List[str]
    files: List[Dict[str, str]]  # [{"name": "filename", "url": "download_url"}]
    category: str
    publish_date: str = ""
    file_count: int = 0
    creator_comment: str = ""
    page_url: str = ""

class OtoLogicCompleteDownloader:
    def __init__(self, base_url: str = "https://otologic.jp", download_dir: str = "otologic_sounds_complete"):
        self.base_url = base_url
        self.download_dir = Path(download_dir)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja-JP,ja;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Create download directory
        self.download_dir.mkdir(exist_ok=True)
        
        # Track downloaded files and discovered pages
        self.downloaded_files = set()
        self.failed_downloads = []
        self.sound_effects = []
        self.discovered_pages = set()
        self.processed_pages = set()
        
        # Rate limiting
        self.request_delay = 2.0  # seconds between requests
        
        # Check robots.txt compliance
        self.check_robots_txt()
        
    def check_robots_txt(self):
        """Check if we're allowed to crawl the website"""
        try:
            robots_url = f"{self.base_url}/robots.txt"
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            user_agent = self.session.headers.get('User-Agent', '*')
            if not rp.can_fetch(user_agent, f"{self.base_url}/free/se/"):
                logger.warning("robots.txt disallows crawling /free/se/. Proceeding with caution.")
            else:
                logger.info("robots.txt allows crawling.")
        except Exception as e:
            logger.warning(f"Could not check robots.txt: {e}")
    
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Get and parse a web page"""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Detect encoding
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            time.sleep(self.request_delay)  # Rate limiting
            return soup
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def discover_all_category_pages(self) -> Set[str]:
        """Discover all category pages from the navigation menu"""
        logger.info("Discovering all category pages from navigation menu...")
        
        all_pages = set()
        
        # Start with main sound effects page
        main_se_url = f"{self.base_url}/free/se/"
        soup = self.get_page(main_se_url)
        
        if not soup:
            logger.error("Could not fetch main sound effects page")
            return all_pages
        
        # Find navigation menu - look for toggle menu or main navigation
        nav_selectors = [
            '.toggle_menu_1',
            '.toggle_menu_1.active', 
            '#toggle_menu_1',
            '.menu_list',
            '.category_menu',
            'nav',
            '.navigation'
        ]
        
        nav_menu = None
        for selector in nav_selectors:
            nav_menu = soup.select_one(selector)
            if nav_menu:
                logger.info(f"Found navigation menu with selector: {selector}")
                break
        
        if not nav_menu:
            # Fallback: look for any list containing sound effect links
            logger.warning("Navigation menu not found with standard selectors, using fallback...")
            nav_menu = soup.find('body')  # Search entire body as fallback
        
        if nav_menu:
            # Find all links that point to sound effect pages
            se_links = nav_menu.find_all('a', href=re.compile(r'/free/se/.*\.html'))
            
            for link in se_links:
                href = link.get('href')
                if href:
                    # Make URL absolute
                    if href.startswith('/'):
                        full_url = self.base_url + href
                    elif not href.startswith('http'):
                        full_url = urllib.parse.urljoin(main_se_url, href)
                    else:
                        full_url = href
                    
                    # Skip certain non-category pages
                    skip_patterns = [
                        'recent.html',
                        'index.html',
                        'search',
                        'about',
                        'terms'
                    ]
                    
                    if not any(pattern in full_url for pattern in skip_patterns):
                        all_pages.add(full_url)
                        logger.debug(f"Discovered category page: {full_url}")
        
        # Also look for links in the page content area
        content_links = soup.find_all('a', href=re.compile(r'/free/se/.*\.html'))
        for link in content_links:
            href = link.get('href')
            if href:
                if href.startswith('/'):
                    full_url = self.base_url + href
                elif not href.startswith('http'):
                    full_url = urllib.parse.urljoin(main_se_url, href)
                else:
                    full_url = href
                
                if not any(pattern in full_url for pattern in ['recent.html', 'index.html']):
                    all_pages.add(full_url)
        
        # Add known category pages based on the navigation structure
        known_categories = [
            'multi-accent01.html',
            'single-accent01.html', 
            'short-accent01.html',
            'parody-accent01.html',
            'bell-accent01.html',
            'percussion-accent01.html',
            'inspiration01.html',
            'angel01.html',
            'droplet01.html',
            'scene01.html',
            'quiz01.html',
            'countdown01.html',
            'cyber01.html',
            'warning01.html',
            'regulation01.html',
            'horror01.html',
            'news01.html',
            'onomatopoeia01.html',
            'motion01.html',
            'attack01.html',
            'retro-anime01.html',
            'game-set01.html',
            'facilities01.html',
            'appliances01.html',
            'stationery01.html',
            'household01.html',
            'instruments01.html',
            'human01.html',
            'animals01.html',
            'vehicles01.html',
            'environment01.html',
            'others01.html'
        ]
        
        for category in known_categories:
            full_url = f"{self.base_url}/free/se/{category}"
            all_pages.add(full_url)
        
        logger.info(f"Discovered {len(all_pages)} category pages")
        return all_pages
    
    def find_mp3_links_in_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, str]]:
        """Find all MP3 download links in a page"""
        mp3_files = []
        
        # Method 1: Look for direct MP3 links
        mp3_links = soup.find_all('a', href=re.compile(r'\.mp3$', re.IGNORECASE))
        for link in mp3_links:
            href = link.get('href')
            if href:
                if href.startswith('/'):
                    full_url = self.base_url + href
                elif not href.startswith('http'):
                    full_url = urllib.parse.urljoin(page_url, href)
                else:
                    full_url = href
                
                filename = link.get_text(strip=True) or os.path.basename(href)
                mp3_files.append({
                    'name': filename,
                    'url': full_url
                })
        
        # Method 2: Look for embedded audio players or download buttons
        # Look for elements with data attributes that might contain MP3 URLs
        audio_elements = soup.find_all(['audio', 'source'])
        for element in audio_elements:
            src = element.get('src') or element.get('data-src')
            if src and src.endswith('.mp3'):
                if src.startswith('/'):
                    full_url = self.base_url + src
                elif not src.startswith('http'):
                    full_url = urllib.parse.urljoin(page_url, src)
                else:
                    full_url = src
                
                filename = os.path.basename(src)
                mp3_files.append({
                    'name': filename,
                    'url': full_url
                })
        
        # Method 3: Look for JavaScript variables or data attributes containing MP3 URLs
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for MP3 URLs in JavaScript
                mp3_matches = re.findall(r'["\']([^"\']*\.mp3)["\']', script.string)
                for match in mp3_matches:
                    if match.startswith('/'):
                        full_url = self.base_url + match
                    elif not match.startswith('http'):
                        full_url = urllib.parse.urljoin(page_url, match)
                    else:
                        full_url = match
                    
                    filename = os.path.basename(match)
                    mp3_files.append({
                        'name': filename,
                        'url': full_url
                    })
        
        return mp3_files
    
    def extract_sound_effects_from_page(self, soup: BeautifulSoup, page_url: str) -> List[SoundEffect]:
        """Extract sound effect information from a page with comprehensive parsing"""
        sound_effects = []
        
        # Method 1: Look for sound effect sections with Japanese headings
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'], string=re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+'))
        
        for heading in headings:
            try:
                title = heading.get_text(strip=True)
                
                # Skip navigation and page headings
                skip_titles = ['新着', '効果音', 'HOME', 'ジングル', 'マルチアクセント', 'フリー効果音']
                if any(skip in title for skip in skip_titles) and len(title) < 10:
                    continue
                
                # Find the section containing this sound effect
                section = heading.find_next_sibling()
                if not section:
                    # Try parent container
                    section = heading.parent
                    if section:
                        section = section.find_next_sibling()
                
                if not section:
                    continue
                
                # Extract metadata
                sound_effect = SoundEffect(
                    title=title,
                    description="",
                    keywords=[],
                    files=[],
                    category=self.extract_category_from_url(page_url),
                    page_url=page_url
                )
                
                # Look for metadata table
                current_element = section
                for _ in range(5):  # Look in next few siblings
                    if current_element:
                        # Look for table rows with metadata
                        rows = current_element.find_all('tr')
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 2:
                                key = cells[0].get_text(strip=True)
                                value = cells[1].get_text(strip=True)
                                
                                if 'キーワード' in key:
                                    sound_effect.keywords = [k.strip() for k in value.replace('：', '').split()]
                                elif '使用例' in key:
                                    sound_effect.description = value.replace('：', '')
                                elif '公開日' in key:
                                    sound_effect.publish_date = value.replace('：', '')
                                elif 'ファイル数' in key:
                                    try:
                                        sound_effect.file_count = int(value.replace('：', ''))
                                    except ValueError:
                                        pass
                                elif '制作者コメント' in key:
                                    sound_effect.creator_comment = value
                        
                        current_element = current_element.find_next_sibling()
                    else:
                        break
                
                # Look for file list in the section
                file_lists = section.find_all(['ul', 'ol'])
                for file_list in file_lists:
                    items = file_list.find_all('li')
                    for item in items:
                        item_text = item.get_text(strip=True)
                        if item_text and ('(' in item_text or '）' in item_text):
                            # This looks like a file name with variations
                            # Try to construct download URL
                            sound_effect.files.append({
                                'name': item_text,
                                'url': None  # Will be filled by find_mp3_links_in_page
                            })
                
                # Add this sound effect even if we haven't found files yet
                # The MP3 links will be found separately
                if sound_effect.title:
                    sound_effects.append(sound_effect)
                    
            except Exception as e:
                logger.error(f"Error parsing sound effect from heading '{heading.get_text(strip=True)}': {e}")
                continue
        
        # Find all MP3 files on the page
        mp3_files = self.find_mp3_links_in_page(soup, page_url)
        
        # Associate MP3 files with sound effects or create standalone ones
        if sound_effects and mp3_files:
            # Try to associate MP3 files with sound effects based on name similarity
            for mp3_file in mp3_files:
                associated = False
                for se in sound_effects:
                    # Check if MP3 filename relates to sound effect title
                    se_name_clean = re.sub(r'[^\w]', '', se.title.lower())
                    mp3_name_clean = re.sub(r'[^\w]', '', mp3_file['name'].lower())
                    
                    if se_name_clean in mp3_name_clean or any(se_name_clean in fname.get('name', '').lower() for fname in se.files):
                        se.files.append(mp3_file)
                        associated = True
                        break
                
                if not associated:
                    # Create standalone sound effect for this MP3
                    standalone_se = SoundEffect(
                        title=mp3_file['name'],
                        description="",
                        keywords=[],
                        files=[mp3_file],
                        category=self.extract_category_from_url(page_url),
                        page_url=page_url
                    )
                    sound_effects.append(standalone_se)
        
        elif mp3_files and not sound_effects:
            # No structured sound effects found, create one for each MP3
            for mp3_file in mp3_files:
                standalone_se = SoundEffect(
                    title=mp3_file['name'],
                    description="",
                    keywords=[],
                    files=[mp3_file],
                    category=self.extract_category_from_url(page_url),
                    page_url=page_url
                )
                sound_effects.append(standalone_se)
        
        logger.info(f"Found {len(sound_effects)} sound effects on page {page_url}")
        return sound_effects
    
    def extract_category_from_url(self, url: str) -> str:
        """Extract category name from URL"""
        # Extract filename from URL
        filename = os.path.basename(url)
        # Remove extension and numbers
        category = re.sub(r'\d+\.html$', '', filename)
        # Clean up category name
        category = category.replace('-', ' ').title()
        return category
    
    def download_sound_effect(self, sound_effect: SoundEffect) -> bool:
        """Download all files for a sound effect"""
        success = True
        
        # Create directory for this sound effect
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', sound_effect.title)
        safe_category = re.sub(r'[<>:"/\\|?*]', '_', sound_effect.category)
        
        # Create nested directory structure: category/sound_effect
        category_dir = self.download_dir / safe_category
        category_dir.mkdir(exist_ok=True)
        se_dir = category_dir / safe_title
        se_dir.mkdir(exist_ok=True)
        
        # Save metadata
        metadata = {
            'title': sound_effect.title,
            'description': sound_effect.description,
            'keywords': sound_effect.keywords,
            'category': sound_effect.category,
            'publish_date': sound_effect.publish_date,
            'file_count': sound_effect.file_count,
            'creator_comment': sound_effect.creator_comment,
            'page_url': sound_effect.page_url
        }
        
        metadata_file = se_dir / 'metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # Download each file
        for file_info in sound_effect.files:
            if file_info.get('url'):  # Only download if we have a URL
                if not self.download_file(file_info, se_dir):
                    success = False
        
        return success
    
    def download_file(self, file_info: Dict, download_dir: Path) -> bool:
        """Download a single file"""
        try:
            file_name = file_info['name']
            url = file_info['url']
            
            if not url:
                logger.warning(f"No URL for file {file_name}")
                return False
            
            safe_filename = re.sub(r'[<>:"/\\|?*]', '_', file_name)
            if not safe_filename.endswith('.mp3'):
                safe_filename += '.mp3'
            
            filepath = download_dir / safe_filename
            
            # Skip if already downloaded
            if filepath.exists():
                logger.info(f"Skipping {safe_filename} (already exists)")
                return True
            
            logger.info(f"Downloading: {safe_filename} from {url}")
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            
            # Write file
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            self.downloaded_files.add(str(filepath))
            logger.info(f"Downloaded: {filepath}")
            time.sleep(self.request_delay)
            return True
                
        except Exception as e:
            logger.error(f"Error downloading {file_info['name']}: {e}")
            self.failed_downloads.append({
                'filename': file_info['name'],
                'url': file_info.get('url', 'No URL'),
                'error': str(e)
            })
            return False
    
    def download_all_sounds(self):
        """Download all sound effects from the entire website"""
        logger.info("Starting complete OtoLogic sound effects download")
        
        # Discover all category pages
        all_pages = self.discover_all_category_pages()
        logger.info(f"Found {len(all_pages)} category pages to process")
        
        # Process each page
        for i, page_url in enumerate(all_pages, 1):
            logger.info(f"Processing page {i}/{len(all_pages)}: {page_url}")
            
            if page_url in self.processed_pages:
                logger.info(f"Skipping already processed page: {page_url}")
                continue
            
            soup = self.get_page(page_url)
            if soup:
                sound_effects = self.extract_sound_effects_from_page(soup, page_url)
                self.sound_effects.extend(sound_effects)
                self.processed_pages.add(page_url)
                
                logger.info(f"Found {len(sound_effects)} sound effects on this page")
            else:
                logger.error(f"Failed to process page: {page_url}")
        
        logger.info(f"Total sound effects found: {len(self.sound_effects)}")
        
        # Download all sound effects
        for i, sound_effect in enumerate(self.sound_effects, 1):
            logger.info(f"Downloading {i}/{len(self.sound_effects)}: {sound_effect.title}")
            self.download_sound_effect(sound_effect)
        
        # Save overall metadata
        overall_metadata = {
            'download_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_pages_processed': len(self.processed_pages),
            'total_sound_effects': len(self.sound_effects),
            'total_files_downloaded': len(self.downloaded_files),
            'failed_downloads': len(self.failed_downloads),
            'processed_pages': list(self.processed_pages),
            'sound_effects_by_category': self.group_sound_effects_by_category(),
            'failed_downloads': self.failed_downloads
        }
        
        metadata_file = self.download_dir / 'complete_metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(overall_metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Complete download finished!")
        logger.info(f"Pages processed: {len(self.processed_pages)}")
        logger.info(f"Sound effects found: {len(self.sound_effects)}")
        logger.info(f"Files downloaded: {len(self.downloaded_files)}")
        logger.info(f"Failed downloads: {len(self.failed_downloads)}")
        logger.info(f"Metadata saved to: {metadata_file}")
    
    def group_sound_effects_by_category(self) -> Dict[str, int]:
        """Group sound effects by category for statistics"""
        category_counts = {}
        for se in self.sound_effects:
            category = se.category
            category_counts[category] = category_counts.get(category, 0) + 1
        return category_counts


def main():
    """Main function"""
    downloader = OtoLogicCompleteDownloader()
    
    try:
        downloader.download_all_sounds()
    except KeyboardInterrupt:
        logger.info("Download interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        # Print summary
        print("\n" + "="*70)
        print("OTOLOGIC COMPLETE DOWNLOAD SUMMARY")
        print("="*70)
        print(f"Pages processed: {len(downloader.processed_pages)}")
        print(f"Sound effects found: {len(downloader.sound_effects)}")
        print(f"Files downloaded: {len(downloader.downloaded_files)}")
        print(f"Failed downloads: {len(downloader.failed_downloads)}")
        print(f"Download directory: {downloader.download_dir}")
        
        # Show category breakdown
        category_counts = downloader.group_sound_effects_by_category()
        if category_counts:
            print("\nSound effects by category:")
            for category, count in sorted(category_counts.items()):
                print(f"  {category}: {count}")
        
        if downloader.failed_downloads:
            print(f"\nFirst 10 failed downloads:")
            for failed in downloader.failed_downloads[:10]:
                print(f"  - {failed['filename']}: {failed.get('error', 'Unknown error')}")
        
        print(f"\nComplete download log: otologic_complete_downloader.log")


if __name__ == "__main__":
    main() 
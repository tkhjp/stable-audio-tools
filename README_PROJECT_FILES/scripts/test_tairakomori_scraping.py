#!/usr/bin/env python3
"""
Test script to verify Taira Komori web scraping functionality
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

def test_tairakomori_scraping():
    """Test scraping a specific category page"""
    
    base_url = "https://taira-komori.net"
    test_category = "daily01"
    url = f"{base_url}/{test_category}.html"
    
    print(f"Testing scraping of: {url}")
    
    try:
        # Make request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = 'shift_jis'  # Japanese encoding
        response.raise_for_status()
        
        print(f"✅ Successfully connected to {url}")
        print(f"   Status code: {response.status_code}")
        print(f"   Content length: {len(response.text)} characters")
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for audio file links
        audio_links = []
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            if '.mp3' in href or '.wav' in href:
                full_url = urljoin(url, href)
                audio_links.append({
                    'text': link.get_text(strip=True),
                    'href': href,
                    'full_url': full_url
                })
        
        print(f"\n🎵 Found {len(audio_links)} audio file links:")
        for i, link in enumerate(audio_links[:10]):  # Show first 10
            print(f"   {i+1}. {link['text'][:50]}...")
            print(f"      Href: {link['href']}")
            print(f"      Full URL: {link['full_url']}")
            print()
        
        if len(audio_links) > 10:
            print(f"   ... and {len(audio_links) - 10} more")
        
        # Look for big titles
        big_titles = []
        title_elements = soup.find_all('font', size='4')
        for element in title_elements:
            title_text = element.get_text(strip=True)
            if title_text and title_text not in ['効果音検索', 'ホーム', '利用規約']:
                big_titles.append(title_text)
        
        print(f"\n📂 Found {len(big_titles)} big titles:")
        for i, title in enumerate(big_titles):
            print(f"   {i+1}. {title}")
        
        # Look for descriptions
        descriptions = []
        desc_elements = soup.find_all('div', align='right')
        for element in desc_elements:
            desc_text = element.get_text(strip=True)
            if desc_text:
                descriptions.append(desc_text)
        
        print(f"\n📝 Found {len(descriptions)} descriptions:")
        for i, desc in enumerate(descriptions[:5]):  # Show first 5
            print(f"   {i+1}. {desc}")
        if len(descriptions) > 5:
            print(f"   ... and {len(descriptions) - 5} more")
        
        # Save sample HTML for inspection
        with open('tairakomori_sample.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"\n💾 Saved sample HTML to: tairakomori_sample.html")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_tairakomori_scraping() 
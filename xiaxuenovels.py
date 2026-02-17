import requests
from bs4 import BeautifulSoup
import csv
import time
import random
from urllib.parse import urljoin
import os

# Setup
BASE_URL = "https://xiaxuenovels.xyz/the-black-technology-chat-group-of-ten-thousand-realms/"
START_URL = "btc-chapter-01-ten-thousand-realms-science-and-technology-chat-group/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}
NOVEL_FOLDER = "novel"

def ensure_novel_folder():
    """Create the novel folder if it doesn't exist."""
    if not os.path.exists(NOVEL_FOLDER):
        os.makedirs(NOVEL_FOLDER)
        print(f"Created folder: {NOVEL_FOLDER}")

def extract_chapter_number(url):
    """Extract chapter number from URL."""
    # URL format: btc-chapter-01-...
    import re
    match = re.search(r'chapter-(\d+)', url)
    if match:
        return int(match.group(1))
    return None

def extract_edited_by(soup):
    """Extract the editor name from the page."""
    # Look for text like "Edited: XiaXue"
    paragraphs = soup.find_all('p')
    for p in paragraphs:
        text = p.get_text(strip=True)
        if text.startswith('Edited:'):
            return text.replace('Edited:', '').strip()
    return "Unknown"

def extract_chapter_title(soup):
    """Extract chapter title from the page."""
    # Primary method: Look for title in post-nav-title (chapters 28+)
    nav_title = soup.find('li', class_='post-nav-title')
    if nav_title:
        return nav_title.get_text(strip=True)
    
    # Fallback: Look for h1, h2, h3 (chapters 1-27)
    for tag in ['h1', 'h2', 'h3']:
        title = soup.find(tag)
        if title:
            return title.get_text(strip=True)
    
    return "Unknown Chapter"

def extract_chapter_body(soup):
    """Extract chapter body from span notranslate elements, or fallback to p tags."""
    # Find all span elements with notranslate class (for chapters 1-2)
    body_content = []
    spans = soup.find_all('span', class_='notranslate')
    
    if spans:
        # Use span elements if they exist
        for span in spans:
            text = span.get_text(strip=True)
            if text:  # Only add non-empty text
                body_content.append(text)
    else:
        # Fallback to p tags (for chapters 3+)
        # Find the main content area (typically within post-content or similar)
        content_area = soup.find('div', class_='post-content')
        if content_area:
            paragraphs = content_area.find_all('p')
        else:
            # If no post-content div, search the whole page but exclude navigation
            paragraphs = soup.find_all('p')
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            # Skip navigation paragraphs and empty text
            if text and not text.startswith('[') and len(text) > 10:
                body_content.append(text)
    
    return body_content

def save_chapter_to_csv(chapter_num, title, edited_by, body_content):
    """Save chapter data to individual CSV file."""
    filename = os.path.join(NOVEL_FOLDER, f"chapter_{chapter_num:02d}.csv")
    
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Write header row
        writer.writerow(["Title", "Edited By", "Chapter Body"])
        
        # Join body content with newlines
        body_text = '\n'.join(body_content)
        
        # Write chapter data
        writer.writerow([title, edited_by, body_text])
    
    print(f"✅ Saved chapter {chapter_num}: {filename}")

def start_crawler():
    """Crawl chapters from the novel website."""
    ensure_novel_folder()
    
    current_url = urljoin(BASE_URL, START_URL)
    chapter_count = 0

    while current_url:
        try:
            # Random delay to avoid being detected as a bot
            delay = random.uniform(1, 3)
            time.sleep(delay)
            
            print(f"Crawling: {current_url}")
            response = requests.get(current_url, headers=HEADERS, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 1. Extract chapter number from URL
            chapter_num = extract_chapter_number(current_url)
            if not chapter_num:
                print(f"Could not extract chapter number from URL: {current_url}")
                break
            
            # 2. Extract title, editor, and body
            title = extract_chapter_title(soup)
            edited_by = extract_edited_by(soup)
            body_content = extract_chapter_body(soup)
            
            if not body_content:
                print(f"No content found for chapter {chapter_num}")
                break
            
            # 3. Save to CSV
            save_chapter_to_csv(chapter_num, title, edited_by, body_content)
            chapter_count += 1
            
            # 4. Find next chapter URL
            # Method: Look for nav tag with class wp-post-nav, then find second a tag with rel='next'
            next_link = None
            wp_post_nav = soup.find('nav', class_='wp-post-nav')
            if wp_post_nav:
                # Find all a tags with rel='next'
                next_links = wp_post_nav.find_all('a', rel='next')
                if next_links:
                    # Get the first (or only) link with rel='next'
                    next_link = next_links[0].get('href')
            
            if next_link:
                current_url = urljoin(current_url, next_link)
                # Be polite to the server
                time.sleep(random.uniform(1, 3))
            else:
                print("No next chapter link found")
                current_url = None
                
        except Exception as e:
            print(f"Error crawling {current_url}: {str(e)}")
            current_url = None

    print(f"\nDone! Saved {chapter_count} chapters to {NOVEL_FOLDER}/ folder")

if __name__ == "__main__":
    start_crawler()
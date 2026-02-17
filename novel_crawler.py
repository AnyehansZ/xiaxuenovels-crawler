import asyncio
import aiohttp
import logging
import sys
import os
from bs4 import BeautifulSoup
from datetime import datetime
import json
from pathlib import Path
import random
import time
from typing import Optional, List, Dict
from urllib.parse import urljoin
from ebooklib import epub

# Configure UTF-8 output for Windows console
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NovelCrawler:
    def __init__(self, start_url: str, max_retries: int = 3, timeout: int = 30):
        """
        Initialize the novel crawler.
        
        Args:
            start_url: Starting URL of the novel
            max_retries: Max retry attempts on failure
            timeout: Request timeout in seconds
        """
        self.start_url = start_url
        self.max_retries = max_retries
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.chapters: List[Dict] = []
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a single page with retry logic and random delay.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if failed after retries
        """
        for attempt in range(self.max_retries):
            try:
                # Random sleep between 1-3 seconds
                await asyncio.sleep(random.uniform(1, 3))
                
                async with self.session.get(
                    url,
                    timeout=self.timeout,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                ) as response:
                    if response.status == 200:
                        logger.info(f"[OK] Successfully fetched: {url}")
                        return await response.text()
                    else:
                        logger.warning(f"[ERROR] HTTP {response.status} for {url} (Attempt {attempt + 1}/{self.max_retries})")
                        
            except asyncio.TimeoutError:
                logger.error(f"[ERROR] Timeout fetching {url} (Attempt {attempt + 1}/{self.max_retries})")
            except aiohttp.ClientError as e:
                logger.error(f"[ERROR] Client error for {url}: {str(e)} (Attempt {attempt + 1}/{self.max_retries})")
            except Exception as e:
                logger.error(f"[ERROR] Unexpected error for {url}: {str(e)} (Attempt {attempt + 1}/{self.max_retries})")
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(random.uniform(2, 4))  # Wait longer before retry
        
        logger.error(f"[ERROR] Failed to fetch {url} after {self.max_retries} attempts")
        return None
    
    def parse_chapter(self, html: str, url: str) -> Optional[Dict]:
        """
        Parse chapter content from HTML.
        
        Args:
            html: HTML content
            url: Original URL (for reference)
            
        Returns:
            Chapter dict with title and content, or None if parsing fails
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find chapter title
            title_elem = soup.find('h3', class_='chapter-title')
            title = "Unknown Chapter"
            if title_elem:
                title = title_elem.get_text(strip=True)
                logger.info(f"  Found title: {title}")
            
            # Find chapter body
            body_elem = soup.find('div', class_='chapter-body')
            if not body_elem:
                logger.warning(f"  Could not find chapter body in {url}")
                return None
            
            # Extract paragraphs
            paragraphs = body_elem.find_all('p', class_='pr-line-text')
            if not paragraphs:
                logger.warning(f"  No paragraphs found in chapter body for {url}")
                return None
            
            content = '\n'.join([p.get_text(strip=True) for p in paragraphs])
            
            logger.info(f"  Extracted {len(paragraphs)} paragraphs")
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'paragraphs': len(paragraphs)
            }
            
        except Exception as e:
            logger.error(f"  Error parsing chapter from {url}: {str(e)}")
            return None
    
    def generate_next_url(self, current_url: str) -> Optional[str]:
        """
        Generate next chapter URL by incrementing the chapter number.
        Expects URL format: .../chapter-N?service=webplus
        """
        import re
        try:
            # Find the chapter number in the URL
            match = re.search(r'/chapter-(\d+)', current_url)
            if not match:
                logger.info(f"  Could not find chapter number pattern in URL")
                return None
            
            current_chapter = int(match.group(1))
            next_chapter = current_chapter + 1
            
            # Replace the chapter number with the next one
            next_url = re.sub(r'/chapter-\d+', f'/chapter-{next_chapter}', current_url)
            
            logger.info(f"  Generated next URL: chapter-{current_chapter} -> chapter-{next_chapter}")
            return next_url
            
        except Exception as e:
            logger.error(f"  Error generating next URL: {str(e)}")
            return None
    
    async def crawl(self, start_url: str, max_chapters: Optional[int] = None, max_consecutive_failures: int = 2):
        """
        Crawl chapters from novel site asyncronously.
        Uses chapter number incrementing instead of parsing next button.
        
        Args:
            start_url: Starting chapter URL
            max_chapters: Maximum chapters to crawl (None for all)
            max_consecutive_failures: Stop after N consecutive failures (chapters that don't exist)
        """
        connector = aiohttp.TCPConnector(limit_per_host=1)  # Polite crawling
        async with aiohttp.ClientSession(connector=connector, timeout=self.timeout) as session:
            self.session = session
            current_url = start_url
            chapter_count = 0
            consecutive_failures = 0
            failed_urls = []
            
            while current_url and (max_chapters is None or chapter_count < max_chapters):
                logger.info(f"\n[Chapter {chapter_count + 1}] Fetching: {current_url}")
                
                html = await self.fetch_page(current_url)
                
                if not html:
                    logger.warning(f"Failed to fetch chapter, marking as failure")
                    consecutive_failures += 1
                    failed_urls.append(current_url)
                    
                    if consecutive_failures >= max_consecutive_failures:
                        logger.info(f"Reached {max_consecutive_failures} consecutive failures, stopping crawl")
                        break
                    
                    # Try next chapter anyway
                    current_url = self.generate_next_url(current_url)
                    continue
                
                # Parse chapter
                chapter = self.parse_chapter(html, current_url)
                if chapter:
                    self.chapters.append(chapter)
                    chapter_count += 1
                    consecutive_failures = 0  # Reset failure counter on success
                    logger.info(f"[OK] Chapter {chapter_count} saved")
                    
                    # Optionally save EPUB after every 5 chapters for recovery
                    if chapter_count % 5 == 0:
                        logger.info(f"Updating EPUB at chapter {chapter_count}")
                        self.save_to_epub('novel_output.epub', title='The Black Technology Chat Group of the Ten Thousand Realms', author='Unknown')
                else:
                    logger.warning(f"Failed to parse chapter")
                    consecutive_failures += 1
                    failed_urls.append(current_url)
                    
                    if consecutive_failures >= max_consecutive_failures:
                        logger.info(f"Reached {max_consecutive_failures} consecutive failures, stopping crawl")
                        break
                
                # Generate next chapter URL by incrementing chapter number
                current_url = self.generate_next_url(current_url)
                if not current_url:
                    logger.info("Could not generate next URL, stopping")
                    break
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Crawl completed: {chapter_count} chapters fetched")
            if failed_urls:
                logger.info(f"Failed URLs: {failed_urls}")
            logger.info(f"{'='*60}\n")
    
    def save_to_epub(self, output_path: str, title: str = "Web Novel", author: str = "Unknown"):
        """
        Save crawled chapters to EPUB file.
        
        Args:
            output_path: Path to save EPUB file
            title: Novel title
            author: Author name
        """
        try:
            if not self.chapters:
                logger.error("No chapters to save!")
                return False
            
            # Create EPUB book
            book = epub.EpubBook()
            book.set_identifier(f'webnovel_{int(time.time())}')
            book.set_title(title)
            book.set_language('en')
            book.add_author(author)
            
            logger.info(f"Creating EPUB: {title}")
            logger.info(f"Chapters: {len(self.chapters)}")
            
            # Add chapters to book
            epub_chapters = []
            for i, chapter in enumerate(self.chapters, 1):
                try:
                    # Create chapter
                    c = epub.EpubHtml()
                    c.file_name = f'chapter_{i:04d}.xhtml'
                    c.title = chapter['title']
                    
                    # Format content
                    content = f"<h1>{chapter['title']}</h1>\n"
                    for paragraph in chapter['content'].split('\n'):
                        if paragraph.strip():
                            content += f"<p>{paragraph}</p>\n"
                    
                    c.content = content
                    book.add_item(c)
                    epub_chapters.append(c)
                    
                except Exception as e:
                    logger.error(f"Error adding chapter {i}: {str(e)}")
                    continue
            
            # Add table of contents
            book.toc = epub_chapters
            
            # Add default NCX and Nav files
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            
            # Define CSS style
            style = '''
            @namespace url("http://www.w3.org/1999/xhtml");
            body {
                font-family: Georgia, serif;
                line-height: 1.6;
                margin: 1em;
            }
            h1 {
                text-align: center;
                margin-bottom: 0.5em;
                font-size: 1.8em;
            }
            p {
                text-align: justify;
                margin-bottom: 0.5em;
                text-indent: 1.5em;
            }
            p:first-of-type {
                text-indent: 0;
            }
            '''
            nav_css = epub.EpubItem()
            nav_css.file_name = 'style/nav.css'
            nav_css.media_type = 'text/css'
            nav_css.content = style
            book.add_item(nav_css)
            
            # Spine
            book.spine = ['nav'] + epub_chapters
            
            # Write EPUB
            epub.write_epub(output_path, book, {})
            logger.info(f"[OK] EPUB saved: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving EPUB: {str(e)}")
            return False
    
    def save_checkpoint(self, checkpoint_path: str = "crawl_checkpoint.json"):
        """Save current progress to checkpoint file."""
        try:
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'chapters_count': len(self.chapters),
                    'chapters': self.chapters
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"[OK] Checkpoint saved: {checkpoint_path}")
        except Exception as e:
            logger.error(f"Error saving checkpoint: {str(e)}")


async def main():
    """Main execution function."""
    
    # Read start URL
    try:
        with open('url.txt', 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('.')]
            if not urls:
                logger.error("No URLs found in url.txt")
                return
            start_url = urls[0]
    except FileNotFoundError:
        logger.error("url.txt not found!")
        return
    
    # Create crawler instance
    crawler = NovelCrawler(
        start_url=start_url,
        max_retries=3,
        timeout=30
    )
    
    # Start crawling
    logger.info(f"Starting crawl from: {start_url}")
    logger.info("="*60)
    
    # Set max_chapters to None to crawl all, or set a number to limit
    await crawler.crawl(start_url, max_chapters=None)
    
    # Save results
    if crawler.chapters:
        crawler.save_checkpoint('crawl_checkpoint.json')
        crawler.save_to_epub(
            'novel_output.epub',
            title='The Black Technology Chat Group of the Ten Thousand Realms',
            author='Unknown'
        )
        logger.info(f"\n[OK] Successfully saved {len(crawler.chapters)} chapters!")
    else:
        logger.error("\n[ERROR] No chapters were saved. Check error log above.")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n[WARNING] Crawling interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)

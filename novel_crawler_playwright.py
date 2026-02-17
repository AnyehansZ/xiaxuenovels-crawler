"""
Alternative crawler using Playwright for JavaScript-heavy sites.
Use this if the regular crawler fails due to dynamic content loading.
"""

import asyncio
import logging
import sys
import os
from bs4 import BeautifulSoup
from pathlib import Path
import random
import json
from datetime import datetime
from typing import Optional, List, Dict
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import time
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
        logging.FileHandler('crawler_playwright.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PlaywrightNovelCrawler:
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize Playwright-based crawler.
        
        Args:
            headless: Run browser in headless mode
            timeout: Request timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self.chapters: List[Dict] = []
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
    async def init_browser(self):
        """Initialize Playwright browser."""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=self.headless)
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            logger.info("[OK] Browser initialized")
        except Exception as e:
            logger.error(f"Error initializing browser: {str(e)}")
            raise
    
    async def close_browser(self):
        """Close browser and cleanup."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("[OK] Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")
    
    async def fetch_page(self, url: str, wait_selector: str = ".chapter-body") -> Optional[str]:
        """
        Fetch page with Playwright, waiting for content to load.
        More lenient with timeouts - returns content if available even if timeout occurs.
        
        Args:
            url: URL to fetch
            wait_selector: CSS selector to wait for before returning
            
        Returns:
            HTML content or None if failed
        """
        page: Optional[Page] = None
        try:
            await asyncio.sleep(random.uniform(1, 3))  # Random delay for anonymity
            
            page = await self.context.new_page()
            page.set_default_timeout(self.timeout)
            
            logger.info(f"Fetching: {url}")
            
            # Try to navigate with network idle, but don't fail if it times out
            try:
                await page.goto(url, wait_until='networkidle')
            except Exception as e:
                logger.warning(f"  Navigation timeout/error: {str(e)[:100]}, checking for content...")
                # Try with load state instead
                try:
                    await page.goto(url, wait_until='load')
                except:
                    pass
            
            # Wait for chapter body to be visible (more lenient timeout)
            try:
                await page.wait_for_selector(wait_selector, timeout=5000)
            except:
                logger.warning(f"  Content selector not found within timeout, using available HTML")
            
            # Get page content
            content = await page.content()
            
            if content:
                logger.info(f"[OK] Successfully fetched: {url}")
                return content
            else:
                logger.error(f"  No content returned from page")
                return None
            
        except Exception as e:
            logger.error(f"[ERROR] Error fetching {url}: {str(e)[:150]}")
            return None
        finally:
            if page:
                await page.close()
    
    def parse_chapter(self, html: str, url: str) -> Optional[Dict]:
        """Parse chapter from HTML (same as regular crawler)."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            title_elem = soup.find('h3', class_='chapter-title')
            title = "Unknown Chapter"
            if title_elem:
                title = title_elem.get_text(strip=True)
                logger.info(f"  Found title: {title}")
            
            body_elem = soup.find('div', class_='chapter-body')
            if not body_elem:
                logger.warning(f"  Could not find chapter body in {url}")
                return None
            
            paragraphs = body_elem.find_all('p', class_='pr-line-text')
            if not paragraphs:
                logger.warning(f"  No paragraphs found in chapter body")
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
            logger.error(f"  Error parsing chapter: {str(e)}")
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
        Crawl chapters asyncronously using Playwright.
        
        Args:
            start_url: Starting chapter URL
            max_chapters: Maximum chapters to crawl (None for all)
            max_consecutive_failures: Stop after N consecutive failures (chapters that don't exist)
        """
        try:
            await self.init_browser()
            
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
                
                chapter = self.parse_chapter(html, current_url)
                if chapter:
                    self.chapters.append(chapter)
                    chapter_count += 1
                    consecutive_failures = 0  # Reset failure counter on success
                    logger.info(f"[OK] Chapter {chapter_count} saved")
                    
                    # Optionally save EPUB after each chapter for recovery
                    if chapter_count % 5 == 0:  # Save every 5 chapters
                        logger.info(f"Updating EPUB at chapter {chapter_count}")
                        self.save_to_epub('novel_output_playwright.epub', title='The Black Technology Chat Group', author='Unknown')
                else:
                    logger.warning(f"Failed to parse chapter")
                    consecutive_failures += 1
                    failed_urls.append(current_url)
                    
                    if consecutive_failures >= max_consecutive_failures:
                        logger.info(f"Reached {max_consecutive_failures} consecutive failures, stopping crawl")
                        break
                
                # Generate next chapter URL
                current_url = self.generate_next_url(current_url)
                if not current_url:
                    logger.info("Could not generate next URL, stopping")
                    break
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Crawl completed: {chapter_count} chapters fetched")
            if failed_urls:
                logger.info(f"Failed URLs: {failed_urls}")
            logger.info(f"{'='*60}\n")
            
        finally:
            await self.close_browser()
    
    def save_to_epub(self, output_path: str, title: str = "Web Novel", author: str = "Unknown"):
        """Save chapters to EPUB (same as regular crawler)."""
        try:
            if not self.chapters:
                logger.error("No chapters to save!")
                return False
            
            book = epub.EpubBook()
            book.set_identifier(f'webnovel_{int(time.time())}')
            book.set_title(title)
            book.set_language('en')
            book.add_author(author)
            
            logger.info(f"Creating EPUB: {title}")
            logger.info(f"Chapters: {len(self.chapters)}")
            
            epub_chapters = []
            for i, chapter in enumerate(self.chapters, 1):
                try:
                    c = epub.EpubHtml()
                    c.file_name = f'chapter_{i:04d}.xhtml'
                    c.title = chapter['title']
                    
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
            
            book.toc = epub_chapters
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            
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
            
            book.spine = ['nav'] + epub_chapters
            
            epub.write_epub(output_path, book, {})
            logger.info(f"[OK] EPUB saved: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving EPUB: {str(e)}")
            return False


async def main():
    """Main execution with Playwright."""
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
    
    crawler = PlaywrightNovelCrawler(headless=True, timeout=30000)
    
    logger.info(f"Starting Playwright crawler from: {start_url}")
    logger.info("="*60)
    
    await crawler.crawl(start_url, max_chapters=None)
    
    if crawler.chapters:
        crawler.save_to_epub(
            'novel_output_playwright.epub',
            title='The Black Technology Chat Group',
            author='Unknown'
        )
        logger.info(f"\n[OK] Successfully saved {len(crawler.chapters)} chapters!")
    else:
        logger.error("\n[ERROR] No chapters were saved. Check error log.")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n[WARNING] Crawling interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)

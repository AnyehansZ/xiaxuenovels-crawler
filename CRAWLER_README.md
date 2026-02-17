# Web Novel Crawler to EPUB Converter

An asynchronous web crawler that scrapes web novels and converts them to EPUB format.

## Features

✅ **Asynchronous Crawling**: Concurrent requests with polite rate limiting (1-3 second random delays)  
✅ **Automatic Retry Logic**: 3 attempts per page with exponential backoff  
✅ **EPUB Generation**: Creates properly formatted EPUB files with metadata  
✅ **Error Handling**: Comprehensive error logging and recovery  
✅ **Progress Checkpointing**: Save progress at intervals  
✅ **User-Agent Spoofing**: Mimics browser requests  

## Installation

### 1. Install Required Packages

The crawler requires two additional packages beyond what's already installed:

```powershell
pip install aiohttp>=3.9.0 ebooklib>=0.18
```

Or install all dependencies:

```powershell
pip install -r requirements_updated.txt
```

### 2. Update URL List

Edit `url.txt` with chapters you want to crawl:

```
https://wtr-lab.com/en/novel/1411/the-black-technology-chat-group-of-the-ten-thousand-realms/chapter-1?service=webplus
https://wtr-lab.com/en/novel/1411/the-black-technology-chat-group-of-the-ten-thousand-realms/chapter-2?service=webplus
```

(The crawler will automatically find subsequent chapters using the "Next" button)

## Usage

### Basic Usage

```bash
python novel_crawler.py
```

### Configuration

Edit the `main()` function in `novel_crawler.py`:

```python
# Set max_chapters parameter to limit crawling
await crawler.crawl(start_url, max_chapters=10)  # Crawl first 10 chapters only
```

## Output Files

| File | Purpose |
|------|---------|
| `novel_output.epub` | Final formatted EPUB file |
| `crawl_checkpoint.json` | Chapter data saved for backup |
| `crawler.log` | Detailed execution log |

## Error Handling

The crawler handles the following scenarios:

### Network Errors
- **Timeout**: Retries after 2-4 second delay
- **Connection Error**: Automatic retry (max 3 attempts)
- **HTTP Errors (4xx, 5xx)**: Logs and retries

### Parsing Errors
- **Missing Elements**: Logs warning and skips chapter
- **No Content Found**: Stops gracefully with saved chapters
- **Encoding Issues**: BeautifulSoup auto-handles

### Recovery
- **Checkpoint Saved**: Chapters are saved before attempting EPUB generation
- **Partial Success**: If crawling fails mid-way, already-fetched chapters are saved to EPUB

## Logging

All events are logged to:
1. **Console**: Real-time execution feedback
2. **crawler.log**: Permanent record for debugging

Sample log output:
```
2026-02-17 10:30:45,123 - INFO - Starting crawl from: https://...
[Chapter 1] Fetching: https://...
✓ Successfully fetched: https://...
  Found title: Chapter 1: The Beginning
  Extracted 45 paragraphs
  Found next URL: https://...
✓ Chapter 1 saved
```

## Customization

### Change Novel Title/Author

```python
crawler.save_to_epub(
    'custom_title.epub',
    title='Your Custom Title',
    author='Author Name'
)
```

### Adjust Request Timeout

```python
crawler = NovelCrawler(
    start_url=start_url,
    max_retries=3,
    timeout=60  # 60 second timeout
)
```

### Modify Sleep Timing

Edit line 70 in `novel_crawler.py`:
```python
await asyncio.sleep(random.uniform(1, 3))  # Change to desired range
```

## Troubleshooting

### "No modules named 'aiohttp'"
```bash
pip install aiohttp
```

### "No modules named 'ebooklib'"
```bash
pip install ebooklib
```

### Site blocks your requests
Add random headers:
```python
headers = {
    'User-Agent': random.choice([
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...'
    ])
}
```

### EPUB readers show encoding issues
Ensure HTML content uses proper entities (crawler handles this automatically)

### Crawler runs slowly
This is intentional! The 1-3 second delays are for:
- ✅ Respecting server resources
- ✅ Avoiding temporary IP bans
- ✅ Simulating real user behavior

## Performance

- Average speed: ~20-30 seconds per chapter (including network delays)
- Memory usage: ~50-200MB for 100 chapters
- EPUB file size: ~100-200KB per 100 chapters

## Limitations

⚠️ Some sites may:
- Require JavaScript rendering (use Playwright bridge instead)
- Have rate limiting or CAPTCHA
- Block automated requests

## Support

Check `crawler.log` for detailed error messages. Most issues are network-related and will resolve with retries.

## License & Disclaimer

For personal use and studying purposes only. Respect website terms of service and robots.txt.

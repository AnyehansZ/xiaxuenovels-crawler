import asyncio
from playwright.async_api import async_playwright

async def scrape_page(browser, url):
    # This function handles a single "tab"
    context = await browser.new_context()
    page = await context.new_page()
    
    print(f"📡 Opening: {url}")
    await page.goto(url)
    
    # Wait for the title to be available
    title = await page.title()
    print(f"✅ Finished: {title}")
    
    await context.close()
    return title

async def main():
    urls = [
        "https://quotes.toscrape.com/js/",
        "https://quotes.toscrape.com/scroll",
        "https://quotes.toscrape.com/tableful"
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # 1. Create a list of 'Tasks' (One for each URL)
        tasks = [scrape_page(browser, url) for url in urls]
        
        # 2. Run all tasks simultaneously
        # 'gather' waits for all of them to finish
        results = await asyncio.gather(*tasks)
        
        print(f"\nCollected {len(results)} titles in parallel!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
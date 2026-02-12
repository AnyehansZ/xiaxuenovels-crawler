from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        # 1. Launch a browser (headless=True means no window pops up)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 2. Go to a dynamic site
        print("Opening page...")
        page.goto("https://quotes.toscrape.com/js/")

        # 3. CRITICAL: Wait for the dynamic content to load
        # This tells Playwright to wait for the specific HTML tag to exist
        page.wait_for_selector(".quote")

        # 4. Extract data
        quotes = page.query_selector_all(".quote")
        for quote in quotes:
            text = quote.query_selector(".text").inner_text()
            author = quote.query_selector(".author").inner_text()
            print(f"{text} — {author}")

        browser.close()

if __name__ == "__main__":
    run()
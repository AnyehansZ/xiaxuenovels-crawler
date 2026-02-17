try:
    from playwright.sync_api import sync_playwright
    print("✅ Playwright imported successfully!")
except ImportError as e:
    print(f"❌ Still failing: {e}")
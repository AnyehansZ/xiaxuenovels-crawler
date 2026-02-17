import requests
from bs4 import BeautifulSoup
import csv
import time
import random
from urllib.parse import urljoin

# Setup
BASE_URL = "https://www.fanmtl.com/novel/"
START_URL = "memorize_1.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0"}

def start_crawler():
    # 1. Create and open the CSV file
    with open('novel_data.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write the header row
        writer.writerow(["Chapter Title", "content"])

        current_url = urljoin(BASE_URL, START_URL)

        while current_url:
            print(f"Crawling: {current_url}")
            response = requests.get(current_url, headers=HEADERS)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 2. Extract Data
            container = soup.find("div", class_="chapter-content")
            chapter_title = soup.find("div", class_="titles")
            titles=chapter_title.find_all("h1")
            full_title=" ".join([t.get_text(strip=True) for t in titles])
            all_paragraphs = container.find_all("p")
            full_text = " ".join([p.get_text(strip=True) for p in all_paragraphs])
            # Write a single row to the CSV
            writer.writerow([full_title, full_text])
            # 3. Handle Pagination
            next_button = soup.find("a", class_="chnav next")
            if next_button:
                next_page_rel = next_button.a["href"]
                current_url = urljoin(current_url, next_page_rel)
                
                # 4. Be Polite
                time.sleep(random.uniform(1, 3))
            else:
                current_url = None

    print("\n✅ Done! Data saved to books_data.csv")

if __name__ == "__main__":
    start_crawler()
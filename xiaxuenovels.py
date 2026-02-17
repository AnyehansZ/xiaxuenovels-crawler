import requests
from bs4 import BeautifulSoup
import csv
import time
import random
from urllib.parse import urljoin

# Setup
BASE_URL = "http://books.toscrape.com/catalogue/category/books/mystery_3/"
START_URL = "index.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0"}

def start_crawler():
    # 1. Create and open the CSV file
    with open('books_data.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write the header row
        writer.writerow(["Title", "Price"])

        current_url = urljoin(BASE_URL, START_URL)

        while current_url:
            print(f"Crawling: {current_url}")
            response = requests.get(current_url, headers=HEADERS)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 2. Extract Data
            books = soup.find_all("article", class_="product_pod")
            for book in books:
                title = book.h3.a["title"]
                price = book.find("p", class_="price_color").text
                # Write a single row to the CSV
                writer.writerow([title, price])

            # 3. Handle Pagination
            next_button = soup.find("li", class_="next")
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
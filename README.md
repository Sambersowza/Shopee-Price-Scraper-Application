# Shopee Price Scraper App

This is a Shopee product scraper with a user-friendly GUI — designed to scrape Shopee for product listings, display them in a table, and export data to Excel.

# Features
- Auto-search and scrape products by keyword
- Scrapes first 3 pages (auto-scroll on each page)
- Sort results by Price or Sold count
- Save scraped results and load them anytime
- Delete saved records
- Delete cookies
- Add cookies (manual login + save cookies)
- Return to welcome page from app
- Export results to Excel (.xlsx)

# How to Use

1️⃣ Install requirements:

pip install -r requirements.txt


2️⃣ Run the app:

python scraper.py

3️⃣ Steps in the app:

1. First time: Click "Add Cookies" → click continue for manual log in the pop up → manually log in to shopee → after the given time, the cookies will be saved.
2. Enter a product keyword (e.g., "laptop") → press "Scrape Now"
3. After scraping, you can:
    - Sort results
    - Save results
    - Export to Excel
    - Load saved results
    - Delete saved records
    - Export results in 
    - Return to welcome page

---

# Notes:
- Requires Google Chrome installed (latest version)
- No need to login again after cookies are saved
- If encounter loading issues, delete the existing cookies and add new ones via the "Add Cookies" option.
- Scraper will auto-navigate to page 1, page 2, and page 3
- Auto-scrolls on each page for more product results
- Result table is scrollable and sortable

---

# Developers
Made by Lester Sam Duremdes and Orlando Villanueva

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import time
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

COOKIES_FILE = "shopee_cookies.json"
MAX_RESULTS = 9999
DEBUG_HTML = "shopee_debug.html"
SAVED_DIR = "saved_results"

os.makedirs(SAVED_DIR, exist_ok=True)

def load_cookies(driver):
    if not os.path.exists(COOKIES_FILE):
        return
    with open(COOKIES_FILE, "r", encoding="utf-8") as f:
        cookies = json.load(f)
        for cookie in cookies:
            if 'sameSite' in cookie and cookie['sameSite'] == 'None':
                cookie['sameSite'] = 'Strict'
            driver.add_cookie(cookie)

def save_debug_html(driver):
    with open(DEBUG_HTML, "w", encoding="utf-8") as f:
        f.write(driver.page_source)

def clean_sold_value(sold):
    if not sold or sold == "N/A":
        return 0
    sold = sold.lower().replace("sold", "").replace("per month", "").replace("/month", "").strip()
    if 'k' in sold:
        return int(float(sold.replace("k", "")) * 1000)
    try:
        return int(sold.replace(",", ""))
    except:
        return 0

def clean_price_value(price):
    try:
        return float(price.replace(",", "").strip())
    except:
        return 0.0

def parse_products_from_html(html_source):
    soup = BeautifulSoup(html_source, "html.parser")
    products = soup.select("a.contents")
    results = []
    seen_links = set()

    for p in products[:MAX_RESULTS]:
        try:
            link = "https://shopee.ph" + p.get("href")
            if link in seen_links:
                continue
            seen_links.add(link)

            name_tag = p.select_one("div.line-clamp-2")
            name = name_tag.text.strip() if name_tag else "N/A"

            price = "N/A"
            price_container = p.select_one("div.flex.items-baseline")
            if price_container:
                spans = price_container.find_all("span")
                price = "".join(span.text.strip() for span in spans if "₱" not in span.text and span.text.strip())

            sold_tag = p.select_one("div.text-shopee-black87.text-xs.min-h-4")
            sold_text = sold_tag.text.strip() if sold_tag else ""
            if "sold/month" in sold_text or "per month" in sold_text:
                monthly_sold = sold_text
                total_sold = "N/A"
            elif "sold" in sold_text:
                total_sold = sold_text
                monthly_sold = "N/A"
            else:
                total_sold = "N/A"
                monthly_sold = "N/A"

            # for sorting — take the greater of the two
            sold_val = max(clean_sold_value(total_sold), clean_sold_value(monthly_sold))

            results.append({
                "name": name,
                "price": price,
                "total_sold": total_sold,
                "monthly_sold": monthly_sold,
                "link": link,
                "price_val": clean_price_value(price),
                "sold_val": sold_val
            })
        except Exception:
            continue

    return results

def scroll_page(driver, scroll_times=5):
    for _ in range(scroll_times):
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
        time.sleep(2)

def start_scraper_gui(keyword, treeview, results_holder, saved_dropdown):
    for row in treeview.get_children():
        treeview.delete(row)

    try:
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")

        driver = uc.Chrome(options=options)
        driver.get("https://shopee.ph")
        time.sleep(5)

        load_cookies(driver)
        driver.refresh()
        time.sleep(5)

        search_input = driver.find_element(By.CSS_SELECTOR, 'input.shopee-searchbar-input__input')
        search_input.send_keys(keyword)
        search_input.send_keys(Keys.ENTER)

        time.sleep(5)

        try:
            # Click "Top Sales" button after search
            top_sales_button = driver.find_element(By.XPATH, "//button[span[contains(text(), 'Top Sales')]]")
            driver.execute_script("arguments[0].click();", top_sales_button)
            print("✅ Top Sales clicked.")
            time.sleep(3)
        except Exception as e:
            print("⚠️ Could not click Top Sales button:", str(e))

        results = []

        for page_num in range(0, 3):  # Page 0,1,2
            url = f"https://shopee.ph/search?keyword={keyword}&page={page_num}&sortBy=sales"
            driver.get(url)
            time.sleep(8)
            scroll_page(driver, scroll_times=5)
            save_debug_html(driver)
            html_source = driver.page_source
            new_results = parse_products_from_html(html_source)
            print(f"Page {page_num} scraped: {len(new_results)} items")
            results.extend(new_results)

        driver.quit()

        # Deduplicate
        unique_links = set()
        final_results = []
        for item in results:
            if item['link'] not in unique_links:
                unique_links.add(item['link'])
                final_results.append(item)

        results_holder.clear()
        results_holder.extend(final_results)

        if not final_results:
            messagebox.showinfo("Info", "No results found or parsing error.")
            return

        show_results(treeview, final_results)

    except Exception as e:
        messagebox.showerror("Error", str(e))

def show_results(treeview, results):
    for row in treeview.get_children():
        treeview.delete(row)
    for i, item in enumerate(results, 1):
        treeview.insert("", "end", values=(i, item['name'], f"₱{item['price']}", item['total_sold'], item['monthly_sold'], item['link']))

def save_results(keyword, results):
    if not results:
        messagebox.showwarning("No Data", "Nothing to save.")
        return
    filename = os.path.join(SAVED_DIR, f"{keyword}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    messagebox.showinfo("Saved", f"Results saved as '{keyword}'")

def load_saved_keywords():
    return [f[:-5] for f in os.listdir(SAVED_DIR) if f.endswith(".json")]

def load_saved_results(keyword, treeview, results_holder):
    path = os.path.join(SAVED_DIR, f"{keyword}.json")
    if not os.path.exists(path):
        messagebox.showerror("Not Found", "Selected save not found.")
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        results_holder.clear()
        results_holder.extend(data)
        show_results(treeview, data)

def refresh_dropdown(saved_dropdown):
    saved_dropdown["values"] = load_saved_keywords()

def delete_cookies():
    if os.path.exists(COOKIES_FILE):
        os.remove(COOKIES_FILE)
        messagebox.showinfo("Cookies Deleted", "Shopee cookies have been deleted.")
    else:
        messagebox.showinfo("No Cookies Found", "There were no cookies to delete.")

def delete_saved_record(selected_keyword, saved_dropdown):
    path = os.path.join(SAVED_DIR, f"{selected_keyword}.json")
    if os.path.exists(path):
        os.remove(path)
        messagebox.showinfo("Deleted", f"Saved record '{selected_keyword}' deleted.")
        refresh_dropdown(saved_dropdown)
    else:
        messagebox.showerror("Not Found", "Selected save not found.")

def add_cookies_mode():
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    driver.get("https://shopee.ph")

    print("🚪 Please log in to Shopee manually.")
    input("✅ Press Enter after you're logged in...")

    cookies = driver.get_cookies()
    with open(COOKIES_FILE, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=4)
    print("✅ Cookies saved to 'shopee_cookies.json'")
    driver.quit()

def build_gui():
    welcome = tk.Tk()
    welcome.title("Welcome")
    welcome.geometry("400x300")
    welcome.configure(bg="#1e1e1e")

    tk.Label(welcome, text="Welcome to Price Scraper App", fg="white", bg="#1e1e1e", font=("Segoe UI", 14)).pack(pady=30)

    tk.Button(welcome, text="Enter App", width=20, command=lambda: [welcome.destroy(), build_main_gui()],
              bg="#4caf50", fg="white", font=("Segoe UI", 10, "bold")).pack(pady=10)

    tk.Button(welcome, text="Delete Cookies", width=20, command=delete_cookies,
              bg="#f44336", fg="white", font=("Segoe UI", 10, "bold")).pack(pady=10)

    tk.Button(welcome, text="Add Cookies (Login Mode)", width=20, command=add_cookies_mode,
              bg="#ff9800", fg="white", font=("Segoe UI", 10, "bold")).pack(pady=10)

    welcome.mainloop()

def build_main_gui():
    root = tk.Tk()
    root.title("Shopee Scraper MVP")
    root.geometry("1150x600")
    root.configure(bg="#1e1e1e")

    results_holder = []

    title = tk.Label(root, text="Shopee Product Scraper", fg="white", bg="#1e1e1e", font=("Segoe UI", 18, "bold"))
    title.pack(pady=10)

    input_frame = tk.Frame(root, bg="#1e1e1e")
    input_frame.pack()

    tk.Label(input_frame, text="Enter keyword:", fg="white", bg="#1e1e1e").pack(side=tk.LEFT)
    keyword_entry = tk.Entry(input_frame, width=25, font=("Segoe UI", 10))
    keyword_entry.pack(side=tk.LEFT, padx=5)

    sort_options = ttk.Combobox(input_frame, state="readonly", values=[
        "Sort by Price (High to Low)",
        "Sort by Price (Low to High)",
        "Sort by Sold (High to Low)",
        "Sort by Sold (Low to High)"
    ])
    sort_options.set("Sort Results")
    sort_options.pack(side=tk.LEFT, padx=5)

    tree_frame = tk.Frame(root)
    tree_frame.pack(pady=10)

    tree_scroll = tk.Scrollbar(tree_frame)
    tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    treeview = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set, columns=("#", "Name", "Price", "Total Sold", "Monthly Sold", "Link"), show="headings", height=20)
    tree_scroll.config(command=treeview.yview)

    treeview.heading("#", text="#")
    treeview.heading("Name", text="Name")
    treeview.heading("Price", text="Price")
    treeview.heading("Total Sold", text="Total Sold")
    treeview.heading("Monthly Sold", text="Monthly Sold")
    treeview.heading("Link", text="Product Link")

    treeview.column("#", width=30)
    treeview.column("Name", width=280)
    treeview.column("Price", width=100)
    treeview.column("Total Sold", width=100)
    treeview.column("Monthly Sold", width=120)
    treeview.column("Link", width=480)

    treeview.pack()

    def sort_results():
        if not results_holder:
            messagebox.showwarning("No Data", "Please scrape or load data first.")
            return
        choice = sort_options.get()
        if choice == "Sort by Price (High to Low)":
            results_holder.sort(key=lambda x: x["price_val"], reverse=True)
        elif choice == "Sort by Price (Low to High)":
            results_holder.sort(key=lambda x: x["price_val"])
        elif choice == "Sort by Sold (High to Low)":
            results_holder.sort(key=lambda x: x["sold_val"], reverse=True)
        elif choice == "Sort by Sold (Low to High)":
            results_holder.sort(key=lambda x: x["sold_val"])
        show_results(treeview, results_holder)

    tk.Button(input_frame, text="Apply Sort", command=sort_results,
              bg="#3f51b5", fg="white", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=5)

    tk.Button(input_frame, text="Save Results", command=lambda: save_results(keyword_entry.get().strip(), results_holder),
              bg="#009688", fg="white", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=5)

    saved_dropdown = ttk.Combobox(input_frame, state="readonly", values=load_saved_keywords())
    saved_dropdown.set("Saved ▼")
    saved_dropdown.pack(side=tk.LEFT, padx=5)

    tk.Button(input_frame, text="Load Results", command=lambda: load_saved_results(saved_dropdown.get(), treeview, results_holder),
              bg="#8bc34a", fg="black", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=5)

    tk.Button(input_frame, text="Refresh List", command=lambda: refresh_dropdown(saved_dropdown),
              bg="#607d8b", fg="white", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=5)

    tk.Button(input_frame, text="Delete Saved", command=lambda: delete_saved_record(saved_dropdown.get(), saved_dropdown),
              bg="#f44336", fg="white", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=5)

    def on_search():
        keyword = keyword_entry.get().strip()
        if keyword:
            start_scraper_gui(keyword, treeview, results_holder, saved_dropdown)
            refresh_dropdown(saved_dropdown)
        else:
            messagebox.showinfo("Input Error", "Please enter a keyword.")

    tk.Button(root, text="Scrape Now", command=on_search,
              bg="#ff5722", fg="white", font=("Segoe UI", 10, "bold")).pack(pady=5)

    tk.Button(root, text="Return to Welcome", command=lambda: [root.destroy(), build_gui()],
              bg="#9e9e9e", fg="white", font=("Segoe UI", 10)).pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    build_gui()

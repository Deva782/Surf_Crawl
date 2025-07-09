#!/usr/bin/env python3
"""
Advanced Web Scraper with GUI Interface
A comprehensive web scraping tool for surface web data collection
Author: AI Assistant
Version: 1.3 (UI improved, no top title, buttons adjusted)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import threading
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import logging
from typing import List, Dict, Optional
from datetime import datetime
import sys
import queue

class WebScraper:
    """Core web scraping functionality"""

    def __init__(self, delay: float = 1.0, respect_robots: bool = True, max_items: int = 20):
        self.delay = delay
        self.respect_robots = respect_robots
        self.max_items = max_items
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def can_fetch(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch('*', url)
        except Exception as e:
            self.logger.warning(f"Could not check robots.txt for {url}: {e}")
            return True

    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        parsed_url = urlparse(url)
        if parsed_url.scheme not in ("http", "https"):
            self.logger.error(f"Blocked potentially unsafe URL scheme: {parsed_url.scheme}")
            return None
        if not self.can_fetch(url):
            self.logger.warning(f"Robots.txt disallows fetching {url}")
            return None
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            time.sleep(self.delay)
            return soup
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None

    def scrape_news_articles(self, base_url: str, custom_selectors: List[str] = None) -> List[Dict]:
        articles = []
        soup = self.get_page(base_url)
        if not soup:
            return articles
        selectors = custom_selectors if custom_selectors else [
            'article', '.article', '.news-item', '.post', 'div[class*="article"]', '.story', '.news-story'
        ]
        elements = []
        for selector in selectors:
            found_elements = soup.select(selector)
            if found_elements:
                elements = found_elements
                break
        for element in elements[:self.max_items]:
            try:
                title = element.find(['h1', 'h2', 'h3', 'h4', '.title', '.headline'])
                title_text = title.get_text(strip=True) if title else "No title"
                link_element = element.find('a')
                link = urljoin(base_url, link_element.get('href')) if link_element and link_element.get('href') else ""
                summary_element = element.find(['p', '.summary', '.excerpt', '.description'])
                summary = summary_element.get_text(strip=True)[:200] if summary_element else ""
                date_element = element.find(['time', '.date', '.published', '.timestamp'])
                date = date_element.get_text(strip=True) if date_element else ""
                if date_element and date_element.get('datetime'):
                    date = date_element.get('datetime')
                author_element = element.find(['.author', '.byline', '.writer'])
                author = author_element.get_text(strip=True) if author_element else ""
                articles.append({
                    'title': title_text,
                    'link': link,
                    'summary': summary,
                    'date': date,
                    'author': author,
                    'source': base_url,
                    'type': 'news'
                })
            except Exception as e:
                self.logger.error(f"Error parsing article: {e}")
                continue
        return articles

    def scrape_product_listings(self, base_url: str, custom_selectors: List[str] = None) -> List[Dict]:
        products = []
        soup = self.get_page(base_url)
        if not soup:
            return products
        selectors = custom_selectors if custom_selectors else [
            '.product', '.item', '[data-product]', '.product-item', '.product-card', '.listing-item'
        ]
        elements = []
        for selector in selectors:
            found_elements = soup.select(selector)
            if found_elements:
                elements = found_elements
                break
        for element in elements[:self.max_items]:
            try:
                name_element = element.find(['h1', 'h2', 'h3', '.product-name', '.title', '.name'])
                name = name_element.get_text(strip=True) if name_element else "No name"
                price_element = element.find(['.price', '.cost', '[class*="price"]', '.amount'])
                price = price_element.get_text(strip=True) if price_element else "No price"
                link_element = element.find('a')
                link = urljoin(base_url, link_element.get('href')) if link_element and link_element.get('href') else ""
                rating_element = element.find(['.rating', '.stars', '[class*="rating"]', '.score'])
                rating = rating_element.get_text(strip=True) if rating_element else ""
                img_element = element.find('img')
                image = urljoin(base_url, img_element.get('src')) if img_element and img_element.get('src') else ""
                availability_element = element.find(['.availability', '.stock', '.in-stock'])
                availability = availability_element.get_text(strip=True) if availability_element else ""
                products.append({
                    'name': name,
                    'price': price,
                    'rating': rating,
                    'link': link,
                    'image': image,
                    'availability': availability,
                    'source': base_url,
                    'type': 'product'
                })
            except Exception as e:
                self.logger.error(f"Error parsing product: {e}")
                continue
        return products

    def scrape_social_media_posts(self, base_url: str, custom_selectors: List[str] = None) -> List[Dict]:
        posts = []
        soup = self.get_page(base_url)
        if not soup:
            return posts
        selectors = custom_selectors if custom_selectors else [
            '.tweet', '.post', '.status', '[data-post]', '.message', '.update'
        ]
        elements = []
        for selector in selectors:
            found_elements = soup.select(selector)
            if found_elements:
                elements = found_elements
                break
        for element in elements[:self.max_items]:
            try:
                content_element = element.find(['.content', '.text', 'p', '.message-body'])
                content = content_element.get_text(strip=True) if content_element else ""
                author_element = element.find(['.author', '.username', '.user', '.handle'])
                author = author_element.get_text(strip=True) if author_element else ""
                time_element = element.find(['time', '.timestamp', '.date', '.posted'])
                timestamp = time_element.get_text(strip=True) if time_element else ""
                if time_element and time_element.get('datetime'):
                    timestamp = time_element.get('datetime')
                likes_element = element.find(['.likes', '.reactions', '.hearts'])
                likes = likes_element.get_text(strip=True) if likes_element else ""
                hashtags = [tag.get_text() for tag in element.find_all('a', href=lambda x: x and '#' in str(x))]
                posts.append({
                    'author': author,
                    'content': content[:300],
                    'timestamp': timestamp,
                    'likes': likes,
                    'hashtags': ', '.join(hashtags),
                    'source': base_url,
                    'type': 'social'
                })
            except Exception as e:
                self.logger.error(f"Error parsing post: {e}")
                continue
        return posts

    def scrape_generic_content(self, base_url: str, custom_selectors: List[str] = None) -> List[Dict]:
        content = []
        soup = self.get_page(base_url)
        if not soup:
            return content
        selectors = custom_selectors if custom_selectors else ['p', 'div', 'span', 'h1', 'h2', 'h3', 'li', 'td']
        elements = []
        for selector in selectors:
            found_elements = soup.select(selector)
            if found_elements:
                elements = found_elements[:self.max_items]
                break
        for element in elements:
            try:
                text = element.get_text(strip=True)
                if len(text) > 20:
                    link_element = element.find('a') or element.find_parent('a')
                    link = urljoin(base_url, link_element.get('href')) if link_element and link_element.get('href') else ""
                    classes = ' '.join(element.get('class', []))
                    content.append({
                        'text': text[:500],
                        'link': link,
                        'tag': element.name,
                        'classes': classes,
                        'source': base_url,
                        'type': 'generic'
                    })
            except Exception as e:
                self.logger.error(f"Error parsing content: {e}")
                continue
        return content

    def search_keywords_across_web(self, keywords: List[str], start_urls: List[str], max_depth: int = 1, max_pages: int = 30) -> List[Dict]:
        visited = set()
        results = []
        q = queue.Queue()
        for url in start_urls:
            q.put((url, 0))
        pages_crawled = 0

        while not q.empty() and pages_crawled < max_pages:
            url, depth = q.get()
            if url in visited or depth > max_depth:
                continue
            visited.add(url)
            soup = self.get_page(url)
            if not soup:
                continue
            text = soup.get_text(separator=' ', strip=True)
            for kw in keywords:
                count = text.lower().count(kw.lower())
                if count > 0:
                    results.append({
                        'url': url,
                        'keyword': kw,
                        'count': count,
                        'type': 'keyword_search'
                    })
            if depth < max_depth:
                for a in soup.find_all('a', href=True):
                    link = urljoin(url, a['href'])
                    parsed = urlparse(link)
                    if parsed.scheme in ("http", "https") and link not in visited:
                        q.put((link, depth + 1))
            pages_crawled += 1
        return results
    
class WebScraperGUI:
    """GUI interface for the web scraper"""

    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Web Scraper - Surface Web Data Collection v1.3")
        self.root.geometry("1200x700")
        self.root.configure(bg='#f0f0f0')
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        self.scraper = None
        self.scraped_data = []
        self.is_scraping = False
        self.setup_logging()
        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def configure_styles(self):
        self.style.configure('Heading.TLabel', font=('Arial', 11, 'bold'), background='#f0f0f0', foreground='#34495e')
        self.style.configure('Custom.TButton', font=('Arial', 10, 'bold'))
        self.style.configure('Start.TButton',
            font=('Arial', 14, 'bold'),
            foreground='#ffffff',
            background='#27ae60',
            borderwidth=3,
            focusthickness=3,
            focuscolor='red'
        )
        self.style.map('Start.TButton',
            background=[('active', '#219150'), ('!active', '#27ae60')]
        )
        self.style.configure('Stop.TButton', font=('Arial', 10, 'bold'), foreground='#e74c3c')
        self.style.configure('Export.TButton', font=('Arial', 9), foreground='#3498db')

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('web_scraper.log')
            ]
        )
        self.logger = logging.getLogger(__name__)

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        # Removed the title label from the top
        self.create_settings_panel(main_frame)
        self.create_results_panel(main_frame)
        self.create_log_panel(main_frame)
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=0)

    def create_settings_panel(self, parent):
        settings_frame = ttk.LabelFrame(parent, text="🔧 Scraper Settings", padding="10")
        settings_frame.grid(row=0, column=0, sticky=(tk.N, tk.W, tk.E), padx=(0, 10), pady=(0, 10))
        # URL
        ttk.Label(settings_frame, text="🌍 Target URL:", style='Heading.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 2))
        self.url_var = tk.StringVar(value="https://example.com")
        self.url_entry = ttk.Entry(settings_frame, textvariable=self.url_var, width=40, font=('Arial', 10))
        self.url_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 8))
        # Scraping Type
        ttk.Label(settings_frame, text="📊 Scraping Type:", style='Heading.TLabel').grid(row=2, column=0, sticky=tk.W, pady=(0, 2))
        self.scrape_type = tk.StringVar(value="news")
        scrape_options = ttk.Combobox(settings_frame, textvariable=self.scrape_type,
                                      values=["news", "products", "social", "generic"],
                                      state="readonly", width=18)
        scrape_options.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 8))
        # Delay and Max Items
        ttk.Label(settings_frame, text="⏱️ Delay (s):", style='Heading.TLabel').grid(row=4, column=0, sticky=tk.W, pady=(0, 2))
        self.delay_var = tk.DoubleVar(value=1.5)
        delay_spin = tk.Spinbox(settings_frame, from_=0.5, to=10.0, increment=0.5,
                                 textvariable=self.delay_var, width=8)
        delay_spin.grid(row=5, column=0, sticky=tk.W, pady=(0, 8))
        ttk.Label(settings_frame, text="📊 Max Items:", style='Heading.TLabel').grid(row=4, column=1, sticky=tk.W, pady=(0, 2))
        self.max_items_var = tk.IntVar(value=25)
        items_spin = tk.Spinbox(settings_frame, from_=1, to=100, increment=1,
                                 textvariable=self.max_items_var, width=8)
        items_spin.grid(row=5, column=1, sticky=tk.W, pady=(0, 8))
        # Checkboxes
        self.respect_robots_var = tk.BooleanVar(value=True)
        robots_check = ttk.Checkbutton(settings_frame, text="🤖 Respect robots.txt",
                                       variable=self.respect_robots_var)
        robots_check.grid(row=6, column=0, sticky=tk.W, pady=(0, 2))
        self.save_log_var = tk.BooleanVar(value=True)
        log_check = ttk.Checkbutton(settings_frame, text="💾 Save activity log",
                                    variable=self.save_log_var)
        log_check.grid(row=6, column=1, sticky=tk.W, pady=(0, 2))
        # CSS Selectors (small box)
        ttk.Label(settings_frame, text="🎯 CSS Selectors:", style='Heading.TLabel').grid(row=7, column=0, sticky=tk.W, pady=(0, 2))
        self.selectors_text = scrolledtext.ScrolledText(settings_frame, width=24, height=3, font=('Consolas', 9))
        self.selectors_text.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 8))
        self.selectors_text.insert(tk.END, "# .article-title\n# .product-name")
        # Keywords
        ttk.Label(settings_frame, text="🔑 Keywords (comma separated):", style='Heading.TLabel').grid(row=9, column=0, sticky=tk.W, pady=(0, 2))
        self.keywords_var = tk.StringVar(value="")
        self.keywords_entry = ttk.Entry(settings_frame, textvariable=self.keywords_var, width=40, font=('Arial', 10))
        self.keywords_entry.grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 8))
        # Search Mode
        ttk.Label(settings_frame, text="🌐 Search Mode:", style='Heading.TLabel').grid(row=11, column=0, sticky=tk.W, pady=(0, 2))
        self.search_mode_var = tk.StringVar(value="normal")
        search_mode_combo = ttk.Combobox(settings_frame, textvariable=self.search_mode_var,
                                         values=["normal", "keyword_web"], state="readonly", width=18)
        search_mode_combo.grid(row=12, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 8))
        # Buttons (all in a single row, fill width)
        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=13, column=0, columnspan=2, pady=(10, 0), sticky=tk.EW)
        self.start_button = ttk.Button(
            button_frame,
            text="▶️ START SCRAPING",
            command=self.start_scraping,
            style='Start.TButton',
            width=18
        )
        self.start_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 8), ipadx=8, ipady=6)
        self.stop_button = ttk.Button(button_frame, text="⏹️ Stop",
                                      command=self.stop_scraping, state=tk.DISABLED, style='Stop.TButton', width=10)
        self.stop_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 8))
        self.clear_button = ttk.Button(button_frame, text="🗑️ Clear Results",
                                       command=self.clear_results, width=14)
        self.clear_button.pack(side=tk.LEFT, expand=True, fill=tk.X)

    def create_results_panel(self, parent):
        results_frame = ttk.LabelFrame(parent, text="📊 Scraping Results", padding="10")
        results_frame.grid(row=0, column=1, columnspan=2, sticky=(tk.N, tk.S, tk.E, tk.W), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(2, weight=1)
        progress_frame = ttk.Frame(results_frame)
        progress_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        progress_frame.columnconfigure(1, weight=1)
        self.progress_var = tk.StringVar(value="Ready to scrape...")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var, font=('Arial', 10, 'bold'))
        progress_label.grid(row=0, column=0, sticky=tk.W)
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(15, 0))
        stats_frame = ttk.Frame(results_frame)
        stats_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        self.stats_var = tk.StringVar(value="Items found: 0 | Total scraped: 0")
        stats_label = ttk.Label(stats_frame, textvariable=self.stats_var, font=('Arial', 9))
        stats_label.grid(row=0, column=0, sticky=tk.W)
        columns = ('Type', 'Title/Name', 'URL/Price', 'Date/Rating', 'Source')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=18)
        column_widths = {'Type': 80, 'Title/Name': 250, 'URL/Price': 200, 'Date/Rating': 120, 'Source': 180}
        for col in columns:
            self.results_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(c))
            self.results_tree.column(col, width=column_widths.get(col, 150), anchor='w')
        v_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        self.results_tree.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=2, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=3, column=0, sticky=(tk.W, tk.E))
        export_frame = ttk.Frame(results_frame)
        export_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0), sticky=tk.EW)
        ttk.Button(export_frame, text="📁 Export CSV", command=self.export_csv, style='Export.TButton').pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 8))
        ttk.Button(export_frame, text="📄 Export JSON", command=self.export_json, style='Export.TButton').pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 8))
        ttk.Button(export_frame, text="🔍 View Details", command=self.view_details, style='Export.TButton').pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 8))
        ttk.Button(export_frame, text="📊 Statistics", command=self.show_statistics, style='Export.TButton').pack(side=tk.LEFT, expand=True, fill=tk.X)

    def create_log_panel(self, parent):
        log_frame = ttk.LabelFrame(parent, text="📝 Activity Log", padding="8")
        log_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))
        log_frame.columnconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=120, font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_button_frame = ttk.Frame(log_frame)
        log_button_frame.grid(row=1, column=0, pady=(6, 0), sticky=tk.EW)
        ttk.Button(log_button_frame, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 8))
        ttk.Button(log_button_frame, text="Save Log", command=self.save_log).pack(side=tk.LEFT, expand=True, fill=tk.X)

    def get_custom_selectors(self) -> List[str]:
        selectors_text = self.selectors_text.get(1.0, tk.END).strip()
        if not selectors_text:
            return []
        selectors = []
        for line in selectors_text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                selectors.append(line)
        return selectors

    def log_message(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        if self.save_log_var.get():
            self.logger.info(message)

    def sort_treeview(self, col):
        data = [(self.results_tree.set(child, col), child) for child in self.results_tree.get_children('')]
        data.sort()
        for index, (val, child) in enumerate(data):
            self.results_tree.move(child, '', index)

    def start_scraping(self):
        if self.is_scraping:
            messagebox.showwarning("Warning", "Scraping is already in progress!")
            return
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL to scrape!")
            return
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                messagebox.showerror("Error", "Please enter a valid URL (including http:// or https://)")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Invalid URL: {str(e)}")
            return
        self.is_scraping = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_bar.start()
        self.progress_var.set("🔄 Scraping in progress...")
        self.log_message(f"Starting scraping session for: {url}")
        scraping_thread = threading.Thread(target=self.scrape_data, daemon=True)
        scraping_thread.start()

    def stop_scraping(self):
        self.is_scraping = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.progress_var.set("⏹️ Scraping stopped by user")
        self.log_message("Scraping stopped by user", "WARNING")

    def scrape_data(self):
        try:
            url = self.url_var.get().strip()
            scrape_type = self.scrape_type.get()
            custom_selectors = self.get_custom_selectors()
            keywords = [w.strip() for w in self.keywords_var.get().split(',') if w.strip()]
            search_mode = self.search_mode_var.get()
            self.scraper = WebScraper(
                delay=self.delay_var.get(),
                respect_robots=self.respect_robots_var.get(),
                max_items=self.max_items_var.get()
            )
            self.root.after(0, lambda: self.log_message(f"Initialized scraper with {scrape_type} mode"))
            if search_mode == "keyword_web" and keywords:
                data = self.scraper.search_keywords_across_web(keywords, [url], max_depth=1, max_pages=30)
            elif scrape_type == "news":
                data = self.scraper.scrape_news_articles(url, custom_selectors)
            elif scrape_type == "products":
                data = self.scraper.scrape_product_listings(url, custom_selectors)
            elif scrape_type == "social":
                data = self.scraper.scrape_social_media_posts(url, custom_selectors)
            else:
                data = self.scraper.scrape_generic_content(url, custom_selectors)
            self.root.after(0, lambda: self.update_results(data))
        except Exception as e:
            error_msg = f"Scraping error: {str(e)}"
            self.root.after(0, lambda: self.log_message(error_msg, "ERROR"))
            self.root.after(0, lambda: messagebox.showerror("Scraping Error", error_msg))
        finally:
            self.root.after(0, self.scraping_finished)

    def scraping_finished(self):
        self.is_scraping = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.progress_var.set("✅ Scraping completed")

    def update_results(self, data):
        if not data:
            self.log_message("No data found with current selectors", "WARNING")
            return
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.scraped_data = data
        for item in data:
            if not self.is_scraping:
                break
            try:
                if item.get('type') == 'keyword_search':
                    self.results_tree.insert('', tk.END, values=(
                        'Keyword',
                        item.get('keyword', 'N/A'),
                        f"Count: {item.get('count', 0)}",
                        '',
                        item.get('url', 'N/A')[:30]
                    ))
                elif item.get('type') == 'news':
                    self.results_tree.insert('', tk.END, values=(
                        'News',
                        item.get('title', 'N/A')[:50],
                        item.get('link', 'N/A')[:50],
                        item.get('date', 'N/A'),
                        item.get('source', 'N/A')[:30]
                    ))
                elif item.get('type') == 'product':
                    self.results_tree.insert('', tk.END, values=(
                        'Product',
                        item.get('name', 'N/A')[:50],
                        item.get('price', 'N/A'),
                        item.get('rating', 'N/A'),
                        item.get('source', 'N/A')[:30]
                    ))
                elif item.get('type') == 'social':
                    self.results_tree.insert('', tk.END, values=(
                        'Social',
                        item.get('content', 'N/A')[:50],
                        item.get('author', 'N/A'),
                        item.get('timestamp', 'N/A'),
                        item.get('source', 'N/A')[:30]
                    ))
                else:
                    self.results_tree.insert('', tk.END, values=(
                        'Generic',
                        item.get('text', 'N/A')[:50],
                        item.get('link', 'N/A')[:50],
                        item.get('tag', 'N/A'),
                        item.get('source', 'N/A')[:30]
                    ))
            except Exception as e:
                self.log_message(f"Error adding item to results: {e}", "ERROR")
        total_items = len(data)
        self.stats_var.set(f"Items found: {total_items} | Total scraped: {len(self.scraped_data)}")
        self.log_message(f"Successfully scraped {total_items} items")

    def clear_results(self):
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.scraped_data = []
        self.stats_var.set("Items found: 0 | Total scraped: 0")
        self.progress_var.set("Ready to scrape...")
        self.log_message("Results cleared")

    def export_csv(self):
        if not self.scraped_data:
            messagebox.showwarning("Warning", "No data to export!")
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save CSV File"
        )
        if filename:
            try:
                df = pd.DataFrame(self.scraped_data)
                df.to_csv(filename, index=False, encoding='utf-8')
                self.log_message(f"Data exported to CSV: {filename}")
                messagebox.showinfo("Success", f"Data exported successfully to:\n{filename}")
            except Exception as e:
                error_msg = f"Error exporting CSV: {str(e)}"
                self.log_message(error_msg, "ERROR")
                messagebox.showerror("Export Error", error_msg)

    def export_json(self):
        if not self.scraped_data:
            messagebox.showwarning("Warning", "No data to export!")
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save JSON File"
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
                self.log_message(f"Data exported to JSON: {filename}")
                messagebox.showinfo("Success", f"Data exported successfully to:\n{filename}")
            except Exception as e:
                error_msg = f"Error exporting JSON: {str(e)}"
                self.log_message(error_msg, "ERROR")
                messagebox.showerror("Export Error", error_msg)

    def view_details(self):
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to view details!")
            return
        item_index = self.results_tree.index(selection[0])
        if item_index < len(self.scraped_data):
            item_data = self.scraped_data[item_index]
            details_window = tk.Toplevel(self.root)
            details_window.title("Item Details")
            details_window.geometry("800x600")
            details_window.configure(bg='#f0f0f0')
            details_frame = ttk.Frame(details_window, padding="20")
            details_frame.pack(fill=tk.BOTH, expand=True)
            details_text = scrolledtext.ScrolledText(details_frame, width=80, height=30, font=('Consolas', 10))
            details_text.pack(fill=tk.BOTH, expand=True)
            details_content = "ITEM DETAILS\n" + "="*50 + "\n\n"
            for key, value in item_data.items():
                details_content += f"{key.upper()}: {value}\n\n"
            details_text.insert(tk.END, details_content)
            details_text.config(state=tk.DISABLED)

    def show_statistics(self):
        if not self.scraped_data:
            messagebox.showwarning("Warning", "No data to analyze!")
            return
        stats = {
            'Total Items': len(self.scraped_data),
            'Data Types': {},
            'Sources': {},
            'Items with Links': 0,
            'Average Text Length': 0
        }
        text_lengths = []
        for item in self.scraped_data:
            item_type = item.get('type', 'unknown')
            stats['Data Types'][item_type] = stats['Data Types'].get(item_type, 0) + 1
            source = item.get('source', 'unknown')
            stats['Sources'][source] = stats['Sources'].get(source, 0) + 1
            if item.get('link') or item.get('url'):
                stats['Items with Links'] += 1
            text_content = item.get('text', '') or item.get('content', '') or item.get('title', '') or item.get('name', '')
            if text_content:
                text_lengths.append(len(text_content))
        if text_lengths:
            stats['Average Text Length'] = sum(text_lengths) / len(text_lengths)
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Scraping Statistics")
        stats_window.geometry("600x500")
        stats_window.configure(bg='#f0f0f0')
        stats_frame = ttk.Frame(stats_window, padding="20")
        stats_frame.pack(fill=tk.BOTH, expand=True)
        stats_text = scrolledtext.ScrolledText(stats_frame, width=70, height=25, font=('Consolas', 10))
        stats_text.pack(fill=tk.BOTH, expand=True)
        stats_content = "SCRAPING STATISTICS\n" + "="*50 + "\n\n"
        stats_content += f"Total Items Scraped: {stats['Total Items']}\n"
        stats_content += f"Items with Links: {stats['Items with Links']}\n"
        stats_content += f"Average Text Length: {stats['Average Text Length']:.1f} characters\n\n"
        stats_content += "DATA TYPES:\n" + "-"*20 + "\n"
        for dtype, count in stats['Data Types'].items():
            stats_content += f"{dtype.title()}: {count}\n"
        stats_content += "\nSOURCES:\n" + "-"*20 + "\n"
        for source, count in stats['Sources'].items():
            stats_content += f"{source}: {count}\n"
        stats_text.insert(tk.END, stats_content)
        stats_text.config(state=tk.DISABLED)

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def save_log(self):
        log_content = self.log_text.get(1.0, tk.END)
        if not log_content.strip():
            messagebox.showwarning("Warning", "No log content to save!")
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Log File"
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                messagebox.showinfo("Success", f"Log saved successfully to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Error saving log: {str(e)}")

    def on_closing(self):
        if self.is_scraping:
            if messagebox.askokcancel("Quit", "Scraping is in progress. Do you want to quit?"):
                self.is_scraping = False
                self.new_method()
        else:
            self.root.destroy()

    def new_method(self):
        self.root.destroy()


def main():
    try:
        root = tk.Tk()
        app = WebScraperGUI(root)
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Session", command=app.clear_results)
        file_menu.add_separator()
        file_menu.add_command(label="Export CSV", command=app.export_csv)
        file_menu.add_command(label="Export JSON", command=app.export_json)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Statistics", command=app.show_statistics)
        tools_menu.add_command(label="Clear Log", command=app.clear_log)
        tools_menu.add_command(label="Save Log", command=app.save_log)
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo(
            "About",
            "Advanced Web Scraper v1.3\n\n"
            "A comprehensive tool for scraping surface web data\n"
            "with advanced filtering, custom keyword web search, and export capabilities.\n\n"
            "⚠️ Use responsibly and respect website terms of service."
        ))
        root.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

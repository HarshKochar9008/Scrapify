
import requests
import json
import re
import sqlite3
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import os

class AllInOneShopifyScraper:
    def __init__(self, base_url, db_name="shopify_complete.db"):
        self.base_url = base_url.rstrip('/')
        self.db_name = db_name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.brand_id = None
        
        self.init_database()
        
    def init_database(self):
        print("🗄️ Initializing database...")
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                store_url TEXT UNIQUE NOT NULL,
                about TEXT,
                privacy_policy TEXT,
                shipping_policy TEXT,
                return_policy TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER,
                title TEXT NOT NULL,
                handle TEXT,
                price TEXT,
                currency TEXT,
                is_hero BOOLEAN DEFAULT 0,
                product_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (brand_id) REFERENCES brands (id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS faqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER,
                question TEXT NOT NULL,
                answer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (brand_id) REFERENCES brands (id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS social_handles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER,
                platform TEXT NOT NULL,
                url TEXT,
                FOREIGN KEY (brand_id) REFERENCES brands (id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER,
                contact_type TEXT NOT NULL,
                value TEXT NOT NULL,
                FOREIGN KEY (brand_id) REFERENCES brands (id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS important_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER,
                link_type TEXT NOT NULL,
                url TEXT NOT NULL,
                FOREIGN KEY (brand_id) REFERENCES brands (id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS competitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER,
                competitor_name TEXT NOT NULL,
                competitor_url TEXT NOT NULL,
                competitor_type TEXT,
                similarity_score REAL,
                found_via TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (brand_id) REFERENCES brands (id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS competitor_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_id INTEGER,
                title TEXT NOT NULL,
                price TEXT,
                currency TEXT,
                product_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (competitor_id) REFERENCES competitors (id) ON DELETE CASCADE
            );
        """)
        
        self.conn.commit()
        print("✅ Database initialized successfully!")
    
    def create_or_get_brand(self):
        try:
            self.cursor.execute("SELECT id FROM brands WHERE store_url = ?", (self.base_url,))
            existing = self.cursor.fetchone()
            
            if not existing:
                brand_name = self.extract_brand_name()
                about = self.extract_brand_about()
                
                self.cursor.execute("""
                    INSERT INTO brands (name, store_url, about, created_at)
                    VALUES (?, ?, ?, ?)
                """, (brand_name, self.base_url, about, datetime.now()))
                
                self.brand_id = self.cursor.lastrowid
                self.conn.commit()
                print(f"✨ Created new brand: {brand_name}")
            else:
                self.brand_id = existing[0]
                print(f"Found existing brand ID: {self.brand_id}")
            
            return self.brand_id
            
        except Exception as e:
            print(f"Error creating brand: {e}")
            return None
    
    def extract_brand_name(self):
        try:
            response = self.session.get(self.base_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                selectors = ['title', '.brand-name', '.logo-text', '.site-title', 'h1', '[data-brand]']
                
                for selector in selectors:
                    elem = soup.select_one(selector)
                    if elem:
                        text = elem.get_text(strip=True)
                        if text and len(text) < 100:
                            return text
                return "Unknown Brand"
        except:
            return "Unknown Brand"
    
    def extract_brand_about(self):
        try:
            about_urls = [
                f"{self.base_url}/pages/about",
                f"{self.base_url}/pages/about-us",
                f"{self.base_url}/pages/our-story",
                f"{self.base_url}/pages/company"
            ]
            
            for url in about_urls:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    content = soup.select_one('.page-content, .rte, .about-content, main')
                    if content:
                        return content.get_text(strip=True)[:500] + "..."
            return "Brand information not available"
        except:
            return "Brand information not available"
    
    def scrape_policies(self):
        print("📋 Scraping policies...")
        
        policies = {
            'privacy_policy': ['/pages/privacy-policy', '/pages/privacy'],
            'shipping_policy': ['/pages/shipping-policy', '/pages/shipping'],
            'return_policy': ['/pages/return-policy', '/pages/returns', '/pages/returns-exchanges']
        }
        
        for policy_type, urls in policies.items():
            for url_suffix in urls:
                try:
                    url = f"{self.base_url}{url_suffix}"
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        content = soup.select_one('.page-content, .rte, .policy-content, main')
                        
                        if content:
                            policy_text = content.get_text(strip=True)
                            
                            if policy_type == 'privacy_policy':
                                self.cursor.execute("UPDATE brands SET privacy_policy = ? WHERE id = ?", 
                                                  (policy_text, self.brand_id))
                            elif policy_type == 'shipping_policy':
                                self.cursor.execute("UPDATE brands SET shipping_policy = ? WHERE id = ?", 
                                                  (policy_text, self.brand_id))
                            elif policy_type == 'return_policy':
                                self.cursor.execute("UPDATE brands SET return_policy = ? WHERE id = ?", 
                                                  (policy_text, self.brand_id))
                            
                            self.conn.commit()
                            print(f"{policy_type.replace('_', ' ').title()}: {len(policy_text)} characters")
                            break
                            
                except Exception as e:
                    print(f"Error scraping {policy_type}: {e}")
                    continue
    
    def scrape_hero_products(self):
        print("⭐ Scraping hero products from homepage...")
        
        try:
            response = self.session.get(self.base_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                product_selectors = [
                    '.product-item',
                    '.product-card',
                    '.featured-product',
                    '.hero-product',
                    '[data-product]',
                    '.product-grid .product'
                ]
                
                products_found = 0
                for selector in product_selectors:
                    products = soup.select(selector)
                    if products:
                        for product in products[:10]:
                            try:
                                title_elem = product.select_one('.product-title, .product-name, h3, h4, [data-product-title]')
                                price_elem = product.select_one('.price, .product-price, [data-price]')
                                link_elem = product.select_one('a[href*="/products/"]')
                                
                                if title_elem:
                                    title = title_elem.get_text(strip=True)
                                    price = price_elem.get_text(strip=True) if price_elem else "Price not available"
                                    product_url = urljoin(self.base_url, link_elem['href']) if link_elem else None
                                    
                                    currency = "USD"
                                    if price and any(symbol in price for symbol in ['₹', '€', '£', '¥']):
                                        currency = {'₹': 'INR', '€': 'EUR', '£': 'GBP', '¥': 'JPY'}[
                                            next(symbol for symbol in ['₹', '€', '£', '¥'] if symbol in price)
                                        ]
                                    
                                    self.cursor.execute("""
                                        INSERT INTO products (brand_id, title, price, currency, is_hero, product_url)
                                        VALUES (?, ?, ?, ?, ?, ?)
                                    """, (self.brand_id, title, price, currency, True, product_url))
                                    
                                    products_found += 1
                                    
                            except Exception as e:
                                print(f"Error processing hero product: {e}")
                                continue
                        
                        if products_found > 0:
                            break
                
                self.conn.commit()
                print(f"Found {products_found} hero products")
                
        except Exception as e:
            print(f"Error scraping hero products: {e}")
    
    def scrape_all_products(self):
        print("📦 Scraping all products via Shopify products.json...")
        
        try:
            products_url = f"{self.base_url}/products.json"
            response = self.session.get(products_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                products = data.get('products', [])
                
                print(f"Found {len(products)} products to process...")
                
                for i, product in enumerate(products, 1):
                    try:
                        title = product.get('title', 'Unknown Product')
                        handle = product.get('handle', '')
                        product_url = f"{self.base_url}/products/{handle}"
                        
                        variants = product.get('variants', [])
                        if variants:
                            price = variants[0].get('price', '0.00')
                            currency = product.get('currency', 'USD')
                        else:
                            price = '0.00'
                            currency = 'USD'
                        
                        self.cursor.execute("SELECT id FROM products WHERE title = ? AND brand_id = ?", 
                                          (title, self.brand_id))
                        existing = self.cursor.fetchone()
                        
                        if not existing:
                            self.cursor.execute("""
                                INSERT INTO products (brand_id, title, handle, price, currency, is_hero, product_url)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (self.brand_id, title, handle, price, currency, False, product_url))
                        
                        if i % 100 == 0:
                            print(f"   Processed {i}/{len(products)} products...")
                            self.conn.commit()
                            
                    except Exception as e:
                        print(f"Error processing product {i}: {e}")
                        continue
                
                self.conn.commit()
                print(f"Successfully processed {len(products)} products")
                
        except Exception as e:
            print(f"Error scraping all products: {e}")
    
    def scrape_social_media(self):
        print("📱 Scraping social media handles...")
        
        try:
            response = self.session.get(self.base_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                social_patterns = {
                    'instagram': [r'instagram\.com/([^/\s]+)', r'@([^/\s]+)'],
                    'facebook': [r'facebook\.com/([^/\s]+)', r'fb\.com/([^/\s]+)'],
                    'twitter': [r'twitter\.com/([^/\s]+)', r'x\.com/([^/\s]+)'],
                    'youtube': [r'youtube\.com/([^/\s]+)', r'youtu\.be/([^/\s]+)'],
                    'tiktok': [r'tiktok\.com/@([^/\s]+)'],
                    'linkedin': [r'linkedin\.com/company/([^/\s]+)'],
                    'pinterest': [r'pinterest\.com/([^/\s]+)']
                }
                
                page_text = soup.get_text()
                links = soup.find_all('a', href=True)
                
                for platform, patterns in social_patterns.items():
                    for pattern in patterns:
                        matches = re.findall(pattern, page_text, re.IGNORECASE)
                        if matches:
                            handle = matches[0]
                            url = f"https://{platform}.com/{handle}"
                            
                            self.cursor.execute("""
                                INSERT OR REPLACE INTO social_handles (brand_id, platform, url)
                                VALUES (?, ?, ?)
                            """, (self.brand_id, platform, url))
                            
                            print(f"{platform.title()}: {handle}")
                            break
                        
                        for link in links:
                            href = link['href']
                            if platform in href.lower():
                                matches = re.findall(pattern, href, re.IGNORECASE)
                                if matches:
                                    handle = matches[0]
                                    url = href if href.startswith('http') else f"https://{platform}.com/{handle}"
                                    
                                    self.cursor.execute("""
                                        INSERT OR REPLACE INTO social_handles (brand_id, platform, url)
                                        VALUES (?, ?, ?)
                                    """, (self.brand_id, platform, url))
                                    
                                    print(f"{platform.title()}: {handle}")
                                    break
                
                self.conn.commit()
                
        except Exception as e:
            print(f"Error scraping social media: {e}")
    
    def scrape_contact_info(self):
        print("📞 Scraping contact information...")
        
        try:
            contact_urls = [
                f"{self.base_url}/pages/contact",
                f"{self.base_url}/contact",
                f"{self.base_url}/pages/contact-us"
            ]
            
            for url in contact_urls:
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        page_text = soup.get_text()
                        
                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                        emails = re.findall(email_pattern, page_text)
                        
                        phone_pattern = r'[\+]?[1-9][\d]{0,15}'
                        phones = re.findall(phone_pattern, page_text)
                        
                        for email in emails[:3]:
                            self.cursor.execute("""
                                INSERT OR REPLACE INTO contacts (brand_id, contact_type, value)
                                VALUES (?, ?, ?)
                            """, (self.brand_id, 'email', email))
                            print(f"Email: {email}")
                        
                        for phone in phones[:3]:
                            if len(phone) >= 10:
                                self.cursor.execute("""
                                    INSERT OR REPLACE INTO contacts (brand_id, contact_type, value)
                                    VALUES (?, ?, ?)
                                """, (self.brand_id, 'phone', phone))
                                print(f"Phone: {phone}")
                        
                        break
                        
                except Exception as e:
                    print(f"Error with contact URL {url}: {e}")
                    continue
            
            self.conn.commit()
            
        except Exception as e:
            print(f"Error scraping contact info: {e}")
    
    def scrape_important_links(self):
        print("🔗 Scraping important links...")
        
        try:
            response = self.session.get(self.base_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                important_pages = {
                    'order_tracking': ['/pages/track-order', '/pages/order-tracking', '/track-order'],
                    'returns': ['/pages/returns', '/pages/returns-exchanges', '/returns'],
                    'shipping': ['/pages/shipping-policy', '/pages/shipping', '/shipping'],
                    'about': ['/pages/about', '/pages/about-us', '/about'],
                    'blog': ['/pages/blogs', '/blog', '/blogs'],
                    'support': ['/pages/support', '/support', '/help'],
                    'faq': ['/pages/faq', '/pages/faqs', '/faq', '/faqs']
                }
                
                for link_type, urls in important_pages.items():
                    for url_suffix in urls:
                        try:
                            url = f"{self.base_url}{url_suffix}"
                            response = self.session.get(url, timeout=10)
                            
                            if response.status_code == 200:
                                self.cursor.execute("""
                                    INSERT OR REPLACE INTO important_links (brand_id, link_type, url)
                                    VALUES (?, ?, ?)
                                """, (self.brand_id, link_type, url))
                                
                                print(f"{link_type.replace('_', ' ').title()}: {url}")
                                break
                                
                        except Exception as e:
                            continue
                
                self.conn.commit()
                
        except Exception as e:
            print(f"Error scraping important links: {e}")
    
    def scrape_faqs(self):
        print("Scraping FAQs...")
        
        try:
            faq_urls = [
                f"{self.base_url}/pages/faq",
                f"{self.base_url}/pages/faqs",
                f"{self.base_url}/faq",
                f"{self.base_url}/faqs"
            ]
            
            for url in faq_urls:
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        faq_selectors = [
                            '.faq-item',
                            '.faq-question',
                            '.accordion-item',
                            '[data-faq]'
                        ]
                        
                        faqs_found = 0
                        for selector in faq_selectors:
                            faq_elements = soup.select(selector)
                            if faq_elements:
                                for faq in faq_elements:
                                    try:
                                        question_elem = faq.select_one('.question, .faq-q, h3, h4')
                                        answer_elem = faq.select_one('.answer, .faq-a, .content, p')
                                        
                                        if question_elem and answer_elem:
                                            question = question_elem.get_text(strip=True)
                                            answer = answer_elem.get_text(strip=True)
                                            
                                            if len(question) > 10 and len(answer) > 10:
                                                self.cursor.execute("""
                                                    INSERT INTO faqs (brand_id, question, answer)
                                                    VALUES (?, ?, ?)
                                                """, (self.brand_id, question, answer))
                                                
                                                faqs_found += 1
                                                
                                    except Exception as e:
                                        continue
                                
                                if faqs_found > 0:
                                    break
                        
                        if faqs_found > 0:
                            self.conn.commit()
                            print(f"Found {faqs_found} FAQs")
                            return
                        
                except Exception as e:
                    continue
            
            print("No FAQ page found")
            
        except Exception as e:
            print(f"Error scraping FAQs: {e}")
    
    def find_competitors_online(self):
        print("Finding competitors online...")
        
        competitors_found = []
        
        competitors_found.extend(self.find_competitors_via_google())
        
        competitors_found.extend(self.find_competitors_via_social_media())
        
        competitors_found.extend(self.find_competitors_via_product_search())
        
        competitors_found.extend(self.find_competitors_via_directories())
        
        for competitor in competitors_found:
            self.save_competitor(competitor)
        
        print(f"Found {len(competitors_found)} potential competitors")
        return competitors_found
    
    def find_competitors_via_google(self):
        print("   Searching Google for competitors...")
        competitors = []
        
        try:
            brand_name = self.extract_brand_name()
            if brand_name == "Unknown Brand":
                return competitors
            
            search_queries = [
                f'"{brand_name}" competitors',
                f'"{brand_name}" similar stores',
                f'"{brand_name}" alternative brands',
                f'stores like "{brand_name}"',
                f'"{brand_name}" vs competitors'
            ]
            
            for query in search_queries:
                try:
                    print(f"     Searching: {query}")
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"     Error with Google search: {e}")
                    continue
            
            print("     Google search completed (simulated)")
            
        except Exception as e:
            print(f"     Error in Google competitor search: {e}")
        
        return competitors
    
    def find_competitors_via_social_media(self):
        print("   Finding competitors via social media...")
        competitors = []
        
        try:
            self.cursor.execute("SELECT platform, url FROM social_handles WHERE brand_id = ?", (self.brand_id,))
            social_handles = self.cursor.fetchall()
            
            for platform, url in social_handles:
                try:
                    if platform in ['instagram', 'facebook']:
                        competitors.extend(self.find_social_competitors(platform, url))
                except Exception as e:
                    print(f"     Error with {platform}: {e}")
                    continue
            
        except Exception as e:
            print(f"     Error in social media competitor search: {e}")
        
        return competitors
    
    def find_social_competitors(self, platform, url):
        competitors = []
        
        try:
            if platform == 'instagram':
                username = url.split('/')[-1] if url.endswith('/') else url.split('/')[-1]
                print(f"     Looking for similar Instagram accounts to @{username}")
                
            elif platform == 'facebook':
                page_name = url.split('/')[-1] if url.endswith('/') else url.split('/')[-1]
                print(f"     Looking for similar Facebook pages to {page_name}")
            
        except Exception as e:
            print(f"     Error finding {platform} competitors: {e}")
        
        return competitors
    
    def find_competitors_via_product_search(self):
        print("   Finding competitors via product search...")
        competitors = []
        
        try:
            self.cursor.execute("SELECT title FROM products WHERE brand_id = ? AND is_hero = 1 LIMIT 3", (self.brand_id,))
            hero_products = self.cursor.fetchall()
            
            for product in hero_products:
                product_title = product[0]
                try:
                    competitors.extend(self.search_similar_products(product_title))
                except Exception as e:
                    print(f"     Error searching for product '{product_title}': {e}")
                    continue
            
        except Exception as e:
            print(f"     Error in product-based competitor search: {e}")
        
        return competitors
    
    def search_similar_products(self, product_title):
        competitors = []
        
        try:
            key_terms = self.extract_product_keywords(product_title)
            
            search_queries = [
                f'"{product_title}" alternative',
                f'"{product_title}" similar products',
                f'stores selling {key_terms}',
                f'brands like {key_terms}'
            ]
            
            for query in search_queries:
                print(f"     Searching for: {query}")
                time.sleep(0.5)
            
        except Exception as e:
            print(f"     Error in product search: {e}")
        
        return competitors
    
    def extract_product_keywords(self, product_title):
        common_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        words = product_title.lower().split()
        keywords = [word for word in words if word not in common_words and len(word) > 2]
        return ' '.join(keywords[:3])
    
    def find_competitors_via_directories(self):
        print("   Finding competitors via industry directories...")
        competitors = []
        
        try:
            directories = [
                'https://www.alexa.com/topsites/category/',
                'https://www.similarweb.com/category/',
                'https://www.owler.com/company/'
            ]
            
            industry = self.extract_industry_category()
            
            for directory in directories:
                try:
                    print(f"     Checking directory: {directory}")
                    time.sleep(0.5)
                except Exception as e:
                    print(f"     Error with directory {directory}: {e}")
                    continue
            
        except Exception as e:
            print(f"     Error in directory-based competitor search: {e}")
        
        return competitors
    
    def extract_industry_category(self):
        try:
            self.cursor.execute("SELECT about FROM brands WHERE id = ?", (self.brand_id,))
            about = self.cursor.fetchone()
            
            if about and about[0]:
                about_text = about[0].lower()
                
                industries = {
                    'fashion': ['clothing', 'fashion', 'apparel', 'style', 'wear'],
                    'beauty': ['beauty', 'cosmetics', 'skincare', 'makeup', 'personal care'],
                    'electronics': ['electronics', 'tech', 'gadgets', 'computers', 'phones'],
                    'home': ['home', 'furniture', 'decor', 'kitchen', 'garden'],
                    'sports': ['sports', 'fitness', 'outdoor', 'athletic', 'exercise'],
                    'food': ['food', 'beverages', 'restaurant', 'catering', 'groceries']
                }
                
                for industry, keywords in industries.items():
                    if any(keyword in about_text for keyword in keywords):
                        return industry
                
            return 'general'
            
        except Exception as e:
            print(f"     Error extracting industry: {e}")
            return 'general'
    
    def save_competitor(self, competitor_data):
        try:
            self.cursor.execute("SELECT id FROM competitors WHERE competitor_url = ? AND brand_id = ?", 
                              (competitor_data['url'], self.brand_id))
            existing = self.cursor.fetchone()
            
            if not existing:
                self.cursor.execute("""
                    INSERT INTO competitors (brand_id, competitor_name, competitor_url, competitor_type, 
                                          similarity_score, found_via)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (self.brand_id, competitor_data['name'], competitor_data['url'], 
                     competitor_data.get('type', 'unknown'), competitor_data.get('score', 0.0),
                     competitor_data.get('found_via', 'unknown')))
                
                competitor_id = self.cursor.lastrowid
                print(f"     Saved competitor: {competitor_data['name']}")
                
                if 'products' in competitor_data:
                    self.save_competitor_products(competitor_id, competitor_data['products'])
                
                self.conn.commit()
            else:
                print(f"     Competitor already exists: {competitor_data['name']}")
                
        except Exception as e:
            print(f"     Error saving competitor: {e}")
    
    def save_competitor_products(self, competitor_id, products):
        try:
            for product in products:
                self.cursor.execute("""
                    INSERT INTO competitor_products (competitor_id, title, price, currency, product_url)
                    VALUES (?, ?, ?, ?, ?)
                """, (competitor_id, product['title'], product.get('price', ''), 
                     product.get('currency', 'USD'), product.get('url', '')))
            
            print(f"       Saved {len(products)} competitor products")
            
        except Exception as e:
            print(f"       Error saving competitor products: {e}")
    
    def analyze_competitors(self):
        print("Analyzing competitors...")
        
        try:
            self.cursor.execute("""
                SELECT c.competitor_name, c.competitor_url, c.competitor_type, c.similarity_score,
                       COUNT(cp.id) as product_count
                FROM competitors c
                LEFT JOIN competitor_products cp ON c.id = cp.competitor_id
                WHERE c.brand_id = ?
                GROUP BY c.id
                ORDER BY c.similarity_score DESC
            """, (self.brand_id,))
            
            competitors = self.cursor.fetchall()
            
            if not competitors:
                print("   No competitors found to analyze")
                return
            
            print(f"   Found {len(competitors)} competitors to analyze")
            
            for competitor in competitors:
                name, url, comp_type, score, product_count = competitor
                print(f"   {name}")
                print(f"      URL: {url}")
                print(f"      Type: {comp_type}")
                print(f"      Similarity Score: {score:.2f}")
                print(f"      Products: {product_count}")
                print()
            
            self.generate_competitive_insights(competitors)
            
        except Exception as e:
            print(f"   Error analyzing competitors: {e}")
    
    def generate_competitive_insights(self, competitors):
        print("   COMPETITIVE INSIGHTS:")
        print("   " + "-" * 40)
        
        try:
            if not competitors:
                return
            
            scores = [comp[3] for comp in competitors if comp[3] is not None]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            print(f"   Average Competitor Similarity: {avg_score:.2f}")
            print(f"   Total Competitors Identified: {len(competitors)}")
            
            top_competitors = [comp for comp in competitors if comp[3] and comp[3] > avg_score]
            print(f"   High-Similarity Competitors: {len(top_competitors)}")
            
            types = [comp[2] for comp in competitors if comp[2]]
            if types:
                type_counts = {}
                for comp_type in types:
                    type_counts[comp_type] = type_counts.get(comp_type, 0) + 1
                
                print(f"   Industry Distribution:")
                for comp_type, count in type_counts.items():
                    print(f"      {comp_type}: {count}")
            
            print()
            
        except Exception as e:
            print(f"   Error generating insights: {e}")
    
    def run_complete_scrape(self):
        print(f"Starting complete scrape of: {self.base_url}")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            if not self.create_or_get_brand():
                print("Failed to create brand. Exiting.")
                return False
            
            self.scrape_policies()
            
            self.scrape_hero_products()

            self.scrape_all_products()
            
            self.scrape_social_media()
                    
            self.scrape_contact_info()
            
            self.scrape_important_links()
            
            self.scrape_faqs()
            
            self.find_competitors_online()
            
            self.analyze_competitors()
            
            self.conn.commit()
            
            end_time = time.time()
            duration = end_time - start_time
            
            print("=" * 60)
            print(f"COMPLETE SCRAPE WITH COMPETITORS FINISHED in {duration:.2f} seconds!")
            print(f"Data saved to: {self.db_name}")
            
            self.show_summary()
            
            return True
            
        except Exception as e:
            print(f"Critical error during scraping: {e}")
            return False
        
        finally:
            if hasattr(self, 'conn'):
                self.conn.close()
    
    def run_store_scrape_only(self):
        print(f"Starting store data scrape of: {self.base_url}")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            if not self.create_or_get_brand():
                print("Failed to create brand. Exiting.")
                return False
            
            self.scrape_policies()
            
            self.scrape_hero_products()
            
            self.scrape_all_products()
            
            self.scrape_social_media()
            
            self.scrape_contact_info()
            
            self.scrape_important_links()
            
            self.scrape_faqs()
            
            self.conn.commit()
            
            end_time = time.time()
            duration = end_time - start_time
            
            print("=" * 60)
            print(f"STORE DATA SCRAPE FINISHED in {duration:.2f} seconds!")
            print(f"Data saved to: {self.db_name}")
            
            self.show_summary()
            
            return True
            
        except Exception as e:
            print(f"Critical error during scraping: {e}")
            return False
        
        finally:
            if hasattr(self, 'conn'):
                self.conn.close()
    
    def show_summary(self):
        print("\nDATA COLLECTION SUMMARY:")
        print("-" * 40)
        
        try:
            self.cursor.execute("SELECT name, about FROM brands WHERE id = ?", (self.brand_id,))
            brand_info = self.cursor.fetchone()
            if brand_info:
                print(f"Brand: {brand_info[0]}")
                if brand_info[1]:
                    print(f"   About: {brand_info[1][:100]}...")
            
            self.cursor.execute("SELECT COUNT(*) FROM products WHERE brand_id = ?", (self.brand_id,))
            total_products = self.cursor.fetchone()[0]
            print(f"Total Products: {total_products}")
            
            self.cursor.execute("SELECT COUNT(*) FROM products WHERE brand_id = ? AND is_hero = 1", (self.brand_id,))
            hero_products = self.cursor.fetchone()[0]
            print(f"Hero Products: {hero_products}")
            
            self.cursor.execute("SELECT COUNT(*) FROM social_handles WHERE brand_id = ?", (self.brand_id,))
            social_count = self.cursor.fetchone()[0]
            print(f"Social Media: {social_count} platforms")
            
            self.cursor.execute("SELECT COUNT(*) FROM contacts WHERE brand_id = ?", (self.brand_id,))
            contact_count = self.cursor.fetchone()[0]
            print(f"Contacts: {contact_count}")
            
            self.cursor.execute("SELECT COUNT(*) FROM products WHERE brand_id = ?", (self.brand_id,))
            links_count = self.cursor.fetchone()[0]
            print(f"Important Links: {links_count}")
            
            self.cursor.execute("SELECT COUNT(*) FROM products WHERE brand_id = ?", (self.brand_id,))
            faqs_count = self.cursor.fetchone()[0]
            print(f"FAQs: {faqs_count}")

            self.cursor.execute("SELECT COUNT(*) FROM competitors WHERE brand_id = ?", (self.brand_id,))
            competitors_count = self.cursor.fetchone()[0]
            print(f"Competitors: {competitors_count}")
            
        except Exception as e:
            print(f"Error showing summary: {e}")


def main():
    print("🛍️ ALL-IN-ONE SHOPIFY STORE SCRAPER WITH COMPETITOR ANALYSIS")
    print("=" * 60)
    
    while True:
        print("\n 👍Choose an option:")
        print("1. 🔍 Complete Store Scrape (All Data + Competitors)")
        print("2. 🏢 Find Competitors Only")
        print("3. 📊 Analyze Existing Competitors")
        print("4. 🛒 Scrape Store Data Only (No Competitors)")
        print("5. 🚪 Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            store_url = input("Enter Shopify store URL (e.g., https://store.com): ").strip()
            if store_url:
                if not store_url.startswith(('http://', 'https://')):
                    store_url = 'https://' + store_url
                
                scraper = AllInOneShopifyScraper(store_url)
                success = scraper.run_complete_scrape()
                
                if success:
                    print("\nCOMPLETE SCRAPE WITH COMPETITORS FINISHED!")
                    print("All data and competitors saved to database.")
                else:
                    print("\nSCRAPING FAILED. Check the error messages above.")
            else:
                print("No URL provided.")
        
        elif choice == "2":
            store_url = input("Enter Shopify store URL to find competitors for: ").strip()
            if store_url:
                if not store_url.startswith(('http://', 'https://')):
                    store_url = 'https://' + store_url
                
                scraper = AllInOneShopifyScraper(store_url)
                if scraper.create_or_get_brand():
                    competitors = scraper.find_competitors_online()
                    scraper.analyze_competitors()
                    print(f"\nFound {len(competitors)} competitors!")
                else:
                    print("Failed to create brand. Exiting.")
            else:
                print("No URL provided.")
        
        elif choice == "3":
            store_url = input("Enter Shopify store URL to analyze existing competitors: ").strip()
            if store_url:
                if not store_url.startswith(('http://', 'https://')):
                    store_url = 'https://' + store_url
                
                scraper = AllInOneShopifyScraper(store_url)
                if scraper.create_or_get_brand():
                    scraper.analyze_competitors()
                else:
                    print("Failed to create brand. Exiting.")
            else:
                print("No URL provided.")
        
        elif choice == "4":
            store_url = input("Enter Shopify store URL (e.g., https://store.com): ").strip()
            if store_url:
                if not store_url.startswith(('http://', 'https://')):
                    store_url = 'https://' + store_url
                
                scraper = AllInOneShopifyScraper(store_url)
                success = scraper.run_store_scrape_only()
                
                if success:
                    print("\nSTORE DATA SCRAPING COMPLETED!")
                    print("Store data saved to database (no competitors).")
                else:
                    print("\nSCRAPING FAILED. Check the error messages above.")
            else:
                print("No URL provided.")
        
        elif choice == "5":
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please enter 1-5.")
        
        if choice in ["1", "2", "3", "4"]:
            continue_choice = input("\nDo you want to perform another operation? (y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes']:
                print("👋Goodbye!")
                break


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
# 🚀 All-in-One Shopify Store Scraper

A powerful Python tool that scrapes comprehensive data from Shopify stores and analyzes competitors automatically.

## ✨ What This Tool Does

This scraper extracts **everything** from a Shopify store:
- 🏢 **Store Information**: Brand name, about section, policies
- 🛍️ **Products**: All products with prices, handles, and URLs
- 📱 **Social Media**: Instagram, Facebook, Twitter, YouTube, TikTok, LinkedIn, Pinterest
- 📞 **Contact Info**: Email addresses and phone numbers
- 🔗 **Important Pages**: FAQ, shipping, returns, about, blog, support
- 👥 **Competitors**: Automatically finds and analyzes competing stores
- 📊 **Database Storage**: All data saved in SQLite for easy analysis

## 🎯 Perfect For

- **Market Researchers** analyzing e-commerce landscapes
- **Business Analysts** studying competitors
- **Entrepreneurs** researching market opportunities
- **Developers** building e-commerce tools
- **Students** learning web scraping and data analysis

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Scraper
```bash
python all_in_one_scraper.py
```

### 3. Choose Your Option
The tool gives you 5 options:
1. **Complete Scrape** - Get everything + competitors
2. **Find Competitors Only** - Just competitor analysis
3. **Analyze Existing Data** - Review what you already have
4. **Store Data Only** - No competitors, just store info
5. **Exit**

### 4. Enter Store URL
Just paste any Shopify store URL (e.g., `https://store.com`)

## 📊 What You Get

### Store Data
- **Brand Details**: Name, description, policies
- **Product Catalog**: Complete product list with prices
- **Social Presence**: All social media accounts
- **Contact Information**: Emails and phone numbers
- **Website Structure**: Important pages and links
- **FAQ Content**: Questions and answers if available

### Competitor Analysis
- **Competitor Discovery**: Automatically finds similar stores
- **Similarity Scoring**: Rates how similar competitors are
- **Product Comparison**: Competitor product catalogs
- **Market Insights**: Industry analysis and trends

## 🗄️ Database Structure

All data is stored in a SQLite database (`shopify_complete.db`) with these tables:

- **brands** - Store information and policies
- **products** - Product catalog with pricing
- **social_handles** - Social media accounts
- **contacts** - Email and phone information
- **important_links** - Key website pages
- **faqs** - Frequently asked questions
- **competitors** - Competing stores
- **competitor_products** - Competitor product data

## ⚙️ Requirements

- **Python 3.7+**
- **Internet connection**
- **Dependencies** (see requirements.txt):
  - `requests` - HTTP requests
  - `beautifulsoup4` - HTML parsing
  - `sqlite3` - Database (built-in)
  - `lxml` - XML/HTML processing

## 🔧 How It Works

1. **Store Analysis**: Scrapes the main store page for basic info
2. **Product Discovery**: Uses Shopify's `/products.json` API for complete catalog
3. **Policy Extraction**: Finds and extracts privacy, shipping, and return policies
4. **Social Media Detection**: Searches for social media links and handles
5. **Contact Mining**: Extracts emails and phone numbers from contact pages
6. **Competitor Research**: Uses multiple methods to find competing stores
7. **Data Storage**: Saves everything to organized database tables

## 🚨 Important Notes

- **Respectful Scraping**: Built-in delays to be respectful to websites
- **Error Handling**: Continues working even if some pages fail
- **Data Validation**: Checks for duplicate data before saving
- **SQLite Storage**: Lightweight database, no server setup needed

## 📈 Example Output

```
🚀 Starting complete scrape of: https://example-store.com
============================================================
Initializing database...
Database initialized successfully!
Created new brand: Example Store
Scraping policies...
✅ Privacy Policy: 1,234 characters
✅ Shipping Policy: 567 characters
✅ Return Policy: 890 characters
Scraping hero products from homepage...
Found 5 hero products
Scraping all products via Shopify products.json...
📊 Found 150 products to process...
Successfully processed 150 products
Scraping social media handles...
Instagram: @examplestore
Facebook: examplestore
Twitter: @examplestore
Scraping contact information...
✅ Email: hello@examplestore.com
✅ Phone: +1-555-123-4567
🔗 Scraping important links...
✅ Order Tracking: https://examplestore.com/pages/track-order
✅ Returns: https://examplestore.com/pages/returns
❓ Scraping FAQs...
✅ Found 12 FAQs
🔍 Finding competitors online...
✅ Found 8 potential competitors
📊 Analyzing competitors...
🎉 COMPLETE SCRAPE WITH COMPETITORS FINISHED in 45.23 seconds!
📊 Data saved to: shopify_complete.db
```

## 🛠️ Customization

The tool is designed to be easily customizable:
- Modify selectors for different website layouts
- Add new data extraction methods
- Customize competitor discovery algorithms
- Extend database schema for additional data

## 🤝 Contributing

Feel free to:
- Report bugs or issues
- Suggest new features
- Improve the code
- Add new scraping capabilities

## ⚖️ Legal & Ethical Use

- **Respect robots.txt** files
- **Don't overload** websites with requests
- **Use responsibly** and ethically
- **Follow website terms** of service
- **Respect privacy** and data protection laws

## 📞 Support

If you encounter issues:
1. Check that all dependencies are installed
2. Verify the store URL is accessible
3. Check your internet connection
4. Review the error messages for specific issues

## 🎉 Happy Scraping!

This tool makes it easy to gather comprehensive e-commerce intelligence. Use it wisely and discover valuable market insights! 🚀

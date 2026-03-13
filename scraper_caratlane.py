import os
import time
import django
import random
import re
from bs4 import BeautifulSoup

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preference_site.settings')
django.setup()

from preference_app.models import JewelryCatalog

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("Please install selenium and webdriver_manager: pip install selenium webdriver-manager")
    exit(1)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def clean_price(price_str):
    """Convert a price string like '₹ 15,000' to an integer 15000."""
    try:
        clean_str = re.sub(r'[^\d]', '', price_str)
        return int(clean_str) if clean_str else 0
    except Exception:
        return 0

def guess_attributes(name, item_type):
    """Heuristic logic to guess style, material, occasion, aesthetic if missing."""
    name_lower = f"{name} {item_type}".lower()
    
    # Material
    if "gold" in name_lower or "22kt" in name_lower or "18kt" in name_lower:
        material = "Gold"
    elif "diamond" in name_lower:
        material = "Diamond"
    elif "platinum" in name_lower:
        material = "Platinum"
    elif "silver" in name_lower:
        material = "Silver"
    else:
        material = random.choice(["Gold", "Diamond", "Alloy"])

    # Style
    if "stud" in name_lower or "minimal" in name_lower or "simple" in name_lower:
        style = "Minimalist"
    elif "drop" in name_lower or "dangle" in name_lower or "long" in name_lower:
        style = "Elegant"
    elif "statement" in name_lower or "heavy" in name_lower or "choker" in name_lower:
        style = "Statement"
    else:
        style = random.choice(["Classic", "Modern", "Minimalist", "Bold"])

    # Occasion
    if "bridal" in name_lower or "wedding" in name_lower:
        occasion = "Bridal"
    elif "party" in name_lower:
        occasion = "Party"
    elif style in ["Minimalist", "Simple"]:
        occasion = "Everyday"
    else:
        occasion = random.choice(["Everyday", "Party", "Casual", "Formal"])

    # Aesthetic
    if "traditional" in name_lower or "antique" in name_lower or "temple" in name_lower:
        aesthetic = "Traditional"
    elif "modern" in name_lower or "abstract" in name_lower:
        aesthetic = "Modern"
    else:
        aesthetic = random.choice(["Classic", "Trendy", "Vintage", "Boho"])

    return style, material, occasion, aesthetic

def scrape_caratlane():
    print("Starting CaratLane Scraper...")
    driver = setup_driver()
    
    # Target URLs
    urls = [
        ("Ring", "https://www.caratlane.us/jewellery/rings.html"),
        ("Earring", "https://www.caratlane.us/jewellery/earrings.html"),
        ("Necklace", "https://www.caratlane.us/jewellery/necklaces.html")
    ]
    
    total_added = 0
    
    for item_type, url in urls:
        print(f"Scraping {item_type}s from {url}...")
        driver.get(url)
        time.sleep(5)  # Wait for initial load
        
        # Scroll down to load lazy images and more products
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Caratlane product cards are usually inside 'li.item.product.product-item'
        products = soup.select('li.item.product.product-item')
        print(f"Found {len(products)} products on page.")
        
        for product in products:
            try:
                # Extract Name
                name_elem = product.select_one('.product-item-link, .product.name a')
                name = name_elem.text.strip() if name_elem else "Unknown Product"
                
                # Extract URL
                link = name_elem['href'] if name_elem and name_elem.has_attr('href') else url
                
                # Extract Price
                price_elem = product.select_one('.price')
                price_str = price_elem.text.strip() if price_elem else "0"
                price = clean_price(price_str)
                
                # Extract Image
                img_elem = product.select_one('img.product-image-photo')
                image_url = ""
                if img_elem:
                    if img_elem.has_attr('src') and 'placeholder' not in img_elem['src']:
                        image_url = img_elem['src']
                    elif img_elem.has_attr('data-src'):
                        image_url = img_elem['data-src']
                
                if not image_url or "loader" in image_url:
                    continue # Skip products without real images
                
                # Skip if empty name or price 0
                if name == "Unknown Product" or price == 0:
                    continue
                    
                # Prevent duplicates
                if JewelryCatalog.objects.filter(name=name, item_type=item_type).exists():
                    continue

                style, material, occasion, aesthetic = guess_attributes(name, item_type)
                
                JewelryCatalog.objects.create(
                    name=name,
                    item_type=item_type,
                    style=style,
                    material=material,
                    occasion=occasion,
                    aesthetic=aesthetic,
                    price=price,
                    image_url=image_url,
                    product_link=link
                )
                total_added += 1
                
                if total_added % 10 == 0:
                    print(f"Added {total_added} items...")
                    
            except Exception as e:
                print(f"Error parsing product: {e}")
                
    driver.quit()
    print(f"Scraping completed. Total new items added: {total_added}")
    print(f"Current DB Catalog Total: {JewelryCatalog.objects.count()}")

if __name__ == "__main__":
    scrape_caratlane()

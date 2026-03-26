"""
MoneyControl & GoldAPI Integration Service
Provides live metal prices and jewelry/metal news.
- Prices: Primary from GoldAPI.io (with 12h persistent cache), fallback to MoneyControl/Local HTML.
- News: Filtered from MoneyControl.
"""

import time
import logging
import requests
import random
import os
import json
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────────────────
PRICE_CACHE_FILE = os.path.join("/tmp", "metal_prices_cache.json")

# ── API Keys (from environment) ──────────────────────────────────────────────
GOLDAPI_KEY = os.getenv("GOLDAPI_KEY", "")

# ── Cache TTL ────────────────────────────────────────────────────────────────
PRICE_CACHE_TTL = 43200  # 12 hours (2 calls per day)
NEWS_CACHE_TTL = 300     # 5 minutes (in-memory)

# ── In-Memory Cache for News ─────────────────────────────────────────────────
_news_cache = {"data": None, "timestamp": 0}

# ── Fallback Data ────────────────────────────────────────────────────────────
FALLBACK_PRICES = {
    "gold_24k": {"name": "Gold 24K", "price": "87,340", "change": "+0.4%", "direction": "up", "unit": "per 10g"},
    "gold_22k": {"name": "Gold 22K", "price": "80,060", "change": "+0.4%", "direction": "up", "unit": "per 10g"},
    "silver":   {"name": "Silver",   "price": "97,200", "change": "-0.2%", "direction": "down", "unit": "per 1kg"},
    "platinum": {"name": "Platinum", "price": "28,450", "change": "+0.1%", "direction": "up", "unit": "per 10g"},
}


def get_headers():
    """Return realistic headers for MoneyControl scraping."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    ]
    return {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.7",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


# ── GoldAPI.io Integration ───────────────────────────────────────────────

def _fetch_from_goldapi():
    """Fetch gold and silver prices from GoldAPI.io."""
    headers = {
        "x-access-token": GOLDAPI_KEY,
        "Content-Type": "application/json"
    }
    
    results = {}
    
    # Symbols to fetch
    symbols = {
        "XAU": "gold_24k",
        "XAG": "silver",
        "XPT": "platinum"
    }
    
    for symbol, key in symbols.items():
        try:
            url = f"https://www.goldapi.io/api/{symbol}/INR"
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                
                # Preferred: use per-gram prices if available (very accurate)
                pg_24k = data.get("price_gram_24k")
                pg_22k = data.get("price_gram_22k")
                base_price = data.get("price", 0)
                change = data.get("chp", 0.0)
                
                if symbol == "XAU":
                    # Gold 24K (per 10g)
                    price_10g_24k = (pg_24k * 10) if pg_24k else (base_price / 31.1035 * 10)
                    results["gold_24k"] = {
                        "name": "Gold 24K",
                        "price": f"{price_10g_24k:,.0f}",
                        "change": f"{'+' if change >= 0 else ''}{change}%",
                        "direction": "up" if change >= 0 else "down",
                        "unit": "per 10g"
                    }
                    # Gold 22K (per 10g)
                    price_10g_22k = (pg_22k * 10) if pg_22k else (price_10g_24k * 0.9167)
                    results["gold_22k"] = {
                        "name": "Gold 22K",
                        "price": f"{price_10g_22k:,.0f}",
                        "change": f"{'+' if change >= 0 else ''}{change}%",
                        "direction": "up" if change >= 0 else "down",
                        "unit": "per 10g"
                    }
                elif symbol == "XAG":
                    # Silver (per 1kg)
                    price_1kg = (base_price / 31.1035 * 1000)
                    results["silver"] = {
                        "name": "Silver",
                        "price": f"{price_1kg:,.0f}",
                        "change": f"{'+' if change >= 0 else ''}{change}%",
                        "direction": "up" if change >= 0 else "down",
                        "unit": "per 1kg"
                    }
                elif symbol == "XPT":
                    # Platinum (per 10g)
                    price_10g_pt = (base_price / 31.1035 * 10)
                    results["platinum"] = {
                        "name": "Platinum",
                        "price": f"{price_10g_pt:,.0f}",
                        "change": f"{'+' if change >= 0 else ''}{change}%",
                        "direction": "up" if change >= 0 else "down",
                        "unit": "per 10g"
                    }
                    
            time.sleep(1) # Be nice to the API
        except Exception as e:
            logger.warning(f"GoldAPI fetch failed for {symbol}: {e}")
            
    return results


# ── MoneyControl Scraping Fallback ───────────────────────────────────────────

def _parse_html_for_prices(soup, url_hint=""):
    """Heuristic to find prices in any MoneyControl-like HTML."""
    prices = {}
    rows = soup.select("table tr")
    for row in rows:
        text = row.get_text(separator=" ", strip=True).lower()
        cells = row.find_all(["td", "th"])
        if len(cells) >= 2:
            val_text = cells[1].get_text(strip=True).replace("₹", "").replace(",", "").strip()
            if not any(c.isdigit() for c in val_text): continue
            
            try:
                val_float = float(val_text)
                if val_float < 1000: continue 
                
                change = cells[2].get_text(strip=True) if len(cells) > 2 else "+0.0%"
                direction = "down" if "-" in change else "up"
                display_price = f"{val_float:,.0f}"

                if ("24k" in text or "24 k" in text) and "gold_24k" not in prices:
                    prices["gold_24k"] = {"name": "Gold 24K", "price": display_price, "change": change, "direction": direction, "unit": "per 10g"}
                elif ("22k" in text or "22 k" in text) and "gold_22k" not in prices:
                    prices["gold_22k"] = {"name": "Gold 22K", "price": display_price, "change": change, "direction": direction, "unit": "per 10g"}
                elif "silver" in text and "silver" not in prices:
                    prices["silver"] = {"name": "Silver", "price": display_price, "change": change, "direction": direction, "unit": "per 1kg"}
                elif "platinum" in text and "platinum" not in prices:
                    prices["platinum"] = {"name": "Platinum", "price": display_price, "change": change, "direction": direction, "unit": "per 10g"}
            except ValueError:
                continue
    return prices


def _scrape_moneycontrol_prices():
    prices = {}
    urls = ["https://www.moneycontrol.com/commodity/gold-price.html", "https://www.moneycontrol.com/commodity/silver-price.html"]
    for url in urls:
        try:
            resp = requests.get(url, headers=get_headers(), timeout=10)
            if resp.status_code == 200:
                prices.update(_parse_html_for_prices(BeautifulSoup(resp.text, "html.parser")))
        except: pass

    return prices


# ── Main Entry Point with 12h Cache ──────────────────────────────────────────

def get_live_metal_prices():
    """Get live prices with 12h persistent cache and 2-calls-daily limit."""
    now = time.time()
    
    # 1. Try to load from persistent cache
    cached_data = None
    if os.path.exists(PRICE_CACHE_FILE):
        try:
            with open(PRICE_CACHE_FILE, "r") as f:
                cached_data = json.load(f)
                
            last_fetch = cached_data.get("timestamp", 0)
            # If cache is valid (less than 12 hours old)
            if (now - last_fetch) < PRICE_CACHE_TTL:
                return cached_data.get("prices", FALLBACK_PRICES)
        except Exception as e:
            logger.warning(f"Cache load failed: {e}")

    # 2. Cache is stale or missing, fetch from GoldAPI
    logger.info("Persistent cache stale or missing. Fetching from GoldAPI...")
    new_prices = _fetch_from_goldapi()
    
    # 3. If GoldAPI failed or returned incomplete data, try MoneyControl
    if not new_prices:
        logger.info("GoldAPI failed. Trying MoneyControl fallback...")
        new_prices = _scrape_moneycontrol_prices()

    # 4. Merge with fallback and update persistent cache
    result = dict(FALLBACK_PRICES)
    for k, v in new_prices.items():
        if v and v.get('price'):
            result[k] = v
            
    # Save to persistent cache
    try:
        with open(PRICE_CACHE_FILE, "w") as f:
            json.dump({"timestamp": now, "prices": result}, f)
        logger.info(f"Updated persistent cache: {PRICE_CACHE_FILE}")
    except Exception as e:
        logger.error(f"Cache save failed: {e}")
        
    return result


# ── Live News (In-Memory Only) ───────────────────────────────────────────────

METAL_KEYWORDS = ["gold", "silver", "platinum", "jewel", "jewellery", "jewelry", "bullion", "mcx", "diamond", "gem", "titan", "tanishq"]

def _extract_news_from_soup(soup):
    items = []
    for art in soup.select("li.clearfix, .newslist"):
        title_tag = art.select_one("h2 a, h3 a, .related_des a")
        if title_tag:
            title = title_tag.get_text(strip=True)
            link = title_tag.get("href", "#")
            if not link.startswith("http"): link = "https://www.moneycontrol.com" + link
            date_tag = art.select_one("span.list_dt, p.related_date, .date")
            date = date_tag.get_text(strip=True) if date_tag else ""
            if any(kw in title.lower() for kw in METAL_KEYWORDS):
                items.append({"title": title, "link": link, "date": date})
    return items

def get_jewelry_metal_news():
    now = time.time()
    if _news_cache["data"] and (now - _news_cache["timestamp"]) < NEWS_CACHE_TTL:
        return _news_cache["data"]

    news_items = []
    urls = ["https://www.moneycontrol.com/news/business/commodities/", "https://www.moneycontrol.com/news/tags/gold.html"]
    for url in urls:
        try:
            resp = requests.get(url, headers=get_headers(), timeout=10)
            if resp.status_code == 200:
                news_items.extend(_extract_news_from_soup(BeautifulSoup(resp.text, "html.parser")))
                if len(news_items) >= 5: break
        except: pass

    seen = set()
    unique_news = [i for i in news_items if not (i['title'] in seen or seen.add(i['title']))]
    
    if not unique_news:
        unique_news = [{"title": "Gold Prices Steady Amid Global Economic Shifts", "link": "#", "date": "Live"}]

    _news_cache["data"] = unique_news[:10]
    _news_cache["timestamp"] = now
    return unique_news[:10]

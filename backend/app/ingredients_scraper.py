"""
Ingredients Scraper — Open Food Facts + iHerb
==============================================
Scrapes ingredient lists for specialty Asian grocery & health products
from two sources:
  1. Open Food Facts API  (free, no auth, best for packaged foods)
  2. iHerb.com            (BeautifulSoup, best for herbal/supplement items)

Products are loaded dynamically from POP xlsx files in pop_data/.
Results are merged and exported to a single CSV with source attribution.

Dependencies:
    pip install beautifulsoup4 requests pandas openpyxl

Usage:
    python ingredients_scraper.py
    python ingredients_scraper.py --output ingredients_export.csv
    python ingredients_scraper.py --skip-iherb    # Open Food Facts only
    python ingredients_scraper.py --skip-off      # iHerb only

Folder structure expected:
    your_project/
    ├── ingredients_scraper.py
    └── pop_data/
        ├── POP_ItemSpecMaster.xlsx
        └── POP_InventorySnapshot.xlsx   (optional)
"""

import re
import time
import random
import argparse
import logging
import os
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

import requests
import pandas as pd
from bs4 import BeautifulSoup
from dynamic_family_extractor import DynamicFamilyExtractor

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
POP_DATA_DIR = Path("pop_data")

# Dynamic family extractor - replaces hardcoded INFER_RULES
DYNAMIC_EXTRACTOR = DynamicFamilyExtractor()

# Get category sources from dynamic extractor
CATEGORY_SOURCES = DYNAMIC_EXTRACTOR.get_category_sources()

# Flavor/variant keywords to append to the base search query when found
# in the description, so iHerb/OFF searches are product-specific.
FLAVOR_KEYWORDS = [
    "original", "lemon", "mango", "lychee", "pineapple", "coconut",
    "blood orange", "assorted", "turmeric", "jasmine", "oolong",
    "white", "green", "extra strength", "ultra strength",
    "hazelnut", "cappuccino", "dark", "noisette", "orange",
]

SIZE_RE = re.compile(r"(?<!\d)(\d+(?:\.\d+)?\s*(?:oz|lb|g|bags?|pcs?|ct|pc))\b", re.I)


# ── User-Agent Pool ───────────────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]


# ═════════════════════════════════════════════════════════════════════════════
# Step 1 — Load products from POP xlsx and build the PRODUCTS list
# ═════════════════════════════════════════════════════════════════════════════

def load_products() -> list[dict]:
    """
    Load products using dynamic family extraction from POP xlsx files.
    Returns a PRODUCTS-style list of dicts ready for scraping.
    """
    log.info("Loading products with dynamic family extraction...")
    
    # Use the dynamic extractor to build products list
    products = DYNAMIC_EXTRACTOR.build_products_list()
    
    log.info(f"  ↳ {len(products)} products loaded across "
             f"{len({p['category'] for p in products})} families")
    return products


# ═════════════════════════════════════════════════════════════════════════════
# Step 2 — Open Food Facts Scraper
# ═════════════════════════════════════════════════════════════════════════════

class OpenFoodFactsScraper:
    """
    Uses the Open Food Facts public API — no auth, no scraping, never blocked.
    Docs: https://wiki.openfoodfacts.org/API
    """

    SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"

    def __init__(self, delay: float = 1.0, cache_dir: str = "cache", cache_hours: int = 24):
        self.delay = delay
        self.cache_dir = cache_dir
        self.cache_hours = cache_hours
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)

    def search(self, query: str) -> Optional[dict]:
        """Search OFF and return the best-matching product dict, or None."""
        params = {
            "search_terms":   query,
            "search_simple":  1,
            "action":         "process",
            "json":           1,
            "page_size":      5,
            "fields":         "product_name,ingredients_text,ingredients_text_en,"
                              "brands,categories,quantity,countries,code",
        }
        try:
            time.sleep(self.delay)
            resp = requests.get(
                self.SEARCH_URL, params=params, timeout=12,
                headers={"User-Agent": "IngredientsScraper/1.0 (research)"},
            )
            resp.raise_for_status()
            products = resp.json().get("products", [])
            if not products:
                return None
            # Prefer results that actually have ingredients
            for p in products:
                if p.get("ingredients_text_en") or p.get("ingredients_text"):
                    return p
            return products[0]
        except Exception as exc:
            log.warning(f"    ↳ OFF search failed for '{query}': {exc}")
            return None

    @staticmethod
    def _clean(text: str) -> str:
        return re.sub(r"\s{2,}", " ", text).strip()

    def scrape_product(self, name: str, query: str, category: str) -> dict:
        log.info(f"  [OFF] {name}")
        product = self.search(query)
        if not product:
            return _empty_row(name, category, "Open Food Facts", query, "no results")

        raw = (product.get("ingredients_text_en") or
               product.get("ingredients_text") or "").strip()
        ingredients = self._clean(raw)

        return {
            "scraped_at":        datetime.now().isoformat(),
            "product_name":      name,
            "category":          category,
            "source":            "Open Food Facts",
            "search_query":      query,
            "matched_title":     product.get("product_name", "")[:120],
            "brand":             product.get("brands", ""),
            "quantity":          product.get("quantity", ""),
            "ingredients":       ingredients,
            "ingredients_found": bool(ingredients),
            "off_barcode":       product.get("code", ""),
            "notes":             "",
        }

    def _get_cache_filename(self) -> str:
        """Generate cache filename for Open Food Facts data."""
        return os.path.join(self.cache_dir, "open_food_facts_cache.csv")

    def _is_cache_valid(self, cache_path: str) -> bool:
        """Check if cache file exists and is within the validity period."""
        if not os.path.exists(cache_path):
            return False
        
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        expiry_time = datetime.now() - timedelta(hours=self.cache_hours)
        
        return file_time > expiry_time

    def _load_from_cache(self, products: list[dict]) -> Optional[list[dict]]:
        """Load Open Food Facts data from cache if valid."""
        cache_path = self._get_cache_filename()
        
        if not self._is_cache_valid(cache_path):
            log.info("Open Food Facts cache not found or expired, will fetch fresh data")
            return None
        
        try:
            log.info(f"Loading Open Food Facts data from cache: {cache_path}")
            df = pd.read_csv(cache_path)
            
            # Filter cached data for current products
            cached_rows = []
            product_names = [p["name"] for p in products if p.get("off_query")]
            
            for _, row in df.iterrows():
                if row.get("product_name") in product_names:
                    cached_rows.append(row.to_dict())
            
            log.info(f"✓ Loaded {len(cached_rows)} Open Food Facts rows from cache")
            return cached_rows
            
        except Exception as exc:
            log.warning(f"Failed to load Open Food Facts from cache: {exc}")
            return None

    def _save_to_cache(self, rows: list[dict]) -> None:
        """Save Open Food Facts data to cache file."""
        cache_path = self._get_cache_filename()
        
        try:
            log.info(f"Saving Open Food Facts data to cache: {cache_path}")
            df = pd.DataFrame(rows)
            df.to_csv(cache_path, index=False, encoding="utf-8-sig")
            log.info("✓ Open Food Facts data cached successfully")
        except Exception as exc:
            log.warning(f"Failed to save Open Food Facts to cache: {exc}")

    def scrape_all(self, products: list[dict], force_refresh: bool = False) -> list[dict]:
        rows = []
        items = [p for p in products if p.get("off_query")]
        log.info(f"Open Food Facts: scraping {len(items)} products...")
        
        # Try to load from cache unless force refresh is requested
        if not force_refresh:
            cached_data = self._load_from_cache(products)
            if cached_data is not None:
                # Add missing products that weren't in cache
                cached_names = {row.get("product_name") for row in cached_data}
                missing_items = [p for p in items if p["name"] not in cached_names]
                
                if missing_items:
                    log.info(f"Fetching {len(missing_items)} missing products from API...")
                    for p in missing_items:
                        rows.append(self.scrape_product(p["name"], p["off_query"], p["category"]))
                    
                    # Update cache with new data
                    all_rows = cached_data + rows
                    self._save_to_cache(all_rows)
                    return all_rows
                else:
                    log.info("Using cached Open Food Facts data (use --force-refresh to fetch fresh data)")
                    return cached_data
        
        # Fetch fresh data
        for p in items:
            rows.append(self.scrape_product(p["name"], p["off_query"], p["category"]))
        
        # Save fresh data to cache
        self._save_to_cache(rows)
        return rows


# ═════════════════════════════════════════════════════════════════════════════
# Step 3 — iHerb Scraper
# ═════════════════════════════════════════════════════════════════════════════

class iHerbScraper:
    """
    Scrapes ingredient lists from iHerb.com product pages using BeautifulSoup.
    iHerb is much more scraper-friendly than Amazon.
    """

    SEARCH_URL = "https://www.iherb.com/search?kw={query}"
    BASE_URL   = "https://www.iherb.com"

    def __init__(self, delay: float = 2.5, cache_dir: str = "cache", cache_hours: int = 24):
        self.delay   = delay
        self.cache_dir = cache_dir
        self.cache_hours = cache_hours
        self.session = requests.Session()
        self.session.headers.update(self._headers())
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)

    @staticmethod
    def _headers() -> dict:
        return {
            "User-Agent":      random.choice(USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection":      "keep-alive",
        }

    def _get(self, url: str) -> Optional[BeautifulSoup]:
        time.sleep(random.uniform(self.delay * 0.8, self.delay * 1.3))
        self.session.headers.update(self._headers())
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, "html.parser")
            log.warning(f"    ↳ iHerb HTTP {resp.status_code} for {url}")
        except requests.RequestException as exc:
            log.warning(f"    ↳ iHerb request error: {exc}")
        return None

    def _search_first_url(self, query: str) -> Optional[str]:
        url  = self.SEARCH_URL.format(query=requests.utils.quote(query))
        soup = self._get(url)
        if not soup:
            return None
        for sel in [
            "a.absolute-link.product-link",
            "div.product-cell a[href*='/pr/']",
            ".product-title a",
            "a[href*='iherb.com/pr/']",
        ]:
            link = soup.select_one(sel)
            if link and link.get("href"):
                href = link["href"]
                return (self.BASE_URL + href) if href.startswith("/") else href
        for a in soup.find_all("a", href=True):
            if "/pr/" in a["href"]:
                href = a["href"]
                return (self.BASE_URL + href) if href.startswith("/") else href
        return None

    def _parse_ingredients(self, soup: BeautifulSoup) -> tuple[str, str]:
        title = ""
        title_el = soup.select_one("h1.product-name, h1[itemprop='name'], .product-title h1")
        if title_el:
            title = title_el.get_text(strip=True)[:120]

        ingredients = ""

        # Strategy 1: dedicated ingredients section/tab
        for sel in ["#tab-ingredients", "[data-tab='ingredients']",
                    ".ingredients-content", "section.ingredients"]:
            el = soup.select_one(sel)
            if el:
                ingredients = el.get_text(" ", strip=True)
                break

        # Strategy 2: heading "Ingredients" followed by sibling content
        if not ingredients:
            for heading in soup.find_all(["h2", "h3", "h4", "strong", "b"]):
                if heading.get_text(strip=True).lower() in (
                    "ingredients", "ingredient", "other ingredients",
                    "supplement facts", "active ingredients"
                ):
                    sibling = heading.find_next_sibling()
                    if sibling:
                        ingredients = sibling.get_text(" ", strip=True)
                    elif heading.parent:
                        ingredients = heading.parent.get_text(" ", strip=True)
                    if ingredients:
                        break

        # Strategy 3: scan for "Ingredients:" label in block elements
        if not ingredients:
            for el in soup.find_all(["p", "div", "li", "span"]):
                txt = el.get_text(" ", strip=True)
                if re.match(r"^ingredients\s*:", txt, re.I) and len(txt) > 20:
                    ingredients = txt
                    break

        ingredients = re.sub(r"\s{2,}", " ", ingredients).strip()
        ingredients = re.sub(r"^ingredients\s*:\s*", "", ingredients, flags=re.I)
        return ingredients, title

    def scrape_product(self, name: str, query: str, category: str) -> dict:
        log.info(f"  [iHerb] {name}")
        url = self._search_first_url(query)
        if not url:
            return _empty_row(name, category, "iHerb", query, "no search result")

        soup = self._get(url)
        if not soup:
            return _empty_row(name, category, "iHerb", query, "page fetch failed")

        ingredients, page_title = self._parse_ingredients(soup)
        return {
            "scraped_at":        datetime.now().isoformat(),
            "product_name":      name,
            "category":          category,
            "source":            "iHerb",
            "search_query":      query,
            "matched_title":     page_title,
            "brand":             "",
            "quantity":          "",
            "ingredients":       ingredients,
            "ingredients_found": bool(ingredients),
            "off_barcode":       "",
            "notes":             url[:200],
        }

    def _get_cache_filename(self) -> str:
        """Generate cache filename for iHerb data."""
        return os.path.join(self.cache_dir, "iherb_cache.csv")

    def _is_cache_valid(self, cache_path: str) -> bool:
        """Check if cache file exists and is within the validity period."""
        if not os.path.exists(cache_path):
            return False
        
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        expiry_time = datetime.now() - timedelta(hours=self.cache_hours)
        
        return file_time > expiry_time

    def _load_from_cache(self, products: list[dict]) -> Optional[list[dict]]:
        """Load iHerb data from cache if valid."""
        cache_path = self._get_cache_filename()
        
        if not self._is_cache_valid(cache_path):
            log.info("iHerb cache not found or expired, will fetch fresh data")
            return None
        
        try:
            log.info(f"Loading iHerb data from cache: {cache_path}")
            df = pd.read_csv(cache_path)
            
            # Filter cached data for current products
            cached_rows = []
            product_names = [p["name"] for p in products if p.get("iherb_query")]
            
            for _, row in df.iterrows():
                if row.get("product_name") in product_names:
                    cached_rows.append(row.to_dict())
            
            log.info(f"✓ Loaded {len(cached_rows)} iHerb rows from cache")
            return cached_rows
            
        except Exception as exc:
            log.warning(f"Failed to load iHerb from cache: {exc}")
            return None

    def _save_to_cache(self, rows: list[dict]) -> None:
        """Save iHerb data to cache file."""
        cache_path = self._get_cache_filename()
        
        try:
            log.info(f"Saving iHerb data to cache: {cache_path}")
            df = pd.DataFrame(rows)
            df.to_csv(cache_path, index=False, encoding="utf-8-sig")
            log.info("✓ iHerb data cached successfully")
        except Exception as exc:
            log.warning(f"Failed to save iHerb to cache: {exc}")

    def scrape_all(self, products: list[dict], force_refresh: bool = False) -> list[dict]:
        rows = []
        items = [p for p in products if p.get("iherb_query")]
        log.info(f"iHerb: scraping {len(items)} products...")
        
        # Try to load from cache unless force refresh is requested
        if not force_refresh:
            cached_data = self._load_from_cache(products)
            if cached_data is not None:
                # Add missing products that weren't in cache
                cached_names = {row.get("product_name") for row in cached_data}
                missing_items = [p for p in items if p["name"] not in cached_names]
                
                if missing_items:
                    log.info(f"Fetching {len(missing_items)} missing products from iHerb...")
                    for p in missing_items:
                        rows.append(self.scrape_product(p["name"], p["iherb_query"], p["category"]))
                    
                    # Update cache with new data
                    all_rows = cached_data + rows
                    self._save_to_cache(all_rows)
                    return all_rows
                else:
                    log.info("Using cached iHerb data (use --force-refresh to fetch fresh data)")
                    return cached_data
        
        # Fetch fresh data
        for p in items:
            rows.append(self.scrape_product(p["name"], p["iherb_query"], p["category"]))
        
        # Save fresh data to cache
        self._save_to_cache(rows)
        return rows


# ═════════════════════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════════════════════

def _empty_row(name: str, category: str, source: str, query: str, note: str) -> dict:
    return {
        "scraped_at": datetime.now().isoformat(),
        "product_name": name, "category": category,
        "source": source, "search_query": query,
        "matched_title": "", "brand": "", "quantity": "",
        "ingredients": "", "ingredients_found": False,
        "off_barcode": "", "notes": note,
    }


def merge_results(off_rows: list[dict], iherb_rows: list[dict]) -> pd.DataFrame:
    """
    Combine OFF and iHerb rows. Within each product, rows that have
    ingredients sort before rows that don't. Exact duplicate rows are dropped.
    """
    all_rows = off_rows + iherb_rows
    if not all_rows:
        return pd.DataFrame()
    df = pd.DataFrame(all_rows)
    df["_rank"] = df["ingredients_found"].apply(lambda x: 0 if x else 1)
    df = (df.sort_values(["product_name", "_rank"])
            .drop(columns=["_rank"])
            .drop_duplicates()
            .reset_index(drop=True))
    return df


# ═════════════════════════════════════════════════════════════════════════════
# Export
# ═════════════════════════════════════════════════════════════════════════════

COLUMNS = [
    "product_name", "category", "source", "ingredients_found",
    "ingredients", "matched_title", "brand", "quantity",
    "search_query", "off_barcode", "notes", "scraped_at",
]

def export_csv(df: pd.DataFrame, path: str) -> None:
    if df.empty:
        log.warning("No data to export.")
        return
    ordered = [c for c in COLUMNS if c in df.columns]
    extras  = [c for c in df.columns if c not in ordered]
    df[ordered + extras].to_csv(path, index=False, encoding="utf-8-sig")
    found = df["ingredients_found"].sum()
    total = len(df)
    log.info(f"✓ CSV written → {path}")
    log.info(f"  {found}/{total} rows have ingredients ({round(found/total*100)}% fill rate)")


# ═════════════════════════════════════════════════════════════════════════════
# Main
# ═════════════════════════════════════════════════════════════════════════════

def main(args: argparse.Namespace) -> None:
    log.info("=" * 60)
    log.info(" Ingredients Scraper — Open Food Facts + iHerb")
    log.info("=" * 60)

    products   = load_products()
    off_rows    = []
    iherb_rows  = []

    if not args.skip_off:
        scraper    = OpenFoodFactsScraper(delay=args.off_delay, cache_dir=args.cache_dir, cache_hours=args.cache_hours)
        off_rows   = scraper.scrape_all(products, force_refresh=args.force_refresh)
    else:
        log.info("Skipping Open Food Facts (--skip-off)")

    if not args.skip_iherb:
        scraper    = iHerbScraper(delay=args.iherb_delay, cache_dir=args.cache_dir, cache_hours=args.cache_hours)
        iherb_rows = scraper.scrape_all(products, force_refresh=args.force_refresh)
    else:
        log.info("Skipping iHerb (--skip-iherb)")

    df = merge_results(off_rows, iherb_rows)

    if not df.empty:
        log.info("\n── Coverage by Category ────────────────────────────────")
        summary = (df.groupby("category")["ingredients_found"]
                     .agg(["sum", "count"])
                     .rename(columns={"sum": "found", "count": "total"}))
        summary["pct"] = (summary["found"] / summary["total"] * 100).round(0).astype(int)
        for cat, row in summary.iterrows():
            bar = "█" * (row["pct"] // 10) + "░" * (10 - row["pct"] // 10)
            log.info(f"  {cat:<30} {bar}  {row['found']}/{row['total']}  ({row['pct']}%)")
        log.info("")

    export_csv(df, args.output)

    log.info("=" * 60)
    log.info("Done.")
    log.info("=" * 60)

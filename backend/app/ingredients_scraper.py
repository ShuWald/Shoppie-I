"""
Ingredients Scraper — Open Food Facts + iHerb
==============================================
Scrapes ingredient lists for specialty Asian grocery & health products
from two sources:
  1. Open Food Facts API  (free, no auth, best for packaged foods)
  2. iHerb.com            (BeautifulSoup, best for herbal/supplement items)

Results are merged and exported to a single CSV with source attribution.

Dependencies:
    pip install beautifulsoup4 requests pandas

Usage:
    python ingredients_scraper.py
    python ingredients_scraper.py --output ingredients_export.csv
    python ingredients_scraper.py --skip-iherb    # Open Food Facts only
    python ingredients_scraper.py --skip-off      # iHerb only
"""

import re
import time
import random
import argparse
import logging
from datetime import datetime
from typing import Optional

import requests
import pandas as pd
from bs4 import BeautifulSoup

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Product List ──────────────────────────────────────────────────────────────
# Each entry:
#   name        → your internal product name
#   off_query   → search term for Open Food Facts (None = skip OFF for this item)
#   iherb_query → search term for iHerb           (None = skip iHerb for this item)
#   category    → product family for grouping in export

PRODUCTS = [
    # ── American Ginseng ──────────────────────────────────────────────────────
    {"name": "AM GSG Root (Mixed) 1 lb Bag",        "category": "American Ginseng",      "off_query": "American ginseng root",              "iherb_query": "american ginseng root 1lb"},
    {"name": "AM GSG Root (Mixed) 4 oz Bag",        "category": "American Ginseng",      "off_query": "American ginseng root",              "iherb_query": "american ginseng root 4oz"},
    {"name": "AM GSG Root (Mixed) 8 oz Bag",        "category": "American Ginseng",      "off_query": "American ginseng root",              "iherb_query": "american ginseng root 8oz"},
    {"name": "AM GSG Slices 3 oz Jumbo",            "category": "American Ginseng",      "off_query": "American ginseng slices",            "iherb_query": "american ginseng slices"},
    {"name": "AM GSG Slices 6 oz Jumbo",            "category": "American Ginseng",      "off_query": "American ginseng slices",            "iherb_query": "american ginseng slices 6oz"},
    {"name": "AM GSG Root Slices 9 oz",             "category": "American Ginseng",      "off_query": "American ginseng root slices",       "iherb_query": "american ginseng root slices 9oz"},
    {"name": "Wild AM GSG Instant Tea",             "category": "American Ginseng",      "off_query": "American ginseng instant tea",       "iherb_query": "wild american ginseng instant tea"},
    {"name": "AM GSG Candy 1 lb Bag",               "category": "American Ginseng",      "off_query": "American ginseng candy",             "iherb_query": "american ginseng candy"},
    {"name": "AM GSG Candy 6 oz Bag",               "category": "American Ginseng",      "off_query": "American ginseng candy",             "iherb_query": "american ginseng candy 6oz"},
    {"name": "AM GSG RT Tea 20 Bags",               "category": "American Ginseng",      "off_query": "American ginseng root tea",          "iherb_query": "prince of peace american ginseng tea 20"},
    {"name": "AM GSG RT Tea 40 Bags",               "category": "American Ginseng",      "off_query": "American ginseng root tea",          "iherb_query": "prince of peace american ginseng tea 40"},
    {"name": "AM GSG RT Tea 60 Bags",               "category": "American Ginseng",      "off_query": "American ginseng root tea",          "iherb_query": "prince of peace american ginseng tea 60"},
    {"name": "AM GSG RT Tea 80 Bags",               "category": "American Ginseng",      "off_query": "American ginseng root tea",          "iherb_query": "prince of peace american ginseng tea 80"},
    # ── Ginger Chews ─────────────────────────────────────────────────────────
    {"name": "POP Ginger Chews Original 8 oz",      "category": "Ginger Chews",          "off_query": "Prince of Peace ginger chews original", "iherb_query": "prince of peace ginger chews original 8oz"},
    {"name": "POP Ginger Chews Original 2 oz",      "category": "Ginger Chews",          "off_query": "Prince of Peace ginger chews original", "iherb_query": "prince of peace ginger chews original 2oz"},
    {"name": "POP Ginger Chews Original 4 oz",      "category": "Ginger Chews",          "off_query": "Prince of Peace ginger chews original", "iherb_query": "prince of peace ginger chews original 4oz"},
    {"name": "POP Ginger Chews Original 1 lb Bulk", "category": "Ginger Chews",          "off_query": "Prince of Peace ginger chews bulk",     "iherb_query": "prince of peace ginger chews bulk 1lb"},
    {"name": "POP Ginger Chews Mango 8 oz",         "category": "Ginger Chews",          "off_query": "Prince of Peace ginger chews mango",    "iherb_query": "prince of peace ginger chews mango"},
    {"name": "POP Ginger Chews Mango 4 oz",         "category": "Ginger Chews",          "off_query": "Prince of Peace ginger chews mango",    "iherb_query": "prince of peace ginger chews mango 4oz"},
    {"name": "POP Ginger Chews Lemon 8 oz",         "category": "Ginger Chews",          "off_query": "Prince of Peace ginger chews lemon",    "iherb_query": "prince of peace ginger chews lemon 8oz"},
    {"name": "POP Ginger Chews Lemon 4 oz",         "category": "Ginger Chews",          "off_query": "Prince of Peace ginger chews lemon",    "iherb_query": "prince of peace ginger chews lemon 4oz"},
    {"name": "POP Ginger Chews Lemon 2 oz",         "category": "Ginger Chews",          "off_query": "Prince of Peace ginger chews lemon",    "iherb_query": "prince of peace ginger chews lemon 2oz"},
    {"name": "POP Ginger Chews Blood Orange 8 oz",  "category": "Ginger Chews",          "off_query": "Prince of Peace ginger chews blood orange", "iherb_query": "prince of peace ginger chews blood orange"},
    {"name": "POP Ginger Chews Blood Orange 4 oz",  "category": "Ginger Chews",          "off_query": "Prince of Peace ginger chews blood orange", "iherb_query": "prince of peace ginger chews blood orange 4oz"},
    {"name": "POP Ginger Chews Lychee 8 oz",        "category": "Ginger Chews",          "off_query": "Prince of Peace ginger chews lychee",   "iherb_query": "prince of peace ginger chews lychee"},
    {"name": "POP Ginger Chews Pineapple Coconut",  "category": "Ginger Chews",          "off_query": "Prince of Peace ginger chews pineapple","iherb_query": "prince of peace ginger chews pineapple coconut"},
    {"name": "POP Ginger Chews Assorted 8 oz",      "category": "Ginger Chews",          "off_query": "Prince of Peace ginger chews assorted", "iherb_query": "prince of peace ginger chews assorted"},
    {"name": "POP Ginger Chews Plus+ Original 3 oz","category": "Ginger Chews",          "off_query": "Prince of Peace ginger chews plus",     "iherb_query": "prince of peace ginger chews plus original"},
    {"name": "POP Ginger Chews Plus+ Lemon 3 oz",   "category": "Ginger Chews",          "off_query": "Prince of Peace ginger chews plus lemon","iherb_query": "prince of peace ginger chews plus lemon"},
    # ── Ginger Honey Crystals ─────────────────────────────────────────────────
    {"name": "POP Ginger Honey Crystals Original",  "category": "Ginger Honey Crystals", "off_query": "Prince of Peace ginger honey crystals", "iherb_query": "prince of peace ginger honey crystals original"},
    {"name": "POP Ginger Honey Crystals Lemon",     "category": "Ginger Honey Crystals", "off_query": "Prince of Peace ginger honey crystals lemon", "iherb_query": "prince of peace ginger honey crystals lemon"},
    {"name": "POP Ginger Honey Crystals Turmeric",  "category": "Ginger Honey Crystals", "off_query": "Prince of Peace ginger honey crystals turmeric", "iherb_query": "prince of peace ginger honey crystals turmeric"},
    # ── European Confections ──────────────────────────────────────────────────
    {"name": "Ferrero Rocher 12 Pcs",               "category": "European Confections",  "off_query": "Ferrero Rocher 12",                  "iherb_query": None},
    {"name": "Ferrero Rocher 24 Pcs Diamond",       "category": "European Confections",  "off_query": "Ferrero Rocher 24",                  "iherb_query": None},
    {"name": "Ferrero Rocher 48 Gift Box",          "category": "European Confections",  "off_query": "Ferrero Rocher 48",                  "iherb_query": None},
    {"name": "Gavottes Crepes 500g",                "category": "European Confections",  "off_query": "Gavottes crepes dentelle 500g",      "iherb_query": None},
    {"name": "Gavottes Crepes 1250g",               "category": "European Confections",  "off_query": "Gavottes crepes dentelle 1250g",     "iherb_query": None},
    {"name": "Kjeldsens Danish Butter Cookies 1lb", "category": "European Confections",  "off_query": "Kjeldsens butter cookies",           "iherb_query": None},
    {"name": "MX Eggrolls 32 pcs",                 "category": "European Confections",  "off_query": "Mexican egg rolls",                  "iherb_query": None},
    # ── Loacker ───────────────────────────────────────────────────────────────
    {"name": "Loacker Wafer Hazelnut 250g",         "category": "Loacker",               "off_query": "Loacker wafer hazelnut 250g",         "iherb_query": None},
    {"name": "Loacker GP Noisette Choc 3.53oz",     "category": "Loacker",               "off_query": "Loacker Gran Pasticceria noisette",   "iherb_query": None},
    {"name": "Loacker GP Dark Hazelnut 3.53oz",     "category": "Loacker",               "off_query": "Loacker Gran Pasticceria dark hazelnut","iherb_query": None},
    {"name": "Loacker GP Cappuccino 3.53oz",        "category": "Loacker",               "off_query": "Loacker Gran Pasticceria cappuccino", "iherb_query": None},
    {"name": "Loacker GP White Coconut 3.53oz",     "category": "Loacker",               "off_query": "Loacker Gran Pasticceria white coconut","iherb_query": None},
    {"name": "Loacker GP Coconut Choc 3.53oz",      "category": "Loacker",               "off_query": "Loacker Gran Pasticceria coconut",    "iherb_query": None},
    {"name": "Loacker GP Orange Choc 3.53oz",       "category": "Loacker",               "off_query": "Loacker Gran Pasticceria orange",     "iherb_query": None},
    # ── Asian Pantry ─────────────────────────────────────────────────────────
    {"name": "Mazola Corn Oil 128 oz",              "category": "Asian Pantry",           "off_query": "Mazola corn oil",                    "iherb_query": None},
    {"name": "Mazola Corn Oil 40 oz",               "category": "Asian Pantry",           "off_query": "Mazola corn oil",                    "iherb_query": None},
    {"name": "Totole Chicken Bouillon 2.2 lbs",     "category": "Asian Pantry",           "off_query": "Totole chicken bouillon",            "iherb_query": None},
    # ── Tiger Balm & Kwan Loong ───────────────────────────────────────────────
    {"name": "Kwan Loong Oil 2 fl oz",              "category": "Topical Health",         "off_query": None,                                 "iherb_query": "kwan loong medicated oil"},
    {"name": "Tiger Balm 18g Red Extra Strength",   "category": "Topical Health",         "off_query": None,                                 "iherb_query": "tiger balm red 18g"},
    {"name": "Tiger Balm 18g Ultra Strength",       "category": "Topical Health",         "off_query": None,                                 "iherb_query": "tiger balm ultra 18g"},
    {"name": "Tiger Balm 50g Ultra Strength",       "category": "Topical Health",         "off_query": None,                                 "iherb_query": "tiger balm ultra 50g"},
    {"name": "Tiger Balm Patch Large",              "category": "Topical Health",         "off_query": None,                                 "iherb_query": "tiger balm patch large"},
    {"name": "Tiger Balm Ultra 10g",                "category": "Topical Health",         "off_query": None,                                 "iherb_query": "tiger balm ultra 10g"},
    # ── Herbal Health Teas ────────────────────────────────────────────────────
    {"name": "POP OG Green Tea 100 Bags",           "category": "Herbal Health Teas",     "off_query": "Prince of Peace organic green tea",  "iherb_query": "prince of peace organic green tea 100"},
    {"name": "POP OG Jasmine Tea 100 Bags",         "category": "Herbal Health Teas",     "off_query": "Prince of Peace organic jasmine tea", "iherb_query": "prince of peace organic jasmine tea 100"},
    {"name": "POP OG Oolong Tea 100 Bags",          "category": "Herbal Health Teas",     "off_query": "Prince of Peace organic oolong tea",  "iherb_query": "prince of peace organic oolong tea 100"},
    {"name": "POP OG White Tea 100 Bags",           "category": "Herbal Health Teas",     "off_query": "Prince of Peace organic white tea",   "iherb_query": "prince of peace organic white tea 100"},
    {"name": "POP HT Blood Pressure Tea",           "category": "Herbal Health Teas",     "off_query": "blood pressure herbal tea",           "iherb_query": "prince of peace blood pressure tea"},
    {"name": "POP HT Blood Sugar Tea",              "category": "Herbal Health Teas",     "off_query": "blood sugar herbal tea",              "iherb_query": "prince of peace blood sugar tea"},
    {"name": "POP HT Cholesterol Tea",              "category": "Herbal Health Teas",     "off_query": "cholesterol herbal tea",              "iherb_query": "prince of peace cholesterol tea"},
]

# ── User-Agent Pool ───────────────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]


# ═════════════════════════════════════════════════════════════════════════════
# Open Food Facts Scraper
# ═════════════════════════════════════════════════════════════════════════════

class OpenFoodFactsScraper:
    """
    Uses the Open Food Facts public API — no auth, no scraping, never blocked.
    Docs: https://wiki.openfoodfacts.org/API
    """

    SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"

    def __init__(self, delay: float = 1.0):
        self.delay = delay

    def search(self, query: str) -> Optional[dict]:
        """Search OFF and return the best-matching product dict, or None."""
        params = {
            "search_terms":   query,
            "search_simple":  1,
            "action":         "process",
            "json":           1,
            "page_size":      5,
            "fields":         "product_name,ingredients_text,ingredients_text_en,"
                              "brands,categories,quantity,countries",
        }
        try:
            time.sleep(self.delay)
            resp = requests.get(self.SEARCH_URL, params=params, timeout=12,
                                headers={"User-Agent": "IngredientsScraper/1.0 (research)"})
            resp.raise_for_status()
            data = resp.json()
            products = data.get("products", [])
            if not products:
                return None
            # Prefer results that actually have ingredients
            for p in products:
                if p.get("ingredients_text_en") or p.get("ingredients_text"):
                    return p
            return products[0]  # fallback: return first even if no ingredients
        except Exception as exc:
            log.warning(f"    ↳ OFF search failed for '{query}': {exc}")
            return None

    def get_ingredients(self, product: dict) -> str:
        """Extract the cleanest ingredient string from an OFF product dict."""
        raw = (product.get("ingredients_text_en") or
               product.get("ingredients_text") or "").strip()
        # Light cleanup: collapse extra whitespace
        return re.sub(r"\s{2,}", " ", raw)

    def scrape_product(self, name: str, query: str, category: str) -> dict:
        """Return a single result row for one product."""
        log.info(f"  [OFF] {name}")
        product = self.search(query)
        if not product:
            return _empty_row(name, category, "Open Food Facts", query, "no results")

        ingredients = self.get_ingredients(product)
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

    def scrape_all(self, products: list[dict]) -> list[dict]:
        rows = []
        items = [p for p in products if p.get("off_query")]
        log.info(f"Open Food Facts: scraping {len(items)} products...")
        for p in items:
            rows.append(self.scrape_product(p["name"], p["off_query"], p["category"]))
        return rows


# ═════════════════════════════════════════════════════════════════════════════
# iHerb Scraper
# ═════════════════════════════════════════════════════════════════════════════

class iHerbScraper:
    """
    Scrapes ingredient lists from iHerb.com product pages using BeautifulSoup.
    iHerb is much more scraper-friendly than Amazon.
    """

    SEARCH_URL = "https://www.iherb.com/search?kw={query}"
    BASE_URL   = "https://www.iherb.com"

    def __init__(self, delay: float = 2.5):
        self.delay   = delay
        self.session = requests.Session()
        self.session.headers.update(self._headers())

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
        """Fetch URL with jitter delay, return BeautifulSoup or None."""
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
        """Search iHerb and return the first product page URL."""
        url  = self.SEARCH_URL.format(query=requests.utils.quote(query))
        soup = self._get(url)
        if not soup:
            return None

        # iHerb search result product cards
        for sel in [
            "a.absolute-link.product-link",
            "div.product-cell a[href*='/pr/']",
            ".product-title a",
            "a[href*='iherb.com/pr/']",
        ]:
            link = soup.select_one(sel)
            if link and link.get("href"):
                href = link["href"]
                if href.startswith("/"):
                    href = self.BASE_URL + href
                return href

        # Fallback: any /pr/ link
        for a in soup.find_all("a", href=True):
            if "/pr/" in a["href"]:
                href = a["href"]
                if href.startswith("/"):
                    href = self.BASE_URL + href
                return href

        return None

    def _parse_ingredients(self, soup: BeautifulSoup) -> tuple[str, str]:
        """
        Extract ingredient text and matched page title from a product page.
        Returns (ingredients_text, page_title).
        """
        title = ""
        title_el = soup.select_one("h1.product-name, h1[itemprop='name'], .product-title h1")
        if title_el:
            title = title_el.get_text(strip=True)[:120]

        ingredients = ""

        # Strategy 1: dedicated ingredients section/tab
        for sel in [
            "#tab-ingredients",
            "[data-tab='ingredients']",
            ".ingredients-content",
            "section.ingredients",
        ]:
            el = soup.select_one(sel)
            if el:
                ingredients = el.get_text(" ", strip=True)
                break

        # Strategy 2: look for heading "Ingredients" followed by content
        if not ingredients:
            for heading in soup.find_all(["h2", "h3", "h4", "strong", "b"]):
                text = heading.get_text(strip=True).lower()
                if text in ("ingredients", "ingredient", "other ingredients",
                            "supplement facts", "active ingredients"):
                    # Grab next sibling text
                    sibling = heading.find_next_sibling()
                    if sibling:
                        ingredients = sibling.get_text(" ", strip=True)
                    else:
                        parent = heading.parent
                        if parent:
                            ingredients = parent.get_text(" ", strip=True)
                    if ingredients:
                        break

        # Strategy 3: scan all text blocks for "Ingredients:" label
        if not ingredients:
            for el in soup.find_all(["p", "div", "li", "span"]):
                txt = el.get_text(" ", strip=True)
                if re.match(r"^ingredients\s*:", txt, re.I) and len(txt) > 20:
                    ingredients = txt
                    break

        # Cleanup
        ingredients = re.sub(r"\s{2,}", " ", ingredients).strip()

        # Strip leading label if present
        ingredients = re.sub(r"^ingredients\s*:\s*", "", ingredients, flags=re.I)

        return ingredients, title

    def scrape_product(self, name: str, query: str, category: str) -> dict:
        log.info(f"  [iHerb] {name}")
        url = self._search_first_url(query)
        if not url:
            log.info(f"    ↳ No iHerb search result for: {query}")
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

    def scrape_all(self, products: list[dict]) -> list[dict]:
        rows = []
        items = [p for p in products if p.get("iherb_query")]
        log.info(f"iHerb: scraping {len(items)} products...")
        for p in items:
            rows.append(self.scrape_product(p["name"], p["iherb_query"], p["category"]))
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
    Combine OFF and iHerb rows. For products found in both sources,
    prefer the one that actually has ingredients; keep both if both have them.
    """
    all_rows = off_rows + iherb_rows
    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)

    # Sort so rows WITH ingredients come first within each product
    df["_rank"] = df["ingredients_found"].apply(lambda x: 0 if x else 1)
    df = df.sort_values(["product_name", "_rank"]).drop(columns=["_rank"])

    return df.reset_index(drop=True)


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
    # Reorder columns, keep any extras at end
    ordered = [c for c in COLUMNS if c in df.columns]
    extras  = [c for c in df.columns if c not in ordered]
    df[ordered + extras].to_csv(path, index=False, encoding="utf-8-sig")
    found   = df["ingredients_found"].sum()
    total   = len(df)
    log.info(f"✓ CSV written → {path}")
    log.info(f"  {found}/{total} rows have ingredients  "
             f"({round(found/total*100)}% fill rate)")


# ═════════════════════════════════════════════════════════════════════════════
# Main
# ═════════════════════════════════════════════════════════════════════════════

def main(args: argparse.Namespace) -> None:
    log.info("=" * 60)
    log.info(" Ingredients Scraper — Open Food Facts + iHerb")
    log.info("=" * 60)

    off_rows    = []
    iherb_rows  = []

    if not args.skip_off:
        scraper    = OpenFoodFactsScraper(delay=args.off_delay)
        off_rows   = scraper.scrape_all(PRODUCTS)
    else:
        log.info("Skipping Open Food Facts (--skip-off)")

    if not args.skip_iherb:
        scraper    = iHerbScraper(delay=args.iherb_delay)
        iherb_rows = scraper.scrape_all(PRODUCTS)
    else:
        log.info("Skipping iHerb (--skip-iherb)")

    df = merge_results(off_rows, iherb_rows)

    # Summary by category
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


# ═════════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Scrape ingredient lists from Open Food Facts + iHerb",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--output", default=f"ingredients_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        help="Output CSV filename (default: ingredients_YYYYMMDD_HHMM.csv)",
    )
    p.add_argument(
        "--off-delay", type=float, default=1.0,
        help="Seconds between Open Food Facts API calls (default: 1.0)",
    )
    p.add_argument(
        "--iherb-delay", type=float, default=2.5,
        help="Seconds between iHerb requests (default: 2.5)",
    )
    p.add_argument("--skip-off",   action="store_true", help="Skip Open Food Facts")
    p.add_argument("--skip-iherb", action="store_true", help="Skip iHerb")
    return p.parse_args()


if __name__ == "__main__":
    main(parse_args())
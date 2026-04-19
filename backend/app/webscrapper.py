"""
Google Trends Scraper — POP Specialty Grocery Products
=======================================================
Reads product families directly from POP xlsx files in pop_data/,
then fetches Google Trends interest-over-time and related queries only.

Dependencies:
    pip install pytrends pandas openpyxl

Usage:
    python google_trends_scraper.py
    python google_trends_scraper.py --timeframe "today 3-m" --output q2_trends.csv
    python google_trends_scraper.py --geo US-CA

Folder structure expected:
    your_project/
    ├── google_trends_scraper.py
    └── pop_data/
        ├── POP_ItemSpecMaster.xlsx
        └── POP_InventorySnapshot.xlsx
"""

import re
import time
import argparse
import logging
import os
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

import pandas as pd
from pytrends.request import TrendReq
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

# Dynamic family extractor - replaces hardcoded FAMILY_RULES
DYNAMIC_EXTRACTOR = DynamicFamilyExtractor()

# Extract families and keywords dynamically from POP data
FAMILY_GROUPS, CATEGORY_KEYWORDS = DYNAMIC_EXTRACTOR.extract_families_and_keywords()


# ═════════════════════════════════════════════════════════════════════════════
# Step 1 — Load products from POP xlsx files
# ═════════════════════════════════════════════════════════════════════════════

def load_pop_products() -> pd.DataFrame:
    """
    Load POP data using dynamic family extraction.
    Returns a DataFrame with item details, assigned family, trends keyword,
    and per-site inventory (SF / NJ / LA).
    """
    log.info("Loading POP data with dynamic family extraction...")
    
    # Use the dynamic extractor to load and process POP data
    pop_df = DYNAMIC_EXTRACTOR.load_pop_data()
    
    # Assign family and trends keyword dynamically
    pop_df["family"] = ""
    pop_df["trends_keyword"] = ""
    
    for idx, row in pop_df.iterrows():
        desc = row["description"]
        if isinstance(desc, str) and desc.strip():
            family_info = DYNAMIC_EXTRACTOR._extract_family_from_description(desc.strip())
            if family_info:
                family, keyword = family_info
                pop_df.loc[idx, "family"] = family
                pop_df.loc[idx, "trends_keyword"] = keyword
            else:
                pop_df.loc[idx, "family"] = "Other"
                pop_df.loc[idx, "trends_keyword"] = ""
    
    keep = [
        "item_number", "description", "family", "trends_keyword",
        "country_of_origin", "shelf_life", "allergens", "upc",
        "inv_sf_available", "inv_nj_available", "inv_la_available",
    ]
    existing = [c for c in keep if c in pop_df.columns]
    log.info(f"  ↳ {len(pop_df)} products across {pop_df['family'].nunique()} families")
    return pop_df[existing].reset_index(drop=True)


def build_product_groups(products: pd.DataFrame) -> dict[str, list[str]]:
    """
    Use dynamically extracted family groups.
    Returns the pre-built groups from the dynamic extractor.
    """
    log.info(f"  ↳ {len(FAMILY_GROUPS)} trend groups from dynamic extraction")
    return FAMILY_GROUPS


# ═════════════════════════════════════════════════════════════════════════════
# Step 2 — Google Trends scraper
# ═════════════════════════════════════════════════════════════════════════════

class GoogleTrendsScraper:

    def __init__(
        self,
        geo: str = "US",
        timeframe: str = "today 12-m",
        delay: float = 2.5,
        cache_dir: str = "cache",
        cache_hours: int = 24,
    ):
        """
        Args:
            geo:       Country/region code (e.g. 'US', 'US-CA' for California)
            timeframe: Google Trends timeframe string.
                       Options: 'now 1-d', 'now 7-d', 'today 1-m',
                                'today 3-m', 'today 12-m', 'today 5-y'
            delay:     Seconds to wait between API calls (avoid rate-limiting)
            cache_dir: Directory to store cached CSV files
            cache_hours: How many hours before cache expires
        """
        self.geo = geo
        self.timeframe = timeframe
        self.delay = delay
        self.cache_dir = cache_dir
        self.cache_hours = cache_hours
        self.pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        log.info(f"Scraper initialized | geo={geo} | timeframe={timeframe} | cache_dir={cache_dir}")

    def _get_cache_filename(self) -> str:
        """Generate cache filename based on geo and timeframe."""
        safe_geo = self.geo.replace("-", "_")
        safe_timeframe = self.timeframe.replace(" ", "_").replace("-", "_")
        return os.path.join(self.cache_dir, f"trends_{safe_geo}_{safe_timeframe}.csv")

    def _is_cache_valid(self, cache_path: str) -> bool:
        """Check if cache file exists and is within the validity period."""
        if not os.path.exists(cache_path):
            return False
        
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        expiry_time = datetime.now() - timedelta(hours=self.cache_hours)
        
        return file_time > expiry_time

    def _load_from_cache(self) -> Optional[dict]:
        """Load data from cache file if valid."""
        cache_path = self._get_cache_filename()
        
        if not self._is_cache_valid(cache_path):
            log.info("Cache not found or expired, will fetch fresh data")
            return None
        
        try:
            log.info(f"Loading data from cache: {cache_path}")
            df = pd.read_csv(cache_path)
            
            # Convert cached DataFrame back to the expected dict format
            data = {
                "interest_over_time": df[df["section"] == "interest_over_time"],
                "interest_by_region": df[df["section"] == "interest_by_region"],
                "related_queries": {},
                "suggestions": df[df["section"] == "suggestions"],
                "trending_page": []
            }
            
            # Reconstruct related queries from cached data
            rq_df = df[df["section"] == "related_queries"]
            if not rq_df.empty:
                for keyword in rq_df["keyword"].unique():
                    keyword_data = rq_df[rq_df["keyword"] == keyword]
                    data["related_queries"][keyword] = {
                        "top": keyword_data[keyword_data["query_type"] == "top"],
                        "rising": keyword_data[keyword_data["query_type"] == "rising"]
                    }
            
            # Reconstruct trending page data
            tp_df = df[df["section"] == "trending_now"]
            if not tp_df.empty:
                data["trending_page"] = tp_df.to_dict("records")
            
            log.info(f"✓ Loaded {len(df)} rows from cache")
            return data
            
        except Exception as exc:
            log.warning(f"Failed to load from cache: {exc}")
            return None

    def _save_to_cache(self, data: dict) -> None:
        """Save data to cache file."""
        cache_path = self._get_cache_filename()
        
        try:
            log.info(f"Saving data to cache: {cache_path}")
            self.export_to_csv(cache_path, data)
            log.info("✓ Data cached successfully")
        except Exception as exc:
            log.warning(f"Failed to save to cache: {exc}")

    def _build_payload(self, keywords: list[str]) -> None:
        self.pytrends.build_payload(
            kw_list=keywords[:5], cat=0,
            timeframe=self.timeframe, geo=self.geo, gprop="",
        )

    def _safe_fetch(self, method_name: str, *args, **kwargs) -> Optional[pd.DataFrame]:
        try:
            time.sleep(self.delay)
            return getattr(self.pytrends, method_name)(*args, **kwargs)
        except Exception as exc:
            log.warning(f"  ↳ [{method_name}] failed: {exc}")
            return None

    def get_interest_over_time(self, product_groups: dict[str, list[str]]) -> pd.DataFrame:
        log.info("Fetching interest over time...")
        frames = []
        for group_name, keywords in product_groups.items():
            log.info(f"  → {group_name}: {keywords}")
            self._build_payload(keywords)
            df = self._safe_fetch("interest_over_time")
            if df is not None and not df.empty:
                df = df.drop(columns=["isPartial"], errors="ignore")
                df["group"] = group_name
                frames.append(df)
        if not frames:
            log.warning("No interest-over-time data returned.")
            return pd.DataFrame()
        result = pd.concat(frames)
        result.index.name = "date"
        return result

    def get_related_queries(self) -> list[dict]:
        log.info("Fetching related queries...")
        rows = []
        for keyword in CATEGORY_KEYWORDS:
            log.info(f"  → {keyword}")
            self._build_payload([keyword])
            data = self._safe_fetch("related_queries")
            if not data or keyword not in data:
                continue
            for qtype in ("top", "rising"):
                df = data[keyword].get(qtype)
                if isinstance(df, pd.DataFrame) and not df.empty:
                    for _, row in df.iterrows():
                        rows.append({
                            "category_keyword": keyword,
                            "query_type":       qtype,
                            "related_query":    row.get("query", ""),
                            "value":            row.get("value", ""),
                        })
        return rows

    def get_interest_by_region(self) -> pd.DataFrame:
        """Fetch interest by US region for category keywords."""
        log.info("Fetching interest by region...")
        all_frames = []

        # Split category keywords into groups of 5
        chunks = [CATEGORY_KEYWORDS[i:i+5] for i in range(0, len(CATEGORY_KEYWORDS), 5)]
        for keywords in chunks:
            self._build_payload(keywords)
            df = self._safe_fetch("interest_by_region", resolution="REGION", inc_low_vol=True)
            if df is not None and not df.empty:
                all_frames.append(df)

        if not all_frames:
            return pd.DataFrame()
        return pd.concat(all_frames, axis=1).groupby(level=0, axis=1).mean()

    def get_related_topics(self) -> dict[str, dict]:
        """Fetch related topics for category keywords."""
        log.info("Fetching related topics...")
        results = {}

        for keyword in CATEGORY_KEYWORDS:
            log.info(f"  → {keyword}")
            self._build_payload([keyword])
            data = self._safe_fetch("related_topics")
            if data and keyword in data:
                results[keyword] = {
                    "top": data[keyword].get("top"),
                    "rising": data[keyword].get("rising"),
                }
        return results

    def get_suggestions(self) -> pd.DataFrame:
        """Fetch autocomplete suggestions for key product terms."""
        log.info("Fetching keyword suggestions...")
        suggestion_terms = [
            "American ginseng",
            "ginger chews",
            "Tiger Balm",
            "Ferrero Rocher",
            "Loacker wafer",
        ]
        rows = []
        for term in suggestion_terms:
            try:
                time.sleep(self.delay)
                suggestions = self.pytrends.suggestions(keyword=term)
                for s in suggestions:
                    rows.append({
                        "search_term": term,
                        "suggestion_title": s.get("title"),
                        "suggestion_type": s.get("type"),
                    })
            except Exception as exc:
                log.warning(f"  ↳ Suggestions failed for '{term}': {exc}")
        return pd.DataFrame(rows)

    def scrape_trending_page(self) -> list[dict]:
        """Scrape Google Trends 'Trending Now' page with BeautifulSoup."""
        log.info("Scraping Google Trends trending page...")
        url = "https://trends.google.com/trending?geo=US&hours=24"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            import requests
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")

            trends = []
            # Parse trend cards (selector may vary with Google's HTML updates)
            cards = soup.select("div[data-entityid]") or soup.select(".trending-story")
            for card in cards[:30]:
                title_el = card.select_one("a[aria-label], .trending-story-title, h3")
                vol_el = card.select_one(".search-count-title, .trending-searches-count")
                trends.append({
                    "title": title_el.get_text(strip=True) if title_el else "N/A",
                    "search_volume": vol_el.get_text(strip=True) if vol_el else "N/A",
                    "scraped_at": datetime.now().isoformat(),
                })

            if trends:
                log.info(f"  ↳ Found {len(trends)} trending topics")
            else:
                log.info("  ↳ No structured cards found")
            return trends

        except Exception as exc:
            log.warning(f"  ↳ BeautifulSoup scrape failed: {exc}")
            return []

    def export_to_csv(self, output_path: str, data: dict) -> None:
        """Write all collected data to a single flat CSV file."""
        log.info(f"Exporting CSV to {output_path} ...")
        rows = []

        # Interest Over Time
        iot = data.get("interest_over_time")
        if iot is not None and not iot.empty:
            df = iot.reset_index()
            group_col = "group" if "group" in df.columns else None
            keyword_cols = [c for c in df.columns if c not in ("date", "group", "isPartial")]
            for _, row in df.iterrows():
                for kw in keyword_cols:
                    rows.append({
                        "section": "interest_over_time",
                        "date": str(row["date"])[:10],
                        "keyword": kw,
                        "group": row.get("group", "") if group_col else "",
                        "interest_score": row[kw],
                        "region": "",
                        "query_type": "",
                        "related_term": "",
                        "related_value": "",
                        "suggestion_type": "",
                    })

        # Interest by Region
        ibr = data.get("interest_by_region")
        if ibr is not None and not ibr.empty:
            df = ibr.reset_index()
            keyword_cols = [c for c in df.columns if c != "geoName"]
            for _, row in df.iterrows():
                for kw in keyword_cols:
                    rows.append({
                        "section": "interest_by_region",
                        "date": "",
                        "keyword": kw,
                        "group": "",
                        "interest_score": row[kw],
                        "region": row.get("geoName", ""),
                        "query_type": "",
                        "related_term": "",
                        "related_value": "",
                        "suggestion_type": "",
                    })

        # Related Queries
        rq = data.get("related_queries", {})
        for keyword, qdata in rq.items():
            for qtype in ("top", "rising"):
                df = qdata.get(qtype)
                if isinstance(df, pd.DataFrame) and not df.empty:
                    for _, row in df.iterrows():
                        rows.append({
                            "section": "related_queries",
                            "date": "",
                            "keyword": keyword,
                            "group": "",
                            "interest_score": "",
                            "region": "",
                            "query_type": qtype,
                            "related_term": row.get("query", ""),
                            "related_value": row.get("value", ""),
                            "suggestion_type": "",
                        })

        # Suggestions
        sugg = data.get("suggestions")
        if sugg is not None and not sugg.empty:
            for _, row in sugg.iterrows():
                rows.append({
                    "section": "suggestions",
                    "date": "",
                    "keyword": row.get("search_term", ""),
                    "group": "",
                    "interest_score": "",
                    "region": "",
                    "query_type": "",
                    "related_term": row.get("suggestion_title", ""),
                    "related_value": "",
                    "suggestion_type": row.get("suggestion_type", ""),
                })

        # Trending Now
        for item in data.get("trending_page", []):
            rows.append({
                "section": "trending_now",
                "date": item.get("scraped_at", "")[:10],
                "keyword": item.get("title", ""),
                "group": "",
                "interest_score": item.get("search_volume", ""),
                "region": "US",
                "query_type": "",
                "related_term": "",
                "related_value": "",
                "suggestion_type": "",
            })

        if not rows:
            log.warning("No data rows to write to CSV.")
            return

        out_df = pd.DataFrame(rows, columns=[
            "section", "date", "keyword", "group",
            "interest_score", "region", "query_type",
            "related_term", "related_value", "suggestion_type",
        ])
        out_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        log.info(f"✓ CSV export complete → {output_path}  ({len(out_df):,} rows)")

    def export_to_excel(self, output_path: str, data: dict) -> None:
        """Write all collected data to a multi-sheet Excel workbook."""
        log.info(f"Exporting data to {output_path} ...")
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            # Interest Over Time
            if "interest_over_time" in data and not data["interest_over_time"].empty:
                df = data["interest_over_time"].reset_index()
                df.to_excel(writer, sheet_name="Interest Over Time", index=False)

            # Interest by Region
            if "interest_by_region" in data and not data["interest_by_region"].empty:
                data["interest_by_region"].reset_index().to_excel(
                    writer, sheet_name="By Region", index=False
                )

            # Related Queries
            rq = data.get("related_queries", {})
            top_rows, rising_rows = [], []
            for keyword, qdata in rq.items():
                if isinstance(qdata.get("top"), pd.DataFrame):
                    df = qdata["top"].copy()
                    df.insert(0, "keyword", keyword)
                    top_rows.append(df)
                if isinstance(qdata.get("rising"), pd.DataFrame):
                    df = qdata["rising"].copy()
                    df.insert(0, "keyword", keyword)
                    rising_rows.append(df)

            if top_rows:
                pd.concat(top_rows).to_excel(writer, sheet_name="Related Queries Top", index=False)
            if rising_rows:
                pd.concat(rising_rows).to_excel(writer, sheet_name="Related Queries Rising", index=False)

            # Suggestions
            if "suggestions" in data and not data["suggestions"].empty:
                data["suggestions"].to_excel(writer, sheet_name="Suggestions", index=False)

            # Trending Now
            bs_data = data.get("trending_page", [])
            if bs_data:
                pd.DataFrame(bs_data).to_excel(writer, sheet_name="Trending Now", index=False)

            # Run metadata
            meta = pd.DataFrame([{
                "run_at": datetime.now().isoformat(),
                "geo": self.geo,
                "timeframe": self.timeframe,
                "cache_hours": self.cache_hours,
            }])
            meta.to_excel(writer, sheet_name="Metadata", index=False)

        log.info(f"✓ Export complete → {output_path}")

    def run(self, output_path: str, csv_only: bool = False, force_refresh: bool = False, products: pd.DataFrame = None, product_groups: dict = None) -> None:
        """Run the full scrape pipeline and export results."""
        log.info("=" * 60)
        log.info("Starting Google Trends scrape for specialty grocery products")
        log.info("=" * 60)

        collected = {}
        
        # Try to load from cache unless force refresh is requested
        if not force_refresh:
            cached_data = self._load_from_cache()
            if cached_data is not None:
                collected = cached_data
                log.info("Using cached data (use --force-refresh to fetch fresh data)")
            else:
                log.info("Fetching fresh data from APIs...")
                if product_groups:
                    collected["interest_over_time"] = self.get_interest_over_time(product_groups)
                collected["interest_by_region"] = self.get_interest_by_region()
                collected["related_queries"]    = self.get_related_queries()
                collected["related_topics"]     = self.get_related_topics()
                collected["suggestions"]        = self.get_suggestions()
                collected["trending_page"]      = self.scrape_trending_page()
                
                # Save fresh data to cache
                self._save_to_cache(collected)
        else:
            log.info("Force refresh requested, fetching fresh data...")
            if product_groups:
                collected["interest_over_time"] = self.get_interest_over_time(product_groups)
            collected["interest_by_region"] = self.get_interest_by_region()
            collected["related_queries"]    = self.get_related_queries()
            collected["related_topics"]     = self.get_related_topics()
            collected["suggestions"]        = self.get_suggestions()
            collected["trending_page"]      = self.scrape_trending_page()
            
            # Save fresh data to cache
            self._save_to_cache(collected)

        # Always write CSV
        csv_path = output_path.replace(".xlsx", ".csv") if output_path.endswith(".xlsx") else output_path
        if not csv_path.endswith(".csv"):
            csv_path += ".csv"
        self.export_to_csv(csv_path, collected)

        # Also write Excel unless --csv-only flag is set
        if not csv_only:
            xlsx_path = output_path if output_path.endswith(".xlsx") else output_path.replace(".csv", ".xlsx")
            self.export_to_excel(xlsx_path, collected)

        log.info("=" * 60)
        log.info("Scrape complete.")
        log.info("=" * 60)


# ═════════════════════════════════════════════════════════════════════════════
# Step 3 — Export to CSV
# ═════════════════════════════════════════════════════════════════════════════

ALL_COLUMNS = [
    "section", "date", "group", "keyword", "interest_score",
    "query_type", "related_query", "value",
    "item_number", "description", "family", "trends_keyword",
    "country_of_origin", "shelf_life", "allergens", "upc",
    "inv_sf_available", "inv_nj_available", "inv_la_available",
]

def _blank_row(section: str = "", **kwargs) -> dict:
    row = {c: "" for c in ALL_COLUMNS}
    row["section"] = section
    row.update(kwargs)
    return row

def export_csv(
    output_path: str,
    products: pd.DataFrame,
    iot: pd.DataFrame,
    related: list[dict],
) -> None:
    rows = []

    # ── Section A: Interest Over Time ─────────────────────────────────────────
    rows.append(_blank_row("=== INTEREST OVER TIME ==="))
    if not iot.empty:
        df = iot.reset_index()
        kw_cols = [c for c in df.columns if c not in ("date", "group", "isPartial")]
        for _, row in df.iterrows():
            for kw in kw_cols:
                rows.append(_blank_row(
                    section="interest_over_time",
                    date=str(row["date"])[:10],
                    group=row.get("group", ""),
                    keyword=kw,
                    interest_score=row[kw],
                ))
    else:
        rows.append(_blank_row("no data retrieved"))

    rows.append(_blank_row())  # blank separator

    # ── Section B: Related Queries ────────────────────────────────────────────
    rows.append(_blank_row("=== RELATED QUERIES ==="))
    if related:
        for r in related:
            rows.append(_blank_row(
                section="related_queries",
                group=r["category_keyword"],
                keyword=r["category_keyword"],
                query_type=r["query_type"],
                related_query=r["related_query"],
                value=r["value"],
            ))
    else:
        rows.append(_blank_row("no data retrieved"))

    rows.append(_blank_row())  # blank separator

    # ── Section C: Product Reference ──────────────────────────────────────────
    rows.append(_blank_row("=== PRODUCT REFERENCE (from POP xlsx) ==="))
    for _, p in products.iterrows():
        rows.append(_blank_row(
            section="product_reference",
            group=p.get("family", ""),
            keyword=p.get("trends_keyword", ""),
            item_number=p.get("item_number", ""),
            description=p.get("description", ""),
            family=p.get("family", ""),
            trends_keyword=p.get("trends_keyword", ""),
            country_of_origin=p.get("country_of_origin", ""),
            shelf_life=p.get("shelf_life", ""),
            allergens=p.get("allergens", ""),
            upc=p.get("upc", ""),
            inv_sf_available=p.get("inv_sf_available", ""),
            inv_nj_available=p.get("inv_nj_available", ""),
            inv_la_available=p.get("inv_la_available", ""),
        ))

    out = pd.DataFrame(rows, columns=ALL_COLUMNS)
    out.to_csv(output_path, index=False, encoding="utf-8-sig")

    iot_count  = sum(1 for r in rows if r["section"] == "interest_over_time")
    rq_count   = len(related)
    prod_count = len(products)
    log.info(f"✓ CSV written → {output_path}")
    log.info(f"  Interest over time rows : {iot_count:,}")
    log.info(f"  Related query rows      : {rq_count:,}")
    log.info(f"  Product reference rows  : {prod_count:,}")


# ═════════════════════════════════════════════════════════════════════════════
# Main
# ═════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Google Trends scraper for POP specialty grocery products"
    )
    parser.add_argument(
        "--geo",
        default="US",
        help="Region code (default: US). Use 'US-CA' for California, etc.",
    )
    parser.add_argument(
        "--timeframe",
        default="today 12-m",
        help=(
            "Trends timeframe (default: 'today 12-m'). "
            "Options: 'now 1-d', 'now 7-d', 'today 1-m', 'today 3-m', "
            "'today 12-m', 'today 5-y'"
        ),
    )
    parser.add_argument(
        "--output",
        default=f"trends_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        help="Output Excel filename (default: trends_YYYYMMDD_HHMM.xlsx)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.5,
        help="Seconds between API calls to avoid rate-limiting (default: 2.5)",
    )
    parser.add_argument(
        "--csv-only",
        action="store_true",
        help="Export only CSV (skip Excel workbook)",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force fresh data fetch, ignoring cache",
    )
    parser.add_argument(
        "--cache-hours",
        type=int,
        default=24,
        help="Cache validity period in hours (default: 24)",
    )
    parser.add_argument(
        "--cache-dir",
        default="cache",
        help="Cache directory path (default: cache)",
    )
    return parser.parse_args()


def main(args: argparse.Namespace) -> None:
    log.info("=" * 60)
    log.info(" Google Trends Scraper — POP Specialty Grocery")
    log.info("=" * 60)

    # 1. Load products + build trend groups from xlsx
    products       = load_pop_products()
    product_groups = build_product_groups(products)

    log.info("\nProduct families → trend keywords:")
    for fam, kws in product_groups.items():
        log.info(f"  {fam:<35} {kws}")
    log.info("")

    # 2. Fetch Google Trends
    scraper = GoogleTrendsScraper(
        geo=args.geo,
        timeframe=args.timeframe,
        delay=args.delay,
        cache_dir=args.cache_dir,
        cache_hours=args.cache_hours,
    )
    scraper.run(output_path=args.output, csv_only=args.csv_only, force_refresh=args.force_refresh, products=products, product_groups=product_groups)

    log.info("=" * 60)
    log.info("Done.")
    log.info("=" * 60)
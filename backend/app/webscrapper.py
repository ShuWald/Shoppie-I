from typing import Annotated
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import requests
from bs4 import BeautifulSoup

"""
Google Trends Scraper - Asian Grocery & Specialty Products
==========================================================
Scrapes trend data for ginseng products, ginger chews, European confections,
Asian pantry staples, and herbal health products.

Dependencies:
    pip install pytrends beautifulsoup4 requests pandas openpyxl

Usage:
    python google_trends_scraper.py
    python google_trends_scraper.py --timeframe today\ 3-m --output trends_q3.xlsx
"""

import time
import argparse
import logging
from datetime import datetime
from typing import Optional

import pandas as pd
from pytrends.request import TrendReq
from bs4 import BeautifulSoup
import requests

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Product Categories ────────────────────────────────────────────────────────
# Grouped by product family for Google Trends comparison (max 5 per query)

PRODUCT_GROUPS = {
    "American Ginseng": [
        "American ginseng root",
        "American ginseng slices",
        "ginseng instant tea",
        "ginseng candy",
        "ginseng herbal tea",
    ],
    "Ginger Chews - Flavors": [
        "Prince of Peace ginger chews",
        "ginger chews original",
        "ginger chews mango",
        "ginger chews lemon",
        "ginger chews blood orange",
    ],
    "Ginger Chews - Health": [
        "ginger chews lychee",
        "ginger chews pineapple coconut",
        "ginger honey crystals",
        "ginger chews plus",
        "ginger chews bulk",
    ],
    "European Confections": [
        "Ferrero Rocher",
        "Gavottes crepes dentelle",
        "Kjeldsens butter cookies",
        "Loacker wafer hazelnut",
        "Mexican egg rolls",
    ],
    "Loacker Varieties": [
        "Loacker dark hazelnut",
        "Loacker cappuccino",
        "Loacker white coconut",
        "Loacker orange chocolate",
        "Loacker Gran Pasticceria",
    ],
    "Asian Pantry Staples": [
        "Mazola corn oil",
        "Totole chicken bouillon",
        "Kwan Loong oil",
        "Tiger Balm",
        "Tiger Balm patch",
    ],
    "Herbal Health Teas": [
        "Prince of Peace green tea",
        "Prince of Peace jasmine tea",
        "Prince of Peace oolong tea",
        "Prince of Peace white tea",
        "blood pressure herbal tea",
    ],
    "Health Supplements Tea": [
        "blood pressure herbal supplement",
        "blood sugar herbal tea",
        "cholesterol herbal supplement",
        "ginseng blood pressure",
        "herbal health tea Asian",
    ],
}

# Broader category keywords for rising/related queries
CATEGORY_KEYWORDS = [
    "American ginseng",
    "ginger chews",
    "Tiger Balm",
    "Ferrero Rocher",
    "herbal health tea",
]


class GoogleTrendsScraper:
    """Scrapes Google Trends data for specialty Asian grocery products."""

    def __init__(
        self,
        geo: str = "US",
        timeframe: str = "today 12-m",
        delay: float = 2.5,
    ):
        """
        Args:
            geo:       Country/region code (e.g. 'US', 'US-CA' for California)
            timeframe: Google Trends timeframe string.
                       Options: 'now 1-d', 'now 7-d', 'today 1-m',
                                'today 3-m', 'today 12-m', 'today 5-y'
            delay:     Seconds to wait between API calls (avoid rate-limiting)
        """
        self.geo = geo
        self.timeframe = timeframe
        self.delay = delay
        self.pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        log.info(f"Scraper initialized | geo={geo} | timeframe={timeframe}")

    # ── Core fetch helpers ────────────────────────────────────────────────────

    def _build_payload(self, keywords: list[str]) -> None:
        """Build pytrends payload for up to 5 keywords."""
        self.pytrends.build_payload(
            kw_list=keywords[:5],
            cat=0,
            timeframe=self.timeframe,
            geo=self.geo,
            gprop="",
        )

    def _safe_fetch(self, method_name: str, *args, **kwargs) -> Optional[pd.DataFrame]:
        """Call a pytrends method with error handling and rate-limit delay."""
        try:
            time.sleep(self.delay)
            method = getattr(self.pytrends, method_name)
            result = method(*args, **kwargs)
            return result
        except Exception as exc:
            log.warning(f"  ↳ Failed [{method_name}]: {exc}")
            return None

    # ── Data fetchers ─────────────────────────────────────────────────────────

    def get_interest_over_time(self) -> pd.DataFrame:
        """Fetch interest-over-time for all product groups."""
        log.info("Fetching interest over time for all product groups...")
        all_frames = []

        for group_name, keywords in PRODUCT_GROUPS.items():
            log.info(f"  → {group_name}")
            self._build_payload(keywords)
            df = self._safe_fetch("interest_over_time")
            if df is not None and not df.empty:
                df = df.drop(columns=["isPartial"], errors="ignore")
                df["group"] = group_name
                all_frames.append(df)

        if not all_frames:
            log.error("No interest-over-time data retrieved.")
            return pd.DataFrame()

        combined = pd.concat(all_frames)
        combined.index.name = "date"
        return combined

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

    def get_related_queries(self) -> dict[str, dict]:
        """Fetch rising and top related queries for category keywords."""
        log.info("Fetching related queries...")
        results = {}

        for keyword in CATEGORY_KEYWORDS:
            log.info(f"  → {keyword}")
            self._build_payload([keyword])
            data = self._safe_fetch("related_queries")
            if data and keyword in data:
                results[keyword] = {
                    "top": data[keyword].get("top"),
                    "rising": data[keyword].get("rising"),
                }
        return results

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

    def get_trending_searches(self) -> pd.DataFrame:
        """Fetch today's trending searches (US)."""
        log.info("Fetching today's trending searches (US)...")
        try:
            time.sleep(self.delay)
            df = self.pytrends.trending_searches(pn="united_states")
            df.columns = ["trending_topic"]
            return df
        except Exception as exc:
            log.warning(f"  ↳ Could not fetch trending searches: {exc}")
            return pd.DataFrame()

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

    # ── BeautifulSoup enrichment ──────────────────────────────────────────────

    def scrape_trending_page(self) -> list[dict]:
        """
        Scrape Google Trends 'Trending Now' page with BeautifulSoup
        for supplemental trend metadata.
        """
        log.info("Scraping Google Trends trending page with BeautifulSoup...")
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
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
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
                log.info(f"  ↳ Found {len(trends)} trending topics via BeautifulSoup")
            else:
                log.info("  ↳ No structured cards found (Google may have updated HTML)")
            return trends

        except requests.RequestException as exc:
            log.warning(f"  ↳ BeautifulSoup scrape failed: {exc}")
            return []

    # ── Export ────────────────────────────────────────────────────────────────

    def export_to_csv(self, output_path: str, data: dict) -> None:
        """
        Write all collected data to a single flat CSV file.
        Each row includes: date, keyword, group, interest_score, region, type.
        A second CSV is written for related queries / suggestions.
        """
        log.info(f"Exporting CSV to {output_path} ...")
        rows = []

        # ── 1. Interest Over Time ─────────────────────────────────────────────
        iot = data.get("interest_over_time")
        if iot is not None and not iot.empty:
            df = iot.reset_index()
            group_col = "group" if "group" in df.columns else None
            keyword_cols = [c for c in df.columns if c not in ("date", "group", "isPartial")]
            for _, row in df.iterrows():
                for kw in keyword_cols:
                    rows.append({
                        "section":         "interest_over_time",
                        "date":            str(row["date"])[:10],
                        "keyword":         kw,
                        "group":           row.get("group", "") if group_col else "",
                        "interest_score":  row[kw],
                        "region":          "",
                        "query_type":      "",
                        "related_term":    "",
                        "related_value":   "",
                        "suggestion_type": "",
                    })

        # ── 2. Interest by Region ─────────────────────────────────────────────
        ibr = data.get("interest_by_region")
        if ibr is not None and not ibr.empty:
            df = ibr.reset_index()
            keyword_cols = [c for c in df.columns if c != "geoName"]
            for _, row in df.iterrows():
                for kw in keyword_cols:
                    rows.append({
                        "section":         "interest_by_region",
                        "date":            "",
                        "keyword":         kw,
                        "group":           "",
                        "interest_score":  row[kw],
                        "region":          row.get("geoName", ""),
                        "query_type":      "",
                        "related_term":    "",
                        "related_value":   "",
                        "suggestion_type": "",
                    })

        # ── 3. Related Queries ────────────────────────────────────────────────
        rq = data.get("related_queries", {})
        for keyword, qdata in rq.items():
            for qtype in ("top", "rising"):
                df = qdata.get(qtype)
                if isinstance(df, pd.DataFrame) and not df.empty:
                    for _, row in df.iterrows():
                        rows.append({
                            "section":         "related_queries",
                            "date":            "",
                            "keyword":         keyword,
                            "group":           "",
                            "interest_score":  "",
                            "region":          "",
                            "query_type":      qtype,
                            "related_term":    row.get("query", ""),
                            "related_value":   row.get("value", ""),
                            "suggestion_type": "",
                        })

        # ── 4. Suggestions ────────────────────────────────────────────────────
        sugg = data.get("suggestions")
        if sugg is not None and not sugg.empty:
            for _, row in sugg.iterrows():
                rows.append({
                    "section":         "suggestions",
                    "date":            "",
                    "keyword":         row.get("search_term", ""),
                    "group":           "",
                    "interest_score":  "",
                    "region":          "",
                    "query_type":      "",
                    "related_term":    row.get("suggestion_title", ""),
                    "related_value":   "",
                    "suggestion_type": row.get("suggestion_type", ""),
                })

        # ── 5. Trending Now (BeautifulSoup) ───────────────────────────────────
        for item in data.get("trending_page", []):
            rows.append({
                "section":         "trending_now",
                "date":            item.get("scraped_at", "")[:10],
                "keyword":         item.get("title", ""),
                "group":           "",
                "interest_score":  item.get("search_volume", ""),
                "region":          "US",
                "query_type":      "",
                "related_term":    "",
                "related_value":   "",
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

            # Sheet 1: Interest Over Time
            if "interest_over_time" in data and not data["interest_over_time"].empty:
                df = data["interest_over_time"].reset_index()
                df.to_excel(writer, sheet_name="Interest Over Time", index=False)

            # Sheet 2: Interest by Region
            if "interest_by_region" in data and not data["interest_by_region"].empty:
                data["interest_by_region"].reset_index().to_excel(
                    writer, sheet_name="By Region", index=False
                )

            # Sheet 3–4: Related Queries (Top + Rising)
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

            # Sheet 5: Suggestions
            if "suggestions" in data and not data["suggestions"].empty:
                data["suggestions"].to_excel(writer, sheet_name="Suggestions", index=False)

            # Sheet 6: Trending Now (BeautifulSoup)
            bs_data = data.get("trending_page", [])
            if bs_data:
                pd.DataFrame(bs_data).to_excel(writer, sheet_name="Trending Now (BS4)", index=False)

            # Sheet 7: Run metadata
            meta = pd.DataFrame([{
                "run_at": datetime.now().isoformat(),
                "geo": self.geo,
                "timeframe": self.timeframe,
                "product_groups_scraped": len(PRODUCT_GROUPS),
                "category_keywords": ", ".join(CATEGORY_KEYWORDS),
            }])
            meta.to_excel(writer, sheet_name="Metadata", index=False)

        log.info(f"✓ Export complete → {output_path}")

    # ── Main orchestrator ─────────────────────────────────────────────────────

    def run(self, output_path: str, csv_only: bool = False) -> None:
        """Run the full scrape pipeline and export results."""
        log.info("=" * 60)
        log.info("Starting Google Trends scrape for specialty grocery products")
        log.info("=" * 60)

        collected = {}

        collected["interest_over_time"] = self.get_interest_over_time()
        collected["interest_by_region"] = self.get_interest_by_region()
        collected["related_queries"]    = self.get_related_queries()
        collected["related_topics"]     = self.get_related_topics()
        collected["suggestions"]        = self.get_suggestions()
        collected["trending_page"]      = self.scrape_trending_page()

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


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Google Trends scraper for Asian grocery & specialty products"
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
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    scraper = GoogleTrendsScraper(
        geo=args.geo,
        timeframe=args.timeframe,
        delay=args.delay,
    )
    scraper.run(output_path=args.output, csv_only=args.csv_only)
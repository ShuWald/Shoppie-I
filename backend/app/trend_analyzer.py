import os
from math import ceil
from typing import List, Tuple
from .models import TrendingProduct
from .csv_data_processor import CSVDataProcessor
from .flexlog import log_message

# Fetches trend data 
class TrendAnalyzer:
    def __init__(self, csv_path: str = None):
        default_csv_path = os.path.join(os.path.dirname(__file__), "trends_data.csv")
        self.csv_path = csv_path or default_csv_path
        self.csv_processor = CSVDataProcessor(self.csv_path)
        self._cached_products: List[TrendingProduct] = []
        self._cache_initialized = False
        self.max_page_size = 500
    
    def preload_products(self) -> None:
        """Warm the CSV cache at startup to reduce first-request latency."""
        self._load_products(force_reload=True)

    def fetch_trending_products(self, page: int = 1, page_size: int = 10) -> Tuple[List[TrendingProduct], int]:
        """
        Fetch paginated trending products from CSV cache.

        Returns:
            (products_for_requested_page, total_available_products)
        """
        safe_page = max(1, page)
        safe_page_size = max(1, min(page_size, self.max_page_size))

        if safe_page != page or safe_page_size != page_size:
            log_message(
                f"[TrendAnalyzer] Normalized pagination request page={page}, page_size={page_size} "
                f"-> page={safe_page}, page_size={safe_page_size}",
                additional_route="trend_analyzer",
            )

        products = self._load_products()
        total_available = len(products)

        start_idx = (safe_page - 1) * safe_page_size
        end_idx = start_idx + safe_page_size

        if start_idx >= total_available:
            total_pages = ceil(total_available / safe_page_size) if total_available else 0
            log_message(
                f"[TrendAnalyzer] Requested page={safe_page} out of range (total_pages={total_pages}); returning 0 products",
                additional_route="trend_analyzer",
            )
            return [], total_available

        paginated_products = products[start_idx:end_idx]
        log_message(
            f"[TrendAnalyzer] Returning {len(paginated_products)} products for page={safe_page}, "
            f"page_size={safe_page_size}, total_available={total_available}",
            additional_route="trend_analyzer",
        )
        return paginated_products, total_available

    def _load_products(self, force_reload: bool = False) -> List[TrendingProduct]:
        if self._cache_initialized and not force_reload:
            return self._cached_products

        log_message(f"[TrendAnalyzer] Loading trend data from CSV: {self.csv_path}", additional_route="trend_analyzer")
        products = self.csv_processor.get_unique_products()
        products.sort(key=lambda product: product.trend_score, reverse=True)

        self._cached_products = products
        self._cache_initialized = True

        log_message(f"[TrendAnalyzer] Cached {len(products)} unique products", additional_route="trend_analyzer")
        return self._cached_products

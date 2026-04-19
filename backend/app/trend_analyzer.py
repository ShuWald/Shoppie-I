# All of this is mock data, needs to be replaced with real data fetching logic

import requests
from typing import List, Dict
from datetime import datetime
import json
import random
from .models import TrendingProduct, ProductCategory
from .flexlog import log_message

# Fetches trend data 
class TrendAnalyzer:
    def __init__(self):
        self.trend_sources = [
            "google_trends",
            "social_media", 
            "market_research",
            "industry_reports"
        ]
    
    # Simulate fetching data and return as a TrendingProduct
    # Will probably need a lot of validation logic especially if we use different data sources
    def fetch_trending_products(self) -> List[TrendingProduct]:
        """Simulate fetching trending health/wellness products from various sources"""
        log_message("[TrendAnalyzer] Fetching trending products", additional_route="trend_analyzer")
        trending_data = self._get_mock_trending_data()
        log_message(f"[TrendAnalyzer] Raw items fetched: {len(trending_data)}", additional_route="trend_analyzer")
        products = []
        
        for idx, item in enumerate(trending_data, 1):
            try:
                product = TrendingProduct(
                    name=item["name"],
                    category=ProductCategory(item["category"]),
                    description=item["description"],
                    trend_score=item["trend_score"],
                    market_growth_rate=item["market_growth_rate"],
                    consumer_interest_score=item["consumer_interest_score"],
                    source=item["source"],
                    trend_keywords=item["trend_keywords"]
                )
                products.append(product)
            except Exception as e:
                product_name = item.get("name", f"item_{idx}") if isinstance(item, dict) else f"item_{idx}"
                log_message(f"[TrendAnalyzer] Skipping invalid product payload: {product_name}", print_log=True, additional_route="trend_analyzer")
                log_message(f"[TrendAnalyzer] Exception type: {type(e).__name__}", additional_route="trend_analyzer")
                continue

        log_message(f"[TrendAnalyzer] Valid products ready: {len(products)}", additional_route="trend_analyzer")
        
        return products
    
    # Generates fake data
    def _get_mock_trending_data(self) -> List[Dict]:
        """Mock data for trending health/wellness products"""
        return [
            {
                "name": "Adaptogenic Mushroom Coffee",
                "category": "Herbal Supplement",
                "description": "Coffee infused with functional mushrooms like lion's mane and reishi for stress relief and focus",
                "trend_score": 87,
                "market_growth_rate": 45,
                "consumer_interest_score": 92,
                "source": "social_media",
                "trend_keywords": ["adaptogens", "functional mushrooms", "stress relief", "focus"]
            },
            {
                "name": "Organic Ginger Turmeric Elixir",
                "category": "Ginger",
                "description": "Concentrated liquid supplement combining organic ginger and turmeric for anti-inflammatory benefits",
                "trend_score": 79,
                "market_growth_rate": 38,
                "consumer_interest_score": 85,
                "source": "market_research",
                "trend_keywords": ["anti-inflammatory", "organic ginger", "turmeric", "immune support"]
            },
            {
                "name": "CBD-Infused Herbal Tea",
                "category": "Tea",
                "description": "Relaxing tea blends with CBD for anxiety relief and better sleep",
                "trend_score": 72,
                "market_growth_rate": 42,
                "consumer_interest_score": 78,
                "source": "industry_reports",
                "trend_keywords": ["cbd", "herbal tea", "anxiety relief", "sleep"]
            },
            {
                "name": "Fermented Ginseng Shots",
                "category": "Ginseng",
                "description": "Ready-to-drink fermented ginseng shots for energy and immune support",
                "trend_score": 68,
                "market_growth_rate": 35,
                "consumer_interest_score": 71,
                "source": "google_trends",
                "trend_keywords": ["fermented", "ginseng", "energy shots", "immune support"]
            },
            {
                "name": "Medicinal Mushroom Complex",
                "category": "Herbal Supplement",
                "description": "Multi-mushroom supplement featuring reishi, chaga, cordyceps for overall wellness",
                "trend_score": 75,
                "market_growth_rate": 48,
                "consumer_interest_score": 80,
                "source": "social_media",
                "trend_keywords": ["medicinal mushrooms", "reishi", "chaga", "wellness"]
            },
            {
                "name": "Organic Honey Loquat Syrup",
                "category": "Honey",
                "description": "Traditional honey-based cough and throat relief syrup with loquat extract",
                "trend_score": 65,
                "market_growth_rate": 28,
                "consumer_interest_score": 68,
                "source": "market_research",
                "trend_keywords": ["honey", "loquat", "cough relief", "traditional remedy"]
            },
            {
                "name": "Herbal Pain Relief Patches",
                "category": "Pain Relief",
                "description": "Topical patches with natural herbs for muscle and joint pain relief",
                "trend_score": 70,
                "market_growth_rate": 33,
                "consumer_interest_score": 74,
                "source": "industry_reports",
                "trend_keywords": ["pain relief", "topical", "herbal", "muscle pain"]
            },
            {
                "name": "Matcha Ginger Energy Drinks",
                "category": "Ginger",
                "description": "Natural energy drinks combining matcha green tea and ginger for sustained energy",
                "trend_score": 73,
                "market_growth_rate": 41,
                "consumer_interest_score": 76,
                "source": "google_trends",
                "trend_keywords": ["matcha", "ginger", "energy drinks", "natural caffeine"]
            }
        ]

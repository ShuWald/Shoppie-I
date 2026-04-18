"""
CSV Data Processor - Converts webscraped CSV data to TrendingProduct objects
"""
import pandas as pd
from typing import List
from .models import TrendingProduct, ProductCategory
import re

class CSVDataProcessor:
    """Processes webscraped CSV data and converts to TrendingProduct objects"""
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.df = None
        
    def load_data(self) -> pd.DataFrame:
        """Load and preprocess CSV data"""
        try:
            self.df = pd.read_csv(self.csv_path)
            print(f"Loaded {len(self.df)} rows from {self.csv_path}")
            return self.df
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return pd.DataFrame()
    
    def categorize_product(self, keyword: str, group: str) -> ProductCategory:
        """Categorize product based on keyword and group"""
        keyword_lower = keyword.lower()
        group_lower = group.lower()
        
        # Check for ginseng products
        if any(term in keyword_lower for term in ['ginseng', 'american ginseng']):
            return ProductCategory.GINSENG
        
        # Check for ginger products
        if any(term in keyword_lower for term in ['ginger', 'ginger chews']):
            return ProductCategory.GINGER
        
        # Check for tea products
        if any(term in keyword_lower for term in ['tea', 'green tea', 'jasmine tea', 'oolong tea', 'white tea']):
            return ProductCategory.TEA
        
        # Check for herbal supplements
        if any(term in keyword_lower for term in ['herbal', 'supplement', 'blood pressure', 'cholesterol']):
            return ProductCategory.HERBAL_SUPPLEMENT
        
        # Check for pain relief
        if any(term in keyword_lower for term in ['tiger balm', 'pain', 'relief']):
            return ProductCategory.PAIN_RELIEF
        
        # Default to herbal supplement for unknown categories
        return ProductCategory.HERBAL_SUPPLEMENT
    
    def calculate_trend_score(self, interest_score: float, section: str) -> float:
        """Calculate trend score from interest score and section"""
        if pd.isna(interest_score) or interest_score == 0:
            return 10.0  # Default low score for no data
        
        # Normalize interest score to 0-100 scale
        # Google Trends interest is typically 0-100, but we'll cap and normalize
        normalized_score = min(float(interest_score), 100.0)
        
        # Boost score for certain sections
        if section == 'interest_over_time':
            return normalized_score * 0.8  # High reliability
        elif section == 'related_queries':
            return normalized_score * 0.6  # Medium reliability
        elif section == 'suggestions':
            return normalized_score * 0.4  # Lower reliability
        else:
            return normalized_score * 0.5  # Default
    
    def extract_keywords(self, keyword: str, group: str) -> List[str]:
        """Extract relevant keywords from product data"""
        keywords = []
        
        # Add main keyword
        keywords.append(keyword.lower())
        
        # Add group as keyword
        if group and pd.notna(group):
            keywords.append(group.lower())
        
        # Extract additional keywords from the main keyword
        # Split on common separators and clean
        parts = re.split(r'[,;|]', keyword)
        for part in parts:
            clean_part = part.strip().lower()
            if len(clean_part) > 2:  # Only keep meaningful parts
                keywords.append(clean_part)
        
        # Remove duplicates and return
        return list(set(keywords))
    
    def get_unique_products(self) -> List[TrendingProduct]:
        """Convert CSV data to unique TrendingProduct objects"""
        if self.df is None:
            self.load_data()
        
        if self.df.empty:
            return []
        
        # Group by keyword to get unique products
        unique_products = {}
        
        for _, row in self.df.iterrows():
            keyword = str(row.get('keyword', '')).strip()
            group = str(row.get('group', '')).strip()
            section = str(row.get('section', '')).strip()
            interest_score = row.get('interest_score', 0)
            
            if not keyword or keyword == 'nan':
                continue
            
            # Create product key
            product_key = f"{keyword}_{group}"
            
            # If we haven't seen this product yet, create it
            if product_key not in unique_products:
                category = self.categorize_product(keyword, group)
                trend_score = self.calculate_trend_score(interest_score, section)
                keywords = self.extract_keywords(keyword, group)
                
                unique_products[product_key] = TrendingProduct(
                    name=keyword,
                    category=category,
                    description=f"Trending product from {group} category with interest score {interest_score}",
                    trend_score=trend_score,
                    market_growth_rate=trend_score * 0.8,  # Estimate based on trend score
                    consumer_interest_score=trend_score * 0.9,  # Estimate based on trend score
                    source="Google Trends CSV Data",
                    trend_keywords=keywords
                )
            else:
                # Update existing product with better data if available
                existing_product = unique_products[product_key]
                new_trend_score = self.calculate_trend_score(interest_score, section)
                
                # Keep the higher trend score
                if new_trend_score > existing_product.trend_score:
                    existing_product.trend_score = new_trend_score
                    existing_product.market_growth_rate = new_trend_score * 0.8
                    existing_product.consumer_interest_score = new_trend_score * 0.9
                    existing_product.description = f"Updated: {group} category with interest score {interest_score}"
        
        return list(unique_products.values())
    
    def get_products_by_category(self) -> dict:
        """Get products grouped by category"""
        products = self.get_unique_products()
        categorized = {}
        
        for product in products:
            category = product.category.value
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(product)
        
        return categorized
    
    def get_top_products(self, limit: int = 10) -> List[TrendingProduct]:
        """Get top products by trend score"""
        products = self.get_unique_products()
        # Sort by trend score descending
        products.sort(key=lambda x: x.trend_score, reverse=True)
        return products[:limit]

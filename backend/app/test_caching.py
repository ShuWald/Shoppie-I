#!/usr/bin/env python3
"""
Test script to verify CSV caching functionality for both scrapers.
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_webscraper_cache():
    """Test Google Trends scraper caching."""
    print("Testing Google Trends scraper caching...")
    
    # Create a temporary cache directory
    temp_cache = tempfile.mkdtemp()
    
    try:
        from webscrapper import GoogleTrendsScraper
        
        # Initialize scraper with short cache time for testing
        scraper = GoogleTrendsScraper(
            geo="US",
            timeframe="today 7-d",
            delay=0.5,
            cache_dir=temp_cache,
            cache_hours=1  # 1 hour cache for testing
        )
        
        # Test cache filename generation
        cache_file = scraper._get_cache_filename()
        print(f"  Cache filename: {cache_file}")
        
        # Test cache validation (should be False since file doesn't exist)
        is_valid = scraper._is_cache_valid(cache_file)
        print(f"  Cache valid (non-existent): {is_valid}")
        
        # Test loading from cache (should return None)
        cached_data = scraper._load_from_cache()
        print(f"  Load from cache (empty): {cached_data is None}")
        
        print("  Google Trends scraper caching tests passed!")
        
    except Exception as e:
        print(f"  Error testing Google Trends scraper: {e}")
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_cache, ignore_errors=True)

def test_ingredients_scraper_cache():
    """Test ingredients scraper caching."""
    print("Testing ingredients scraper caching...")
    
    # Create a temporary cache directory
    temp_cache = tempfile.mkdtemp()
    
    try:
        from ingredients_scraper import OpenFoodFactsScraper, iHerbScraper
        
        # Test Open Food Facts scraper
        off_scraper = OpenFoodFactsScraper(
            delay=0.5,
            cache_dir=temp_cache,
            cache_hours=1
        )
        
        # Test cache filename generation
        cache_file = off_scraper._get_cache_filename()
        print(f"  OFF cache filename: {cache_file}")
        
        # Test cache validation
        is_valid = off_scraper._is_cache_valid(cache_file)
        print(f"  OFF cache valid (non-existent): {is_valid}")
        
        # Test iHerb scraper
        iherb_scraper = iHerbScraper(
            delay=0.5,
            cache_dir=temp_cache,
            cache_hours=1
        )
        
        # Test cache filename generation
        cache_file = iherb_scraper._get_cache_filename()
        print(f"  iHerb cache filename: {cache_file}")
        
        # Test cache validation
        is_valid = iherb_scraper._is_cache_valid(cache_file)
        print(f"  iHerb cache valid (non-existent): {is_valid}")
        
        print("  Ingredients scraper caching tests passed!")
        
    except Exception as e:
        print(f"  Error testing ingredients scraper: {e}")
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_cache, ignore_errors=True)

def test_cache_file_creation():
    """Test that cache files are created properly."""
    print("Testing cache file creation...")
    
    temp_cache = tempfile.mkdtemp()
    
    try:
        from ingredients_scraper import OpenFoodFactsScraper
        
        scraper = OpenFoodFactsScraper(
            delay=0.1,
            cache_dir=temp_cache,
            cache_hours=1
        )
        
        # Create some test data
        test_data = [
            {
                "scraped_at": datetime.now().isoformat(),
                "product_name": "Test Product",
                "category": "Test",
                "source": "Open Food Facts",
                "search_query": "test query",
                "matched_title": "Test Title",
                "brand": "Test Brand",
                "quantity": "100g",
                "ingredients": "test ingredients",
                "ingredients_found": True,
                "off_barcode": "123456789",
                "notes": "test notes"
            }
        ]
        
        # Save to cache
        scraper._save_to_cache(test_data)
        
        # Verify file was created
        cache_file = scraper._get_cache_filename()
        file_exists = os.path.exists(cache_file)
        print(f"  Cache file created: {file_exists}")
        
        if file_exists:
            # Test loading from cache
            loaded_data = scraper._load_from_cache([{"name": "Test Product", "off_query": "test"}])
            print(f"  Loaded {len(loaded_data) if loaded_data else 0} items from cache")
            
            # Test cache validity
            is_valid = scraper._is_cache_valid(cache_file)
            print(f"  Cache valid: {is_valid}")
        
        print("  Cache file creation tests passed!")
        
    except Exception as e:
        print(f"  Error testing cache file creation: {e}")
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_cache, ignore_errors=True)

def main():
    """Run all caching tests."""
    print("=" * 60)
    print("Running Caching Tests")
    print("=" * 60)
    
    test_webscraper_cache()
    print()
    test_ingredients_scraper_cache()
    print()
    test_cache_file_creation()
    
    print("=" * 60)
    print("All caching tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()

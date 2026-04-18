#!/usr/bin/env python3
"""
Integration script to feed webscraper data to evaluator
"""
import sys
import os

# Add app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from evaluator import ProductEvaluator
from webscraper import GoogleTrendsScraper

def run_webscraper_to_evaluator():
    """Run webscraper and feed data to evaluator"""
    print("=== Webscraper to Evaluator Integration ===\n")
    
    # Step 1: Initialize webscraper and get CSV data
    print("1. Initializing webscraper...")
    try:
        scraper = GoogleTrendsScraper(
            geo="US",
            timeframe="today 12-m",
            delay=2.5
        )
        print("   [OK] Webscraper initialized")
    except Exception as e:
        print(f"   [ERROR] Failed to initialize webscraper: {e}")
        return
    
    # Step 2: Get TrendingProduct objects from CSV
    print("2. Loading products from CSV...")
    try:
        products = scraper.get_trending_products_for_evaluator("trends_data.csv")
        print(f"   [OK] Loaded {len(products)} products")
        
        if not products:
            print("   [WARNING] No products found in CSV")
            return
        
        # Show sample products
        print("   Sample products:")
        for i, product in enumerate(products[:3]):
            print(f"     {i+1}. {product.name} ({product.category.value}) - Score: {product.trend_score:.1f}")
        print()
        
    except Exception as e:
        print(f"   [ERROR] Failed to load products: {e}")
        return
    
    # Step 3: Initialize evaluator and run evaluation
    print("3. Running evaluator...")
    try:
        evaluator = ProductEvaluator()
        print("   [OK] Evaluator initialized")
        
        # Run the full evaluation pipeline
        report = evaluator.evaluate_trending_products()
        print(f"   [OK] Evaluation complete")
        print()
        
        # Display results
        print("4. Evaluation Results:")
        print(f"   Total products evaluated: {report.total_products_evaluated}")
        print(f"   High priority products: {len(report.high_priority_products)}")
        print(f"   Medium priority products: {len(report.medium_priority_products)}")
        print(f"   Low priority products: {len(report.low_priority_products)}")
        print()
        
        # Show top products
        if report.high_priority_products:
            print("   Top High Priority Products:")
            for i, evaluation in enumerate(report.high_priority_products[:3]):
                print(f"     {i+1}. {evaluation.product.name}")
                print(f"        PoP Score: {evaluation.pop_relevance_score:.1f}")
                print(f"        Suggested Action: {evaluation.suggested_action.value}")
                print(f"        Confidence: {evaluation.confidence_score:.1f}%")
                print()
        
        # Show summary insights
        if report.summary_insights:
            print("   Summary Insights:")
            for insight in report.summary_insights[:5]:
                print(f"     - {insight}")
        
        print(f"\n   Report generated at: {report.generated_at}")
        
    except Exception as e:
        print(f"   [ERROR] Evaluation failed: {e}")
        return
    
    print("\n=== Integration Complete ===")

if __name__ == "__main__":
    run_webscraper_to_evaluator()

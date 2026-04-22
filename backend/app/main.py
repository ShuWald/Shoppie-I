from typing import List
from .filter import (
    get_fda_substances_endpoint,
    check_restricted_ingredients,
    estimate_shelf_life_endpoint,
    check_tariffs_endpoint,
)
from typing import Annotated
from datetime import datetime
import json
import os
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from .evaluator import ProductEvaluator
from .models import TrendingReport, ProductCategory
from .flexlog import log_message

#NOTES AT BOTTOM OF FILE

# Initialize evaluator from evaluator.py
evaluator = ProductEvaluator()


def _run_precache(start_page: int = 1, page_count: int = 1, batch_size: int = 10):
    """Shared pre-cache helper function to reduce code duplication."""
    def pre_cache_task():
        try:
            log_message(f"[main] Starting pre-caching for pages {start_page}-{start_page + page_count - 1}", print_log=True)
            
            total_cached = 0
            for page_num in range(start_page, start_page + page_count):
                # Get products for this page
                products, _ = evaluator.trend_analyzer.fetch_trending_products(page=page_num, page_size=batch_size)
                
                # Evaluate and cache them
                batch_evaluations = evaluator._evaluate_products_batch(products)
                
                # Store in cache with proper global index
                start_index = (page_num - 1) * batch_size
                evaluated_items = {}
                for j, evaluation in enumerate(batch_evaluations):
                    global_index = start_index + j
                    evaluated_items[global_index] = evaluation
                
                evaluator.evaluation_cache.store_request_items(
                    start_index=start_index,
                    request_count=batch_size,
                    evaluated_items=evaluated_items
                )
                
                total_cached += len(batch_evaluations)
                log_message(f"[main] Pre-cached page {page_num}/{start_page + page_count - 1}", print_log=True)
                
            log_message(f"[main] Pre-caching completed successfully - {total_cached} products cached", print_log=True)
        except Exception as e:
            log_message(f"[main] Pre-caching failed: {str(e)}", print_log=True)
            log_message(f"[main] Exception type: {type(e).__name__}", print_log=True)
    
    # Run in background thread
    thread = threading.Thread(target=pre_cache_task, daemon=True)
    thread.start()
    return thread


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup logic
    try:
        # First preload the CSV data
        evaluator.trend_analyzer.preload_products()
        log_message("[main] Preloaded trend data cache", additional_route="main")
        
        # Then pre-cache all product evaluations
        def pre_cache_evaluations():
            try:
                log_message("[main] Starting pre-caching of all product evaluations", print_log=True)
                all_products, total_available = evaluator.trend_analyzer.fetch_trending_products(page=1, page_size=500)
                
                # Process in smaller batches for better performance
                batch_size = 10
                for i in range(0, len(all_products), batch_size):
                    batch = all_products[i:i+batch_size]
                    
                    # Evaluate batch
                    batch_evaluations = evaluator._evaluate_products_batch(batch)
                    
                    # Store each evaluation in cache with proper global index
                    for j, evaluation in enumerate(batch_evaluations):
                        global_index = i + j
                        evaluator.evaluation_cache.store_request_items(
                            start_index=global_index,
                            request_count=1,
                            evaluated_items={global_index: evaluation}
                        )
                    
                    if i % 50 == 0:  # Log progress every 50 items
                        log_message(f"[main] Pre-cached {min(i + batch_size, len(all_products))}/{len(all_products)} products", print_log=True)
                        
                log_message(f"[main] Pre-caching completed - {len(all_products)} products cached", print_log=True)
            except Exception as e:
                log_message(f"[main] Pre-caching failed: {str(e)}", print_log=True)
                log_message(f"[main] Exception type: {type(e).__name__}", print_log=True)
        
        # Run pre-caching in background thread
        cache_thread = threading.Thread(target=pre_cache_evaluations, daemon=True)
        cache_thread.start()
        
    except Exception as e:
        log_message("[main] Failed to preload trend data cache", print_log=True, additional_route="main")
        log_message(f"[main] Exception type: {type(e).__name__}", additional_route="main")
    
    yield
    
    # Shutdown logic (if needed)
    log_message("[main] Application shutdown", additional_route="main")

'''
--------------------------------
App Initialization (create webserver)
--------------------------------
'''
app = FastAPI(
    title="Prince of Peace Trending Products Evaluator",
    description="AI-powered tool to evaluate trending health/wellness products for Prince of Peace",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for local development - allow all localhost origins
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:58427",
    "http://localhost:8080",  # Alternative development ports
    "http://127.0.0.1:8080",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    "http://localhost:3003",
    "http://127.0.0.1:3003",
    "*",  # Fallback for any localhost origin
]

# Add production origins from environment variable if available
if os.getenv("ALLOWED_ORIGINS"):
    allowed_origins.extend(os.getenv("ALLOWED_ORIGINS").split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600  # Cache-busting for CORS headers
)

# Initialize evaluator from evaluator.py
evaluator = ProductEvaluator()


'''
--------------------------------
API Endpoints
--------------------------------
'''
#API running check (root endpoint)
@app.get("/")
async def root():
    return {"message": "Prince of Peace Trending Products Evaluator API"}

#Main Endpoint (trend report, formatting, error handling)
@app.post("/api/pre-cache-first-pages")
async def pre_cache_first_pages():
    """Pre-cache first few pages for immediate pagination performance"""
    try:
        # Pre-cache first 5 pages (50 products) synchronously
        pages_to_cache = 5
        products_per_page = 10
        
        log_message(f"[main] Pre-caching first {pages_to_cache} pages ({pages_to_cache * products_per_page} products)", print_log=True)
        
        # Use shared helper function
        _run_precache(start_page=1, page_count=pages_to_cache, batch_size=products_per_page)
        
        return {"message": f"Pre-cached first {pages_to_cache} pages successfully", "pages_cached": pages_to_cache}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pre-caching failed: {str(e)}")

@app.post("/api/pre-cache-all-products")
async def pre_cache_all_products():
    """Pre-cache all product evaluations in background for faster pagination"""
    try:
        # Get total product count to calculate pages needed
        _, total_available = evaluator.trend_analyzer.fetch_trending_products(page=1, page_size=1)
        products_per_page = 20  # Use larger batch size for full caching
        pages_needed = (total_available + products_per_page - 1) // products_per_page
        
        log_message(f"[main] Starting pre-caching for all {total_available} products ({pages_needed} pages)", print_log=True)
        
        # Use shared helper function for all products
        _run_precache(start_page=1, page_count=pages_needed, batch_size=products_per_page)
        
        return {"message": "Pre-caching started in background", "status": "processing", "total_products": total_available, "pages_to_cache": pages_needed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pre-caching failed to start: {str(e)}")

@app.get("/api/pre-cache-status")
async def get_pre_cache_status():
    """Get current pre-caching status"""
    try:
        # Count total cached items across all groups
        total_cached = 0
        for group in evaluator.evaluation_cache._groups:
            total_cached += len(group.items)
        
        # Get total product count dynamically instead of hardcoded 326
        _, total_available = evaluator.trend_analyzer.fetch_trending_products(page=1, page_size=1)
        
        return {
            "cache_size": total_cached,
            "max_cache_size": evaluator.evaluation_cache.max_items,
            "cache_hit_rate": f"{(total_cached / total_available * 100):.1f}%" if total_cached > 0 else "0%",
            "status": "ready" if total_cached >= (total_available * 0.9) else "processing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache status: {str(e)}")

@app.get("/api/evaluate-trending-products")
async def evaluate_trending_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=500),
    stream: bool = Query(default=False),
):
    """Evaluate trending products with pagination and optional streaming using async pipeline"""
    try:
        log_message(f"[main] Request: page={page}, page_size={page_size}, stream={stream}", additional_route="main")
        
        if stream:
            return StreamingResponse(
                evaluator.stream_trending_products(page=page, page_size=page_size),
                media_type="application/x-ndjson"
            )
        else:
            report = await evaluator.evaluate_trending_products(page=page, page_size=page_size)
            return JSONResponse(content=report.model_dump(mode="json"))
            
    except Exception as e:
        log_message(f"[main] ERROR in evaluate_trending_products: {str(e)}", print_log=True, additional_route="main")
        log_message(f"[main] Exception type: {type(e).__name__}", additional_route="main")
        raise HTTPException(status_code=500, detail=str(e))


#Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "PoP Trending Products Evaluator"}

@app.get("/api/test-connection")
async def test_connection():
    """Simple test endpoint to verify frontend can connect to backend"""
    return {"message": "Connection successful", "timestamp": datetime.now().isoformat()}

@app.post("/api/test-post")
async def test_post():
    """Simple POST test endpoint to debug frontend POST requests"""
    return {"message": "POST request successful", "timestamp": datetime.now().isoformat()}

@app.get("/api/test-stream")
async def test_stream():
    """Simple test streaming endpoint to debug frontend connectivity"""
    from fastapi.responses import StreamingResponse
    
    async def generate_test():
        yield json.dumps({"type": "test", "message": "Hello from backend"}) + "\n"
        yield json.dumps({"type": "test", "message": "Second line"}) + "\n"
        yield json.dumps({"type": "complete", "message": "Test complete"}) + "\n"
    
    return StreamingResponse(generate_test(), media_type="application/x-ndjson")

@app.get("/api/test-simple-stream")
async def test_simple_stream():
    """Simplified version of main streaming endpoint to isolate issues"""
    from fastapi.responses import StreamingResponse
    
    async def generate_simple():
        # Send meta
        yield json.dumps({
            "type": "meta",
            "page": 1,
            "page_size": 3,
            "total_products_available": 330,
            "total_products_to_evaluate": 3,
            "total_pages": 110,
            "cache_hits": 0,
            "cache_misses": 3
        }) + "\n"
        
        # Send simple test items
        for i in range(1, 4):
            yield json.dumps({
                "type": "item",
                "index": i,
                "total": 3,
                "priority": "medium",
                "from_cache": False,
                "evaluation": {
                    "product": {"name": f"Test Product {i}"},
                    "pop_relevance_score": 65.0,
                    "suggested_action": "Test action"
                }
            }) + "\n"
        
        # Send complete
        yield json.dumps({
            "type": "complete",
            "report": {
                "generated_at": "2026-04-22T10:00:00",
                "total_products_evaluated": 3,
                "high_priority_products": [],
                "medium_priority_products": [],
                "low_priority_products": []
            }
        }) + "\n"
    
    return StreamingResponse(generate_simple(), media_type="application/x-ndjson")

@app.get("/api/evaluate-trending-products-async")
async def evaluate_trending_products_stream(page: int = 1, page_size: int = 10):
    """Async streaming endpoint that properly handles async evaluation"""
    from fastapi.responses import StreamingResponse
    
    async def generate_stream():
        try:
            # Get products
            trending_products, total_available = evaluator.trend_analyzer.fetch_trending_products(page=page, page_size=page_size)
            
            # Send meta
            yield json.dumps({
                "type": "meta",
                "page": page,
                "page_size": page_size,
                "total_products_available": total_available,
                "total_products_to_evaluate": len(trending_products),
                "total_pages": (total_available + page_size - 1) // page_size,
                "cache_hits": 0,
                "cache_misses": len(trending_products)
            }) + "\n"
            
            # Process products one by one to maintain streaming
            for idx, product in enumerate(trending_products, 1):
                try:
                    # Use async evaluation for each product
                    evaluation = await evaluator._evaluate_products_batch_async([product])
                    if evaluation:
                        eval_result = evaluation[0]
                        yield json.dumps({
                            "type": "item",
                            "index": idx,
                            "total": len(trending_products),
                            "priority": evaluator._priority_for_score(eval_result.pop_relevance_score),
                            "from_cache": False,
                            "evaluation": eval_result.model_dump(mode="json"),
                        }) + "\n"
                except Exception as e:
                    log_message(f"[main] Error evaluating product {product.name}: {str(e)}", print_log=True)
                    yield json.dumps({
                        "type": "item_error",
                        "index": idx,
                        "total": len(trending_products),
                        "product_name": product.name,
                        "exception_type": type(e).__name__,
                    }) + "\n"
            
            # Send complete
            yield json.dumps({
                "type": "complete",
                "report": {
                    "generated_at": datetime.now().isoformat(),
                    "total_products_evaluated": len(trending_products),
                    "high_priority_products": [],
                    "medium_priority_products": [],
                    "low_priority_products": []
                }
            }) + "\n"
            
        except Exception as e:
            log_message(f"[main] Streaming error: {str(e)}", print_log=True)
            yield json.dumps({
                "type": "fatal_error",
                "message": "Streaming failed",
                "exception_type": type(e).__name__,
            }) + "\n"
    
    return StreamingResponse(generate_stream(), media_type="application/x-ndjson")


# Filter endpoints
@app.get("/api/fda-substances")
async def fda_substances():
    return get_fda_substances_endpoint()


@app.post("/api/check-restricted")
async def check_restricted(ingredients: List[str]):
    return check_restricted_ingredients(ingredients)


@app.post("/api/estimate-shelf-life")
async def estimate_shelf_life(ingredients: List[str]):
    return estimate_shelf_life_endpoint(ingredients)


@app.post("/api/check-tariffs")
async def check_tariffs(country: str, threshold: float = 15.0):
    return check_tariffs_endpoint(country, threshold)


'''
--------------------------------
NOTES
--------------------------------
How it works:

1. User/frontend sends GET request to /api/evaluate-trending-products
2. FastAPI (this file) routes request to function 'ProductEvaluator'
3. Evaluator generates a 'TrendingReport'
4. FastAPI validates with Pydantic + converts to JSON
5. Returns JSON response to user/frontend

Built-In Advantages:

Automatic validation (via Pydantic models)
Auto-generated API docs (Swagger UI at /docs)
Type safety
Clean error handling
Frontend-ready (CORS enabled)

⚠️ Things to Note:

allow_origins=["*"]
→ Fine for development, but unsafe for production (should restrict domains)
No authentication
→ Anyone can call the API
Assumes ProductEvaluator is reliable
→ If it's slow or unstable, the API will be too
'''

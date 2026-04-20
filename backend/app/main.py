from typing import List
from .filter import (
    get_fda_substances_endpoint,
    check_restricted_ingredients,
    estimate_shelf_life_endpoint,
    check_tariffs_endpoint,
)
from typing import Annotated
import json
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from .evaluator import ProductEvaluator
from .models import TrendingReport, ProductCategory
from .flexlog import log_message

#NOTES AT BOTTOM OF FILE

'''
--------------------------------
App Initialization (create webserver)
--------------------------------
'''
app = FastAPI(
    title="Prince of Peace Trending Products Evaluator",
    description="AI-powered tool to evaluate trending health/wellness products for Prince of Peace",
    version="1.0.0"
)

# Enable CORS for frontend -> prevents frontend connection failure
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize evaluator from evaluator.py
evaluator = ProductEvaluator()


@app.on_event("startup")
async def preload_trending_products_cache():
    """Preload CSV trend data at startup to avoid first-request bottlenecks."""
    try:
        evaluator.trend_analyzer.preload_products()
        log_message("[main] Preloaded trend data cache", additional_route="main")
    except Exception as e:
        log_message("[main] Failed to preload trend data cache", print_log=True, additional_route="main")
        log_message(f"[main] Exception type: {type(e).__name__}", additional_route="main")

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
@app.get("/api/evaluate-trending-products")
async def evaluate_trending_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    stream: bool = Query(default=False),
):
    """
    Evaluate trending health/wellness products for Prince of Peace
    Returns a comprehensive report with prioritized recommendations
    """
    try:
        if stream:
            def ndjson_generator():
                for event in evaluator.stream_trending_products(page=page, page_size=page_size):
                    yield json.dumps(event) + "\n"

            return StreamingResponse(ndjson_generator(), media_type="application/x-ndjson")

        report = evaluator.evaluate_trending_products(page=page, page_size=page_size)
        # Use JSON mode so enums and nested values serialize as JSON-safe primitives.
        report_dict = report.model_dump(mode="json")
        return JSONResponse(content=report_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


#Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "PoP Trending Products Evaluator"}


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

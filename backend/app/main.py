from typing import List
from .filter import (
    get_fda_substances_endpoint,
    check_restricted_ingredients,
    estimate_shelf_life_endpoint,
    check_tariffs_endpoint,
)
from typing import Annotated
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .evaluator import ProductEvaluator
from .models import TrendingReport

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
@app.get("/api/evaluate-trending-products", response_model=TrendingReport)
async def evaluate_trending_products():
    """
    Evaluate trending health/wellness products for Prince of Peace
    Returns a comprehensive report with prioritized recommendations
    """
    try:
        report = evaluator.evaluate_trending_products()
        return report
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

from typing import Annotated
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .evaluator import ProductEvaluator
from .models import TrendingReport

app = FastAPI(
    title="Prince of Peace Trending Products Evaluator",
    description="AI-powered tool to evaluate trending health/wellness products for Prince of Peace",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize evaluator
evaluator = ProductEvaluator()

@app.get("/")
async def root():
    return {"message": "Prince of Peace Trending Products Evaluator API"}

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

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "PoP Trending Products Evaluator"}


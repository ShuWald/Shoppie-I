# Shoppie Backend Architecture Roadmap

## 🎯 Overview
This document maps the complete backend architecture, data flow, and integration status of all components in the Shoppie system. It identifies what's connected, what's disconnected, and provides recommendations for improvements.

---

## 📊 Current Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI Server │    │   Data Sources  │
│  (Next.js)      │◄──►│   (main.py)      │◄──►│  (CSV Files)    │
│ localhost:3000  │    │  localhost:8000  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Evaluation      │
                    │  Pipeline        │
                    │ (evaluator.py)   │
                    └──────────────────┘
```

---

## 🔗 Core Connected Components

### 1. **Main API Gateway** (`main.py`)
**Status:** ✅ **FULLY CONNECTED** - Primary entry point

**Purpose:**
- FastAPI application server
- Handles all HTTP requests from frontend
- Manages CORS, streaming responses, and caching
- Orchestrates the evaluation pipeline

**Key Endpoints:**
- `GET /api/evaluate-trending-products` - Main evaluation endpoint
- `POST /api/pre-cache-first-pages` - Pre-caching for performance
- `GET /api/categories` - Product categories
- `GET /api/health` - Health check

**Connections:**
- ✅ Frontend → main.py
- ✅ main.py → evaluator.py
- ✅ main.py → evaluation_cache.py

---

### 2. **Product Evaluator** (`evaluator.py`)
**Status:** ✅ **FULLY CONNECTED** - Core pipeline manager

**Purpose:**
- Orchestrates the complete evaluation workflow
- Manages batch processing and async operations
- Integrates all evaluation engines

**Pipeline Flow:**
1. Fetch trending products → `trend_analyzer.py`
2. Apply business rules → `business_rules.py`
3. Assess risks → `risk_assessment.py`
4. Score and rank → `scoring.py`
5. Cache results → `evaluation_cache.py`

**Connections:**
- ✅ main.py → evaluator.py
- ✅ evaluator.py → trend_analyzer.py
- ✅ evaluator.py → business_rules.py
- ✅ evaluator.py → risk_assessment.py
- ✅ evaluator.py → scoring.py
- ✅ evaluator.py → evaluation_cache.py

---

### 3. **Data Models** (`models.py`)
**Status:** ✅ **FULLY CONNECTED** - Type definitions

**Purpose:**
- Pydantic models for type safety
- Enums for controlled categories
- Data validation and serialization

**Key Models:**
- `TrendingProduct` - Raw trend data
- `ProductEvaluation` - Complete evaluation result
- `TrendingReport` - API response format
- `BusinessRuleEvaluation` - Business rule results
- `RiskAssessment` - Risk analysis results

**Connections:**
- ✅ Used by ALL components
- ✅ Ensures data consistency across pipeline

---

### 4. **Trend Analyzer** (`trend_analyzer.py`)
**Status:** ✅ **FULLY CONNECTED** - Data source manager

**Purpose:**
- Fetches trending products from CSV data
- Manages pagination and caching
- Provides product data to evaluator

**Data Source:**
- ✅ `trends_data.csv` - Primary data source (326 products)
- ✅ `csv_data_processor.py` - CSV parsing logic

**Connections:**
- ✅ evaluator.py → trend_analyzer.py
- ✅ trend_analyzer.py → csv_data_processor.py
- ✅ trend_analyzer.py → trends_data.csv

---

### 5. **Business Rules Engine** (`business_rules.py`)
**Status:** ✅ **FULLY CONNECTED** - Company alignment checker

**Purpose:**
- Evaluates products against Prince of Peace criteria
- Checks organic compatibility, traditional remedies, etc.
- Determines business alignment

**Rules Evaluated:**
- ✅ Organic compatibility
- ✅ Traditional remedy status
- ✅ Natural ingredients requirement
- ✅ Regulatory compliance feasibility
- ✅ Market alignment
- ✅ Supply chain feasibility

**Connections:**
- ✅ evaluator.py → business_rules.py

---

### 6. **Risk Assessment Engine** (`risk_assessment.py`)
**Status:** ✅ **FULLY CONNECTED** - Risk analysis

**Purpose:**
- Evaluates multiple risk dimensions
- Provides risk flags and concerns
- Supports decision-making process

**Risk Categories:**
- ✅ Tariff risk
- ✅ FDA regulatory concerns
- ✅ Supply chain risks
- ✅ Competition analysis

**Connections:**
- ✅ evaluator.py → risk_assessment.py

---

### 7. **Scoring Engine** (`scoring.py`)
**Status:** ✅ **FULLY CONNECTED** - Final scoring and decisions

**Purpose:**
- Calculates PoP relevance scores (0-100)
- Determines suggested actions
- Generates reasoning and confidence scores

**Scoring Components:**
- ✅ Business rule scoring
- ✅ Risk assessment weighting
- ✅ Final confidence calculation
- ✅ Action recommendation logic

**Connections:**
- ✅ evaluator.py → scoring.py

---

### 8. **CSV Data Processor** (`csv_data_processor.py`)
**Status:** ✅ **FULLY CONNECTED** - Data parsing

**Purpose:**
- Parses and processes trend data CSV files
- Handles data cleaning and transformation
- Creates TrendingProduct objects

**Data Files:**
- ✅ `trends_data.csv` - Main dataset
- ✅ `trends_data_alphabetical.csv` - Alternative sorting

**Connections:**
- ✅ trend_analyzer.py → csv_data_processor.py

---

### 9. **Evaluation Cache** (`evaluation_cache.py`)
**Status:** ✅ **FULLY CONNECTED** - Performance optimization

**Purpose:**
- Caches evaluation results for performance
- Supports pagination and pre-caching
- Reduces redundant computations

**Cache Features:**
- ✅ LRU eviction (1000 items)
- ✅ Pre-caching support
- ✅ Pagination-aware storage

**Connections:**
- ✅ evaluator.py → evaluation_cache.py
- ✅ main.py → evaluation_cache.py

---

## 🔌 Disconnected/Unused Components

### 1. **Web Scraper** (`webscraper.py`)
**Status:** ❌ **NOT CONNECTED** - Complete web scraping system

**Purpose:**
- Real-time Google Trends scraping
- Dynamic trend data collection
- Alternative to static CSV data

**Current Situation:**
- ❌ Never called by main pipeline
- ❌ Complete implementation exists
- ❌ Could replace static CSV data

**Integration Suggestion:**
```python
# In trend_analyzer.py, add option to use web scraper
class TrendAnalyzer:
    def __init__(self, use_web_scraper: bool = False):
        if use_web_scraper:
            from .webscraper import WebScraper
            self.data_source = WebScraper()
        else:
            self.data_source = CSVDataProcessor()
```

**Benefits:**
- Real-time trend data
- No need for manual CSV updates
- More dynamic and current insights

---

### 2. **Ingredients Scraper** (`ingredients_scraper.py`)
**Status:** ❌ **NOT CONNECTED** - Ingredient-based analysis

**Purpose:**
- Scrapes product ingredients from websites
- Supports ingredient-based risk assessment
- Provides detailed product composition data

**Current Situation:**
- ❌ Only imports `dynamic_family_extractor.py`
- ❌ Never called by evaluation pipeline
- ❌ Could enhance risk assessment

**Integration Suggestion:**
```python
# In risk_assessment.py, add ingredient analysis
class RiskAssessmentEngine:
    def __init__(self, use_ingredient_analysis: bool = False):
        if use_ingredient_analysis:
            from .ingredients_scraper import IngredientsScraper
            self.ingredients_scraper = IngredientsScraper()
    
    def assess_ingredient_risks(self, product_name: str):
        # Use ingredients scraper for detailed analysis
        pass
```

**Benefits:**
- More accurate FDA risk assessment
- Ingredient-specific regulatory checks
- Enhanced product safety analysis

---

### 3. **Dynamic Family Extractor** (`dynamic_family_extractor.py`)
**Status:** ❌ **NOT CONNECTED** - PoP product family management

**Purpose:**
- Dynamically extracts product families from PoP Excel files
- Replaces hardcoded product categories
- Supports dynamic product catalog management

**Current Situation:**
- ❌ Only imported by ingredients_scraper.py
- ❌ Never called by main pipeline
- ❌ PoP Excel files exist in `pop_data/` but unused

**Integration Suggestion:**
```python
# In models.py, add dynamic categories
class DynamicProductCategory(str, Enum):
    def __init__(self):
        from .dynamic_family_extractor import DynamicFamilyExtractor
        self.extractor = DynamicFamilyExtractor()
        self.categories = self.extractor.get_product_families()
```

**Benefits:**
- Dynamic product catalog from PoP data
- No hardcoded categories
- Easier maintenance and updates

---

### 4. **Filter Module** (`filter.py`)
**Status:** ⚠️ **PARTIALLY CONNECTED** - Only used for specific endpoints

**Purpose:**
- FDA substance checking
- Tariff estimation
- Shelf life estimation
- Restricted ingredient checking

**Current Situation:**
- ✅ Imported in main.py for specific endpoints
- ❌ Not used in main evaluation pipeline
- ❌ Could enhance risk assessment

**Integration Suggestion:**
```python
# In risk_assessment.py, integrate filter functions
class RiskAssessmentEngine:
    def __init__(self):
        from .filter import check_restricted_ingredients, check_tariffs_endpoint
        self.filter = filter
    
    def enhanced_risk_assessment(self, product):
        # Use filter functions for detailed analysis
        fda_risks = check_restricted_ingredients(product.ingredients)
        tariff_risks = check_tariffs_endpoint(product.category)
        # Combine with existing risk assessment
```

**Benefits:**
- More accurate FDA risk assessment
- Real-time tariff checking
- Enhanced regulatory compliance

---

## 📈 Data Flow Diagram

```
┌─────────────────┐
│   trends_data   │
│      .csv       │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ CSV Data        │    │  Trend Analyzer  │    │  Product        │
│ Processor       │───►│                  │───►│  Evaluator      │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────┬───────┘
                                                        │
                       ┌──────────────────┐            │
                       │  Business Rules  │◄───────────┤
                       │                  │            │
                       └──────────────────┘            │
                                                        │
                       ┌──────────────────┐            │
                       │  Risk Assessment │◄───────────┤
                       │                  │            │
                       └──────────────────┘            │
                                                        │
                       ┌──────────────────┐            │
                       │  Scoring Engine  │◄───────────┤
                       │                  │            │
                       └──────────────────┘            │
                                                        ▼
                   ┌──────────────────┐    ┌─────────────────┐
                   │ Evaluation Cache │    │  TrendingReport │
                   │                  │    │                 │
                   └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                   ┌──────────────────┐
                   │  FastAPI Server  │
                   │    (main.py)     │
                   └──────────────────┘
                                                        │
                                                        ▼
                   ┌──────────────────┐
                   │   Frontend       │
                   │  (Next.js)       │
                   └──────────────────┘
```

---

## 🎯 Integration Roadmap

### Phase 1: Quick Wins (Low Effort, High Impact)

#### 1.1 Integrate Filter Module into Risk Assessment
**Effort:** Low | **Impact:** High | **Priority:** 1

**Steps:**
1. Modify `risk_assessment.py` to import filter functions
2. Use `check_restricted_ingredients()` for FDA risk analysis
3. Use `check_tariffs_endpoint()` for tariff risk assessment
4. Combine results with existing risk scoring

**Expected Benefits:**
- More accurate FDA risk assessments
- Real-time tariff checking
- Enhanced regulatory compliance

#### 1.2 Add Web Scraper as Optional Data Source
**Effort:** Low | **Impact:** Medium | **Priority:** 2

**Steps:**
1. Add `use_web_scraper` parameter to `TrendAnalyzer`
2. Implement fallback logic (web scraper → CSV)
3. Add configuration option in main.py
4. Test with small dataset first

**Expected Benefits:**
- Real-time trend data capability
- Reduced manual CSV maintenance
- More current insights

---

### Phase 2: Medium-Term Enhancements

#### 2.1 Integrate Dynamic Product Categories
**Effort:** Medium | **Impact:** High | **Priority:** 3

**Steps:**
1. Modify `models.py` to use dynamic categories
2. Integrate `dynamic_family_extractor.py` with PoP Excel files
3. Update business rules to work with dynamic categories
4. Add category management endpoints

**Expected Benefits:**
- Dynamic product catalog from PoP data
- No hardcoded category maintenance
- Better alignment with PoP product lines

#### 2.2 Add Ingredient-Based Risk Assessment
**Effort:** Medium | **Impact:** Medium | **Priority:** 4

**Steps:**
1. Integrate `ingredients_scraper.py` into risk assessment
2. Add ingredient analysis to evaluation pipeline
3. Create ingredient-specific risk rules
4. Add ingredient database caching

**Expected Benefits:**
- More detailed product safety analysis
- Ingredient-specific regulatory checking
- Enhanced product quality assessment

---

### Phase 3: Advanced Features

#### 3.1 Real-Time Data Pipeline
**Effort:** High | **Impact:** High | **Priority:** 5

**Steps:**
1. Implement scheduled web scraping
2. Add automated CSV updates
3. Create data freshness monitoring
4. Add data quality checks

**Expected Benefits:**
- Always current trend data
- Automated data maintenance
- Improved data reliability

#### 3.2 Machine Learning Enhancement
**Effort:** High | **Impact:** Medium | **Priority:** 6

**Steps:**
1. Collect evaluation feedback data
2. Train ML models for scoring
3. Implement continuous learning
4. Add model performance monitoring

**Expected Benefits:**
- Improved scoring accuracy
- Adaptive decision-making
- Reduced manual rule maintenance

---

## 📋 Current System Health

### ✅ Working Components (9/13)
- main.py (API Gateway)
- evaluator.py (Pipeline Manager)
- models.py (Data Models)
- trend_analyzer.py (Data Source)
- business_rules.py (Business Logic)
- risk_assessment.py (Risk Analysis)
- scoring.py (Scoring Engine)
- csv_data_processor.py (Data Processing)
- evaluation_cache.py (Performance)

### ⚠️ Partially Connected (1/13)
- filter.py (Limited integration)

### ❌ Disconnected Components (3/13)
- webscraper.py (Complete system unused)
- ingredients_scraper.py (Ingredient analysis unused)
- dynamic_family_extractor.py (Dynamic categories unused)

---

## 🔧 Configuration Recommendations

### Environment Variables
```bash
# Data Source Configuration
USE_WEB_SCRAPER=false
CSV_UPDATE_SCHEDULE=daily
WEB_SCRAPER_INTERVAL=hours

# Risk Assessment Configuration
ENABLE_INGREDIENT_ANALYSIS=false
FDA_CHECK_ENABLED=true
TARIFF_CHECK_ENABLED=true

# Performance Configuration
CACHE_SIZE=1000
PRE_CACHE_PAGES=3
BATCH_SIZE=50
```

### Feature Flags
```python
# In main.py
FEATURE_FLAGS = {
    "web_scraper": os.getenv("USE_WEB_SCRAPER", "false").lower() == "true",
    "ingredient_analysis": os.getenv("ENABLE_INGREDIENT_ANALYSIS", "false").lower() == "true",
    "dynamic_categories": os.getenv("USE_DYNAMIC_CATEGORIES", "false").lower() == "true",
}
```

---

## 📊 Performance Metrics

### Current Performance
- **Evaluation Speed:** ~2-3 seconds per product
- **Cache Hit Rate:** ~85% for repeated requests
- **Memory Usage:** ~200MB (1000 cached evaluations)
- **API Response Time:** ~500ms (cached), ~5s (uncached)

### Expected Improvements After Integration
- **With Web Scraper:** +30% evaluation time (real-time data)
- **With Ingredient Analysis:** +50% evaluation time (detailed analysis)
- **With Dynamic Categories:** +10% evaluation time (category lookup)
- **Overall System:** More comprehensive, slightly slower but more accurate

---

## 🎯 Success Metrics

### Before Integration
- Data freshness: Static CSV updates
- Risk assessment accuracy: Basic rule-based
- Product coverage: 326 static products
- Category management: Hardcoded

### After Full Integration
- Data freshness: Real-time updates
- Risk assessment accuracy: Enhanced with ingredient analysis
- Product coverage: Dynamic from multiple sources
- Category management: Dynamic from PoP data

---

## 🚀 Next Steps

1. **Immediate (This Week):**
   - Integrate filter module into risk assessment
   - Test web scraper as optional data source

2. **Short Term (Next 2 Weeks):**
   - Implement dynamic product categories
   - Add ingredient-based risk assessment

3. **Medium Term (Next Month):**
   - Deploy real-time data pipeline
   - Add performance monitoring

4. **Long Term (Next Quarter):**
   - Implement ML enhancements
   - Add advanced analytics

---

## 📞 Contact and Support

For questions about this roadmap or implementation guidance:
- Review the individual component documentation
- Check the existing test files for usage patterns
- Refer to `BACKEND_ANALYSIS.md` for detailed component analysis

---

*Last Updated: May 5, 2026*
*Version: 1.0*
*Status: Active Development*

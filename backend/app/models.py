from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum

'''
--------------------------------
Define values for controlled categories
--------------------------------
'''
class ProductCategory(str, Enum):
    GINGER = "Ginger"
    TEA = "Tea"
    GINSENG = "Ginseng"
    HERBAL_SUPPLEMENT = "Herbal Supplement"
    PAIN_RELIEF = "Pain Relief"
    HONEY = "Honey"
    ORGANIC_FOOD = "Organic Food"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class SuggestedAction(str, Enum):
    DISTRIBUTE_EXISTING = "Distribute existing product"
    DEVELOP_NEW = "Develop new PoP product"

'''
--------------------------------
Raw Product Trend Data (input layer)
--------------------------------
'''
class TrendingProduct(BaseModel):
    'Metrics'
    name: str
    category: ProductCategory
    description: str
    trend_score: float = Field(ge=0, le=100)
    market_growth_rate: float = Field(ge=0, le=100)
    consumer_interest_score: float = Field(ge=0, le=100)
    'Metadata'
    source: str
    trend_keywords: List[str]

'''
--------------------------------
Source Criteria Pass/Fail (logic checker)
--------------------------------
'''
class BusinessRuleEvaluation(BaseModel):
    organic_compatible: bool
    traditional_remedy: bool
    natural_ingredients: bool
    regulatory_compliance_feasible: bool
    market_alignment: bool
    supply_chain_feasible: bool

class RiskAssessment(BaseModel):
    tariff_risk: RiskLevel
    fda_concern: RiskLevel
    supply_chain_risk: RiskLevel
    competition_risk: RiskLevel
    flags: List[str]

'''
--------------------------------
Analysis -> Decision (output layer)
--------------------------------
'''
class ProductEvaluation(BaseModel):
    product: TrendingProduct
    pop_relevance_score: float = Field(ge=0, le=100)
    business_rules: BusinessRuleEvaluation
    risk_assessment: RiskAssessment
    suggested_action: SuggestedAction
    reasoning: str
    confidence_score: float = Field(ge=0, le=100)

class TrendingReport(BaseModel):
    generated_at: str
    total_products_evaluated: int
    high_priority_products: List[ProductEvaluation]
    medium_priority_products: List[ProductEvaluation]
    low_priority_products: List[ProductEvaluation]
    summary_insights: List[str]

'''
--------------------------------
NOTES
--------------------------------
Validation Features (Pydantic):
Numeric fields are constrained:
 - trend_score, confidence_score, etc. must be between 0 and 100
Type safety
Invalid data will raise errors automatically
'''

from pydantic import BaseModel, Field, computed_field
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
    NOT_RECOMMENDED = "Not recommended - poor business alignment"

'''
--------------------------------
Raw Product Trend Data (input layer)
--------------------------------
'''
class TrendingProduct(BaseModel):
    # Raw CSV columns
    section: str
    date: Optional[str] = None
    keyword: str
    group: str
    interest_score: float = Field(default=0, ge=0, le=100)
    region: Optional[str] = None
    query_type: Optional[str] = None
    related_term: Optional[str] = None
    related_value: Optional[float] = None
    suggestion_type: Optional[str] = None

    # Derived fields used by evaluators/frontend
    category: ProductCategory
    trend_score: float = Field(ge=0, le=100)
    market_growth_rate: float = Field(ge=0, le=100)
    consumer_interest_score: float = Field(ge=0, le=100)
    source: str
    trend_keywords: List[str]

    @computed_field
    @property
    def name(self) -> str:
        return self.keyword

    @computed_field
    @property
    def description(self) -> str:
        return (
            f"Google Trends keyword '{self.keyword}' in group '{self.group}' "
            f"from section '{self.section}'"
        )

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
    page: int
    page_size: int
    total_products_available: int
    total_pages: int
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

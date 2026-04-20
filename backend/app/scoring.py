from typing import List
from .models import TrendingProduct, BusinessRuleEvaluation, RiskAssessment, ProductEvaluation, ProductCategory

# Class containing product relevance scoring logic
# Functions: calculate overall relevance score, calculate scores based on individual factors(trends, business rules, risk flags), generate reasoning (based on flags), calculate confidence
class ScoringEngine:
    def __init__(self):
        self.weights = {
            'trend_score': 0.25,
            'market_growth': 0.20,
            'consumer_interest': 0.15,
            'business_rules': 0.25,
            'risk_adjustment': 0.15
        }
    
    # Scores items based on:  1. trends, 2. business rules alignment, and 3. risk factors
    def calculate_pop_relevance_score(self, product: TrendingProduct, 
                                   business_rules: BusinessRuleEvaluation,
                                   risk_assessment: RiskAssessment) -> float:
        """Calculate Prince of Peace relevance score (0-100)"""
        
        # Trends score
        trend_component = product.trend_score * self.weights['trend_score']
        growth_component = product.market_growth_rate * self.weights['market_growth']
        interest_component = product.consumer_interest_score * self.weights['consumer_interest']
        
        # Business rules alignment score
        business_rules_score = self._calculate_business_rules_score(business_rules)
        business_component = business_rules_score * self.weights['business_rules']
        
        # Risk penalty
        risk_penalty = self._calculate_risk_penalty(risk_assessment)
        risk_component = (100 - risk_penalty) * self.weights['risk_adjustment']
        
        # Add up scores
        final_score = trend_component + growth_component + interest_component + business_component + risk_component
        
        # Ensure score is within bounds
        return max(0, min(100, final_score))
    
    def _calculate_business_rules_score(self, business_rules: BusinessRuleEvaluation) -> float:
        """Calculate business rules alignment score"""
        rules = [
            business_rules.organic_compatible,
            business_rules.traditional_remedy,
            business_rules.natural_ingredients,
            business_rules.regulatory_compliance_feasible,
            business_rules.market_alignment,
            business_rules.supply_chain_feasible
        ]
        
        passed_rules = sum(rules)
        return (passed_rules / len(rules)) * 100
    
    def _calculate_risk_penalty(self, risk_assessment: RiskAssessment) -> float:
        """Calculate risk penalty score"""
        risk_scores = {
            'low': 0,
            'medium': 15,
            'high': 35
        }
        
        tariff_penalty = risk_scores[risk_assessment.tariff_risk.value]
        fda_penalty = risk_scores[risk_assessment.fda_concern.value]
        supply_penalty = risk_scores[risk_assessment.supply_chain_risk.value]
        competition_penalty = risk_scores[risk_assessment.competition_risk.value]
        
        # Additional penalty for each flag
        flag_penalty = len(risk_assessment.flags) * 3
        
        total_penalty = tariff_penalty + fda_penalty + supply_penalty + competition_penalty + flag_penalty
        return min(50, total_penalty)  # Cap penalty at 50 points
    
    def generate_reasoning(self, product: TrendingProduct, 
                          business_rules: BusinessRuleEvaluation,
                          risk_assessment: RiskAssessment,
                          pop_score: float) -> str:
        """Generate reasoning for the evaluation"""
        
        reasoning_parts = []
        
        # Trend analysis
        if product.trend_score >= 80:
            reasoning_parts.append(f"Strong market trend (score: {product.trend_score})")
        elif product.trend_score >= 60:
            reasoning_parts.append(f"Moderate market trend (score: {product.trend_score})")
        else:
            reasoning_parts.append(f"Weak market trend (score: {product.trend_score})")
        
        # Business rules alignment
        if business_rules.traditional_remedy:
            reasoning_parts.append("Aligns with traditional remedies focus")
        
        if business_rules.organic_compatible:
            reasoning_parts.append("Organic certification potential")
        
        if business_rules.supply_chain_feasible:
            reasoning_parts.append("Fits existing supply chain")
        
        # Risk factors
        if risk_assessment.fda_concern.value == "high":
            reasoning_parts.append("Significant regulatory hurdles")
        elif risk_assessment.tariff_risk.value == "medium":
            reasoning_parts.append("Moderate tariff exposure")
        
        # Overall assessment
        if pop_score >= 80:
            reasoning_parts.append("High strategic fit for Prince of Peace")
        elif pop_score >= 60:
            reasoning_parts.append("Good strategic fit with some considerations")
        else:
            reasoning_parts.append("Limited strategic fit")
        
        return "; ".join(reasoning_parts)
    
    def calculate_confidence_score(self, product: TrendingProduct,
                                 business_rules: BusinessRuleEvaluation,
                                 risk_assessment: RiskAssessment) -> float:
        """Calculate confidence in the evaluation (0-100)"""
        
        confidence_factors = []
        
        # Higher confidence for well-known categories
        if product.category in [ProductCategory.GINGER, ProductCategory.TEA, ProductCategory.GINSENG]:
            confidence_factors.append(20)
        else:
            confidence_factors.append(10)
        
        # Higher confidence for stronger trends
        if product.trend_score >= 75:
            confidence_factors.append(20)
        elif product.trend_score >= 60:
            confidence_factors.append(15)
        else:
            confidence_factors.append(10)
        
        # Lower confidence with high risks
        if risk_assessment.fda_concern.value == "high":
            confidence_factors.append(-10)
        elif risk_assessment.tariff_risk.value == "high":
            confidence_factors.append(-5)
        
        # Higher confidence with clear business rules alignment
        business_rules_score = self._calculate_business_rules_score(business_rules)
        confidence_factors.append(business_rules_score / 5)
        
        return max(0, min(100, sum(confidence_factors)))

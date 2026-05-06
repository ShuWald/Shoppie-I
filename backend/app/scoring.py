from typing import List
import os
import json
from .models import TrendingProduct, BusinessRuleEvaluation, RiskAssessment, ProductEvaluation, ProductCategory

# Class containing product relevance scoring logic
# Functions: calculate overall relevance score, calculate scores based on individual factors(trends, business rules, risk flags), generate reasoning (based on flags), calculate confidence
class ScoringEngine:
    def __init__(self):
        # Load configurable weights from environment variables or use defaults
        self.weights = self._load_weights()
    
    def _load_weights(self) -> dict:
        """Load scoring weights from environment variables or JSON file"""
        # Default weights
        default_weights = {
            'trend_score': 0.25,
            'market_growth': 0.20,
            'consumer_interest': 0.15,
            'business_rules': 0.25,
            'risk_adjustment': 0.15
        }
        
        # Try to load from environment variables
        env_weights = {}
        for key, default_value in default_weights.items():
            env_key = f"SCORING_WEIGHT_{key.upper()}"
            env_value = os.getenv(env_key)
            if env_value:
                try:
                    env_weights[key] = float(env_value)
                except ValueError:
                    print(f"[ScoringEngine] Invalid weight value for {env_key}: {env_value}, using default {default_value}")
                    env_weights[key] = default_value
            else:
                env_weights[key] = default_value
        
        # Validate that weights sum to 1.0 (or close)
        total_weight = sum(env_weights.values())
        if abs(total_weight - 1.0) > 0.01:  # Allow small floating point differences
            print(f"[ScoringEngine] Warning: Weights sum to {total_weight:.3f}, should sum to 1.0. Normalizing...")
            # Normalize weights
            env_weights = {k: v / total_weight for k, v in env_weights.items()}
        
        print(f"[ScoringEngine] Using weights: {env_weights}")
        return env_weights
    
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
        """Calculate risk penalty score with different weights per risk type"""
        
        # Different weights per risk type - FDA risk is most critical
        risk_weights = {
            'tariff': 1.0,      # Financial impact
            'fda': 2.5,         # Regulatory risk - most critical
            'supply_chain': 1.5, # Operational complexity
            'competition': 0.8   # Market pressure
        }
        
        # Nonlinear risk penalties - higher risks have disproportionate impact
        risk_penalties = {
            'low': 0,
            'medium': 12,       # Reduced from 15
            'high': 40          # Increased from 35
        }
        
        # Calculate weighted penalties
        tariff_penalty = risk_penalties[risk_assessment.tariff_risk.value] * risk_weights['tariff']
        fda_penalty = risk_penalties[risk_assessment.fda_concern.value] * risk_weights['fda']
        supply_penalty = risk_penalties[risk_assessment.supply_chain_risk.value] * risk_weights['supply_chain']
        competition_penalty = risk_penalties[risk_assessment.competition_risk.value] * risk_weights['competition']
        
        # Additional penalty for each flag (weighted by severity)
        flag_penalty = len(risk_assessment.flags) * 2.5
        
        # Total penalty with higher cap for more nuanced scoring
        total_penalty = tariff_penalty + fda_penalty + supply_penalty + competition_penalty + flag_penalty
        
        # Apply diminishing returns for very high penalties (nonlinear scaling)
        if total_penalty > 60:
            total_penalty = 60 + (total_penalty - 60) * 0.5  # Half penalty for excess over 60
        
        return min(80, total_penalty)  # Higher cap but with diminishing returns
    
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
        """Calculate confidence in the evaluation based on data quality and uncertainty"""
        
        # Base confidence starts at 50 (neutral)
        confidence = 50.0
        
        # Data quality factors
        data_quality_factors = {
            'has_description': bool(product.description and len(product.description) > 20),
            'has_keywords': bool(product.trend_keywords and len(product.trend_keywords) > 1),
            'has_category': product.category is not None,
            'has_scores': all(hasattr(product, attr) and getattr(product, attr) is not None 
                           for attr in ['trend_score', 'market_growth_rate', 'consumer_interest_score'])
        }
        
        # Add/subtract based on data quality
        quality_score = sum(data_quality_factors.values()) / len(data_quality_factors)
        confidence += quality_score * 20  # Up to +20 for perfect data
        
        # Trend reliability - higher confidence for consistent trend signals
        trend_consistency = 0
        if product.trend_score and product.market_growth_rate and product.consumer_interest_score:
            # Check if all trend metrics are aligned (all high or all low)
            trend_values = [product.trend_score, product.market_growth_rate, product.consumer_interest_score]
            if all(v >= 70 for v in trend_values) or all(v <= 30 for v in trend_values):
                trend_consistency = 15  # Consistent trends = higher confidence
            elif abs(max(trend_values) - min(trend_values)) > 50:
                trend_consistency = -10  # Inconsistent trends = lower confidence
        
        confidence += trend_consistency
        
        # Risk uncertainty - higher risks increase uncertainty
        risk_uncertainty = 0
        if risk_assessment.fda_concern.value == "high":
            risk_uncertainty -= 15  # High regulatory risk = more uncertainty
        elif risk_assessment.fda_concern.value == "medium":
            risk_uncertainty -= 5
        
        if len(risk_assessment.flags) > 3:
            risk_uncertainty -= 10  # Many flags = complex situation = more uncertainty
        
        confidence += risk_uncertainty
        
        # Business rules clarity - clear alignment increases confidence
        business_rules_score = self._calculate_business_rules_score(business_rules)
        if business_rules_score >= 80:
            confidence += 10  # Strong alignment = higher confidence
        elif business_rules_score <= 40:
            confidence -= 5  # Poor alignment = lower confidence
        
        # Category familiarity - more confidence in well-known categories
        familiar_categories = [ProductCategory.GINGER, ProductCategory.TEA, ProductCategory.GINSENG]
        if product.category in familiar_categories:
            confidence += 5
        
        # Ensure confidence stays within bounds
        return max(0, min(100, confidence))

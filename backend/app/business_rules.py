from typing import List
from .models import TrendingProduct, ProductCategory, BusinessRuleEvaluation, SuggestedAction

# Evaluate products (using attached attributes/keywords) against PoP business rules
class BusinessRulesEngine:

    # Hardcoded PoP categories and keywords
    def __init__(self):
        self.pop_categories = {
            ProductCategory.GINGER: True,
            ProductCategory.TEA: True,
            ProductCategory.GINSENG: True,
            ProductCategory.HERBAL_SUPPLEMENT: True,
            ProductCategory.PAIN_RELIEF: True,
            ProductCategory.HONEY: True,
            ProductCategory.ORGANIC_FOOD: True
        }
        
        self.natural_keywords = [
            "organic", "natural", "herbal", "traditional", "plant-based",
            "botanical", "whole food", "clean", "pure", "wildcrafted"
        ]
        
        self.remedy_keywords = [
            "stress relief", "immune support", "energy", "focus", "sleep",
            "anti-inflammatory", "pain relief", "digestive health", "respiratory",
            "cough relief", "anxiety relief", "wellness"
        ]
    
    # Returns a BusinessRuleEvaluation based on how well the product aligns with PoP's business rules
    def evaluate_product(self, product: TrendingProduct) -> BusinessRuleEvaluation:
        """Evaluate if a trending product aligns with Prince of Peace business rules"""
        
        # Check if category aligns with PoP
        category_aligned = product.category in self.pop_categories
        
        # Check for organic compatibility
        organic_compatible = self._check_organic_compatibility(product)
        
        # Check if it's a traditional remedy
        traditional_remedy = self._check_traditional_remedy(product)
        
        # Check for natural ingredients
        natural_ingredients = self._check_natural_ingredients(product)
        
        # Check regulatory compliance feasibility
        regulatory_compliance_feasible = self._check_regulatory_compliance(product)
        
        # Check market alignment
        market_alignment = self._check_market_alignment(product)
        
        # Check supply chain feasibility
        supply_chain_feasible = self._check_supply_chain_feasibility(product)
        
        return BusinessRuleEvaluation(
            organic_compatible=organic_compatible,
            traditional_remedy=traditional_remedy,
            natural_ingredients=natural_ingredients,
            regulatory_compliance_feasible=regulatory_compliance_feasible,
            market_alignment=market_alignment,
            supply_chain_feasible=supply_chain_feasible
        )
    
    # Functions to individually check each business rule based on product attributes/keywords
    
    def _check_organic_compatibility(self, product: TrendingProduct) -> bool:
        """Check if product can be made organic"""
        text_to_check = f"{product.name} {product.description} {' '.join(product.trend_keywords)}".lower()
        return "organic" in text_to_check or any(keyword in text_to_check for keyword in ["natural", "herbal", "plant-based"])
    
    def _check_traditional_remedy(self, product: TrendingProduct) -> bool:
        """Check if product aligns with traditional remedies"""
        text_to_check = f"{product.name} {product.description} {' '.join(product.trend_keywords)}".lower()
        return any(keyword in text_to_check for keyword in self.remedy_keywords)
    
    def _check_natural_ingredients(self, product: TrendingProduct) -> bool:
        """Check if product uses natural ingredients"""
        text_to_check = f"{product.name} {product.description} {' '.join(product.trend_keywords)}".lower()
        return any(keyword in text_to_check for keyword in self.natural_keywords)
    
    def _check_regulatory_compliance(self, product: TrendingProduct) -> bool:
        """Check if product can meet US regulations"""
        # Simple heuristic - avoid CBD, high-risk supplements
        text_to_check = f"{product.name} {product.description}".lower()
        high_risk_terms = ["cbd", "thc", "psychoactive", "controlled substance"]
        return not any(term in text_to_check for term in high_risk_terms)
    
    def _check_market_alignment(self, product: TrendingProduct) -> bool:
        """Check if product aligns with PoP's target market"""
        return product.trend_score >= 60 and product.market_growth_rate >= 25
    
    def _check_supply_chain_feasibility(self, product: TrendingProduct) -> bool:
        """Check if supply chain is feasible for PoP"""
        # PoP has established supply chains for ginger, tea, ginseng
        easy_categories = [ProductCategory.GINGER, ProductCategory.TEA, ProductCategory.GINSENG, ProductCategory.HONEY]
        return product.category in easy_categories
    

    # Suggest action based on business rule evaluation and product attributes
    def suggest_action(self, product: TrendingProduct, evaluation: BusinessRuleEvaluation) -> SuggestedAction:
        """Suggest whether to distribute existing product or develop new"""
        
        # Count how many business rules pass
        passed_rules = sum([
            evaluation.organic_compatible,
            evaluation.traditional_remedy,
            evaluation.natural_ingredients,
            evaluation.regulatory_compliance_feasible,
            evaluation.market_alignment,
            evaluation.supply_chain_feasible
        ])
        
        # If product aligns well with existing PoP categories and supply chain
        if (passed_rules >= 4 and 
            evaluation.supply_chain_feasible and 
            product.category in [ProductCategory.GINGER, ProductCategory.TEA, ProductCategory.GINSENG]):
            return SuggestedAction.DISTRIBUTE_EXISTING
        
        # If product is promising but requires new development
        elif passed_rules >= 3:
            return SuggestedAction.DEVELOP_NEW
        
        # Default to develop new for borderline cases
        else:
            return SuggestedAction.DEVELOP_NEW

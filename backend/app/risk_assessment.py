from typing import List
from .models import TrendingProduct, RiskAssessment, RiskLevel

# Assesses risks based on keyword-matching with product attributes
# Also hardcoded logic, will need adapting to real data/features
class RiskAssessmentEngine:
    def __init__(self):
        # Fixed risk assessment keywords
        self.high_tariff_countries = ["china", "india", "vietnam"]
        self.fda_concern_keywords = ["cbd", "thc", "psychoactive", "controlled", "unapproved"]
        self.supply_chain_risk_factors = ["exotic", "rare", "endangered", "wildcrafted"]
    
    # Returns a RiskAssessment based on assessed risk in all categories 
    def assess_risks(self, product: TrendingProduct) -> RiskAssessment:
        """Assess various risks associated with the product"""
        
        tariff_risk = self._assess_tariff_risk(product)
        fda_concern = self._assess_fda_concern(product)
        supply_chain_risk = self._assess_supply_chain_risk(product)
        competition_risk = self._assess_competition_risk(product)
        
        flags = self._generate_flags(product, tariff_risk, fda_concern, supply_chain_risk)
        
        return RiskAssessment(
            tariff_risk=tariff_risk,
            fda_concern=fda_concern,
            supply_chain_risk=supply_chain_risk,
            competition_risk=competition_risk,
            flags=flags
        )
    
    # The following functions assess risk in specific categories based on product ?tags?? idk

    def _assess_tariff_risk(self, product: TrendingProduct) -> RiskLevel:
        """Assess tariff risk based on product category and likely sourcing"""
        # Higher risk for products likely sourced from high-tariff countries
        high_risk_categories = ["herbal_supplement", "tea"]
        if product.category in high_risk_categories:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
    
    def _assess_fda_concern(self, product: TrendingProduct) -> RiskLevel:
        """Assess FDA regulatory concerns"""
        text_to_check = f"{product.name} {product.description} {' '.join(product.trend_keywords)}".lower()
        
        for concern_keyword in self.fda_concern_keywords:
            if concern_keyword in text_to_check:
                return RiskLevel.HIGH
        
        # Medium risk for supplements with strong health claims
        if "supplement" in text_to_check and any(claim in text_to_check for claim in ["cure", "treat", "prevent"]):
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def _assess_supply_chain_risk(self, product: TrendingProduct) -> RiskLevel:
        """Assess supply chain complexity and risk"""
        text_to_check = f"{product.name} {product.description} {' '.join(product.trend_keywords)}".lower()
        
        for risk_factor in self.supply_chain_risk_factors:
            if risk_factor in text_to_check:
                return RiskLevel.MEDIUM
        
        # Higher risk for exotic ingredients
        if any(exotic in text_to_check for exotic in ["exotic", "rare", "wild"]):
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def _assess_competition_risk(self, product: TrendingProduct) -> RiskLevel:
        """Assess market competition risk"""
        # High trend score often means high competition
        if product.trend_score >= 85:
            return RiskLevel.HIGH
        elif product.trend_score >= 75:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    # Generate risk flags based on the assessed risks throughout categories
    def _generate_flags(self, product: TrendingProduct, tariff_risk: RiskLevel, 
                       fda_concern: RiskLevel, supply_chain_risk: RiskLevel) -> List[str]:
        """Generate specific risk flags"""
        flags = []
        
        if tariff_risk == RiskLevel.HIGH:
            flags.append("High tariff exposure - consider alternative sourcing")
        elif tariff_risk == RiskLevel.MEDIUM:
            flags.append("Moderate tariff risk - monitor trade policies")
        
        if fda_concern == RiskLevel.HIGH:
            flags.append("Significant FDA regulatory hurdles")
        elif fda_concern == RiskLevel.MEDIUM:
            flags.append("FDA review required - compliance costs expected")
        
        if supply_chain_risk == RiskLevel.HIGH:
            flags.append("Complex supply chain - multiple suppliers needed")
        elif supply_chain_risk == RiskLevel.MEDIUM:
            flags.append("Supply chain complexity - supplier verification needed")
        
        # Add specific flags based on product characteristics
        text_to_check = f"{product.name} {product.description}".lower()
        
        if "cbd" in text_to_check:
            flags.append("CBD products face evolving regulations")
        
        if "mushroom" in text_to_check:
            flags.append("Mushroom sourcing requires quality control")
        
        if "fermented" in text_to_check:
            flags.append("Fermentation process adds complexity")
        
        return flags

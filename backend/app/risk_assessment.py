import re
from typing import List
from .models import TrendingProduct, RiskAssessment, RiskLevel
from .filter import get_fda_substances, check_tariff_rates as check_tariff_api, estimate_shelf_life as estimate_shelf_life_api
from .flexlog import log_message

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
        
        flags = self._generate_flags(product, tariff_risk, fda_concern, supply_chain_risk, est_shelf_life=True)
        
        assessment = RiskAssessment(
            tariff_risk=tariff_risk,
            fda_concern=fda_concern,
            supply_chain_risk=supply_chain_risk,
            competition_risk=competition_risk,
            flags=flags
        )
        log_message(
            f"[RiskAssessment] DONE assess_risks: {product.name} "
            f"(tariff={tariff_risk.value}, fda={fda_concern.value}, supply={supply_chain_risk.value}, comp={competition_risk.value}, flags={len(flags)})",
            additional_route="risk_assessment",
        )
        return assessment
    
    # The following functions assess risk in specific categories based on product ?tags?? idk

    def _assess_tariff_risk(self, product: TrendingProduct) -> RiskLevel:
        """Assess tariff risk based on product category and likely sourcing"""
        # Higher risk for products likely sourced from high-tariff countries
        high_risk_categories = ["Herbal Supplement", "tea"]
        if product.category in high_risk_categories:
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def _assess_fda_concern(self, product: TrendingProduct) -> RiskLevel:
        """Assess FDA regulatory concerns"""
        # Extract potential ingredients from product description and keywords
        text_to_check = f"{product.name} {product.description} {' '.join(product.trend_keywords)}".lower()
        
        # Simple ingredient extraction - split on common separators
        potential_ingredients = []
        # Look for common ingredient patterns
        words = re.findall(r'\b\w+\b', text_to_check)
        potential_ingredients.extend(words)
        
        # Also check against known restricted substances
        log_message("[RiskAssessment] Checking FDA substances list", additional_route="risk_assessment")
        substances = get_fda_substances()
        restricted_found = any(substance.lower() in text_to_check for substance in substances)
        
        if restricted_found:
            return RiskLevel.HIGH
        
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
                       fda_concern: RiskLevel, supply_chain_risk: RiskLevel, est_shelf_life: bool = True) -> List[str]:
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
        
        # Check shelf life concerns
        # Extract potential ingredients from product description
        text_to_check = f"{product.name} {product.description} {' '.join(product.trend_keywords)}".lower()
        # Simple extraction - look for common ingredient patterns
        potential_ingredients = re.findall(r'\b(?:organic|natural|herbal|ginger|tea|ginseng|honey|mushroom|turmeric|extract|powder|capsule|tablet)\b', text_to_check)
        
        if est_shelf_life and potential_ingredients:
            try:
                shelf_life_acceptable = estimate_shelf_life_api(potential_ingredients)
                if not shelf_life_acceptable:
                    flags.append("Short shelf life - may require special handling or preservatives")
            except Exception as e:
                print(f"[RiskAssessment DEBUG] estimate_shelf_life_api failed: {e}")
                # If API fails, skip shelf life check
                pass
        
        # Add specific flags based on product characteristics
        text_to_check = f"{product.name} {product.description}".lower()
        
        if "cbd" in text_to_check:
            flags.append("CBD products face evolving regulations")
        
        if "mushroom" in text_to_check:
            flags.append("Mushroom sourcing requires quality control")
        
        if "fermented" in text_to_check:
            flags.append("Fermentation process adds complexity")
        
        return flags

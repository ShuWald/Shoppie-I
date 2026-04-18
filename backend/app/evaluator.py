from typing import List
from datetime import datetime
from .models import (
    TrendingProduct, ProductEvaluation, TrendingReport, 
    BusinessRuleEvaluation, RiskAssessment, SuggestedAction
)
from .trend_analyzer import TrendAnalyzer
from .business_rules import BusinessRulesEngine
from .risk_assessment import RiskAssessmentEngine
from .scoring import ScoringEngine

#Pipeline manager for decision-making process
class ProductEvaluator:
    def __init__(self):
        self.trend_analyzer = TrendAnalyzer() #fetches trending products
        self.business_rules = BusinessRulesEngine() #checks company fit
        self.risk_assessor = RiskAssessmentEngine() #assesses risk
        self.scoring_engine = ScoringEngine() #assigns scores + reasoning
    
    #Main Pipeline (end-to-end workflow)
    def evaluate_trending_products(self) -> TrendingReport:
        """Main evaluation pipeline"""
        
        #1. Fetch trending products (input)
        #Pulls list of TrendingProduct objects
        #Our databases and scraping information
        trending_products = self.trend_analyzer.fetch_trending_products()
        
        #2. Evaluate each product (core processing loop)
        #Loops through every product and runs full evaluation
        evaluations = []
        for product in trending_products:
            evaluation = self._evaluate_single_product(product)
            evaluations.append(evaluation)
        
        #3. Prioritize products (grouped by score)
        high_priority = [e for e in evaluations if e.pop_relevance_score >= 75]
        medium_priority = [e for e in evaluations if 60 <= e.pop_relevance_score < 75]
        low_priority = [e for e in evaluations if e.pop_relevance_score < 60]
        
        #4. Sort by score within each priority level
        high_priority.sort(key=lambda x: x.pop_relevance_score, reverse=True)
        medium_priority.sort(key=lambda x: x.pop_relevance_score, reverse=True)
        low_priority.sort(key=lambda x: x.pop_relevance_score, reverse=True)
        
        # Step 5: Generate summary insights
        insights = self._generate_summary_insights(evaluations)
        
        # Step 6: Create report
        report = TrendingReport(
            generated_at=datetime.now().isoformat(),
            total_products_evaluated=len(evaluations),
            high_priority_products=high_priority,
            medium_priority_products=medium_priority,
            low_priority_products=low_priority,
            summary_insights=insights
        )
        
        return report

    
    #Individual product evaluation
    def _evaluate_single_product(self, product: TrendingProduct) -> ProductEvaluation:
        """Evaluate a single trending product"""
        
        # Business rules evaluation
        business_rules = self.business_rules.evaluate_product(product)
        
        # Risk assessment
        risk_assessment = self.risk_assessor.assess_risks(product)
        
        # Calculate PoP relevance score
        pop_score = self.scoring_engine.calculate_pop_relevance_score(
            product, business_rules, risk_assessment
        )
        
        # Suggest action
        suggested_action = self.business_rules.suggest_action(product, business_rules)
        
        # Generate reasoning
        reasoning = self.scoring_engine.generate_reasoning(
            product, business_rules, risk_assessment, pop_score
        )
        
        # Calculate confidence
        confidence = self.scoring_engine.calculate_confidence_score(
            product, business_rules, risk_assessment
        )
        
        return ProductEvaluation(
            product=product,
            pop_relevance_score=pop_score,
            business_rules=business_rules,
            risk_assessment=risk_assessment,
            suggested_action=suggested_action,
            reasoning=reasoning,
            confidence_score=confidence
        )
    
    def _generate_summary_insights(self, evaluations: List[ProductEvaluation]) -> List[str]:
        """Generate summary insights from all evaluations"""
        insights = []
        
        if not evaluations:
            return ["No products evaluated"]
        
        # Count categories
        from collections import Counter
        categories = [e.product.category.value for e in evaluations]
        category_counts = Counter(categories)
        
        # Top categories
        top_category = category_counts.most_common(1)[0]
        insights.append(f"Most trending category: {top_category[0]} ({top_category[1]} products)")
        
        # Average scores
        avg_pop_score = sum(e.pop_relevance_score for e in evaluations) / len(evaluations)
        insights.append(f"Average PoP relevance score: {avg_pop_score:.1f}")
        
        # Action distribution
        actions = [e.suggested_action.value for e in evaluations]
        action_counts = Counter(actions)
        
        if action_counts[SuggestedAction.DISTRIBUTE_EXISTING.value]:
            insights.append(f"Products ready for distribution: {action_counts[SuggestedAction.DISTRIBUTE_EXISTING.value]}")
        
        if action_counts[SuggestedAction.DEVELOP_NEW.value]:
            insights.append(f"Products requiring development: {action_counts[SuggestedAction.DEVELOP_NEW.value]}")
        
        # Risk analysis
        high_risk_products = [e for e in evaluations if 
                            e.risk_assessment.tariff_risk.value == "high" or 
                            e.risk_assessment.fda_concern.value == "high"]
        if high_risk_products:
            insights.append(f"High-risk products requiring careful review: {len(high_risk_products)}")
        
        # Top opportunity
        if evaluations:
            top_product = max(evaluations, key=lambda x: x.pop_relevance_score)
            insights.append(f"Top opportunity: {top_product.product.name} (Score: {top_product.pop_relevance_score:.1f})")
        
        return insights

'''
-------------------
NOTES:
-------------------
⚠️ Limitations:
- Hardcoded thresholds (75, 60) → might need tuning
- No parallel processing → could be slow with many products
- Assumes all subsystems return valid data
- Risk logic is somewhat simplified (e.g., only checks two high-risk types for alerts)
'''
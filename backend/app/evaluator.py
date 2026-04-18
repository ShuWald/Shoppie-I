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
from .flexlog import log_message

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
        log_message("[ProductEvaluator] Starting evaluation pipeline", print_log=True, additional_route="evaluator")
        
        #1. Fetch trending products (input)
        #Pulls list of TrendingProduct objects
        #Our databases and scraping information
        try:
            trending_products = self.trend_analyzer.fetch_trending_products()
            log_message(f"[ProductEvaluator] Fetched {len(trending_products)} trending products", additional_route="evaluator")
        except Exception as e:
            log_message("[ProductEvaluator] ERROR fetching trending products", print_log=True, additional_route="evaluator")
            log_message(f"[ProductEvaluator] Exception type: {type(e).__name__}", additional_route="evaluator")
            raise
        
        #2. Evaluate each product (core processing loop)
        #Loops through every product and runs full evaluation
        evaluations = []
        for idx, product in enumerate(trending_products, 1):
            try:
                evaluation = self._evaluate_single_product(product)
                evaluations.append(evaluation)
                log_message(f"[ProductEvaluator] Evaluated product {idx}/{len(trending_products)}: {product.name} (score: {evaluation.pop_relevance_score:.1f})", additional_route="evaluator")
            except Exception as e:
                log_message(f"[ProductEvaluator] ERROR evaluating product '{product.name}'", print_log=True, additional_route="evaluator")
                log_message(f"[ProductEvaluator] Exception type: {type(e).__name__}", additional_route="evaluator")
                continue
        
        #3. Prioritize products (grouped by score)
        high_priority = [e for e in evaluations if e.pop_relevance_score >= 75]
        medium_priority = [e for e in evaluations if 60 <= e.pop_relevance_score < 75]
        low_priority = [e for e in evaluations if e.pop_relevance_score < 60]
        
        #4. Sort by score within each priority level
        high_priority.sort(key=lambda x: x.pop_relevance_score, reverse=True)
        medium_priority.sort(key=lambda x: x.pop_relevance_score, reverse=True)
        low_priority.sort(key=lambda x: x.pop_relevance_score, reverse=True)
        
        # Step 5: Generate summary insights
        try:
            insights = self._generate_summary_insights(evaluations)
            log_message(f"[ProductEvaluator] Generated {len(insights)} summary insights", additional_route="evaluator")
        except Exception as e:
            log_message("[ProductEvaluator] ERROR generating insights", print_log=True, additional_route="evaluator")
            log_message(f"[ProductEvaluator] Exception type: {type(e).__name__}", additional_route="evaluator")
            insights = []
        
        # Step 6: Create report
        log_message(f"[ProductEvaluator] Creating report with {len(evaluations)} evaluations", additional_route="evaluator")
        report = TrendingReport(
            generated_at=datetime.now().isoformat(),
            total_products_evaluated=len(evaluations),
            high_priority_products=high_priority,
            medium_priority_products=medium_priority,
            low_priority_products=low_priority,
            summary_insights=insights
        )
        
        log_message(f"[ProductEvaluator] Pipeline complete: {len(high_priority)} high, {len(medium_priority)} medium, {len(low_priority)} low priority products", print_log=True, additional_route="evaluator")
        return report

    
    #Individual product evaluation
    def _evaluate_single_product(self, product: TrendingProduct) -> ProductEvaluation:
        """Evaluate a single trending product"""
        
        try:
            step = "business_rules.evaluate_product"
            log_message(f"[ProductEvaluator] [{product.name}] START {step}", additional_route="evaluator")
            # Business rules evaluation
            business_rules = self.business_rules.evaluate_product(product)
            log_message(f"[ProductEvaluator] [{product.name}] DONE {step}", additional_route="evaluator")
            
            step = "risk_assessor.assess_risks"
            log_message(f"[ProductEvaluator] [{product.name}] START {step}", additional_route="evaluator")
            # Risk assessment
            risk_assessment = self.risk_assessor.assess_risks(product)
            log_message(f"[ProductEvaluator] [{product.name}] DONE {step}", additional_route="evaluator")
            log_message(f"[ProductEvaluator] {product.name} - tariff_risk:{risk_assessment.tariff_risk.value}, fda:{risk_assessment.fda_concern.value}, flags:{len(risk_assessment.flags)}", additional_route="evaluator")
            
            step = "scoring_engine.calculate_pop_relevance_score"
            log_message(f"[ProductEvaluator] [{product.name}] START {step}", additional_route="evaluator")
            # Calculate PoP relevance score
            pop_score = self.scoring_engine.calculate_pop_relevance_score(
                product, business_rules, risk_assessment
            )
            log_message(f"[ProductEvaluator] [{product.name}] DONE {step} -> score:{pop_score:.1f}", additional_route="evaluator")
            
            step = "business_rules.suggest_action"
            log_message(f"[ProductEvaluator] [{product.name}] START {step}", additional_route="evaluator")
            # Suggest action
            suggested_action = self.business_rules.suggest_action(product, business_rules)
            log_message(f"[ProductEvaluator] [{product.name}] DONE {step} -> action:{suggested_action.value}", additional_route="evaluator")
            
            step = "scoring_engine.generate_reasoning"
            log_message(f"[ProductEvaluator] [{product.name}] START {step}", additional_route="evaluator")
            # Generate reasoning
            reasoning = self.scoring_engine.generate_reasoning(
                product, business_rules, risk_assessment, pop_score
            )
            log_message(f"[ProductEvaluator] [{product.name}] DONE {step}", additional_route="evaluator")
            
            step = "scoring_engine.calculate_confidence_score"
            log_message(f"[ProductEvaluator] [{product.name}] START {step}", additional_route="evaluator")
            # Calculate confidence
            confidence = self.scoring_engine.calculate_confidence_score(
                product, business_rules, risk_assessment
            )
            log_message(f"[ProductEvaluator] [{product.name}] DONE {step} -> confidence:{confidence:.1f}", additional_route="evaluator")
            
            step = "ProductEvaluation(...)"
            log_message(f"[ProductEvaluator] [{product.name}] START {step}", additional_route="evaluator")
            return ProductEvaluation(
                product=product,
                pop_relevance_score=pop_score,
                business_rules=business_rules,
                risk_assessment=risk_assessment,
                suggested_action=suggested_action,
                reasoning=reasoning,
                confidence_score=confidence
            )
        except Exception as e:
            log_message(f"[ProductEvaluator] CRITICAL ERROR in _evaluate_single_product for '{product.name}' at step '{step}'", print_log=True, additional_route="evaluator")
            # Intentionally not logging {e} text here because some exceptions include massive HTML payloads.
            log_message(f"[ProductEvaluator] Exception type: {type(e).__name__}", additional_route="evaluator")
            raise
    
    def _generate_summary_insights(self, evaluations: List[ProductEvaluation]) -> List[str]:
        """Generate summary insights from all evaluations"""
        log_message(f"[ProductEvaluator] Generating insights from {len(evaluations)} evaluations", additional_route="evaluator")
        insights = []
        
        if not evaluations:
            log_message("[ProductEvaluator] WARNING: No evaluations to generate insights from", print_log=True, additional_route="evaluator")
            return ["No products evaluated"]
        
        try:
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
            
            log_message(f"[ProductEvaluator] Successfully generated {len(insights)} insights", additional_route="evaluator")
        except Exception as e:
            log_message("[ProductEvaluator] ERROR generating insights", print_log=True, additional_route="evaluator")
            log_message(f"[ProductEvaluator] Exception type: {type(e).__name__}", additional_route="evaluator")
        
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
from typing import Dict, Generator, List, Tuple
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
from math import ceil

#Pipeline manager for decision-making process
class ProductEvaluator:
    def __init__(self):
        self.trend_analyzer = TrendAnalyzer() #fetches trending products
        self.business_rules = BusinessRulesEngine() #checks company fit
        self.risk_assessor = RiskAssessmentEngine() #assesses risk
        self.scoring_engine = ScoringEngine() #assigns scores + reasoning
    
    #Main Pipeline (end-to-end workflow)
    def evaluate_trending_products(self, page: int = 1, page_size: int = 10) -> TrendingReport:
        """Main evaluation pipeline"""
        log_message("[ProductEvaluator] Starting evaluation pipeline", print_log=True, additional_route="evaluator")
        
        #1. Fetch trending products (input)
        #Pulls list of TrendingProduct objects
        #Our databases and scraping information
        try:
            trending_products, total_available = self.trend_analyzer.fetch_trending_products(page=page, page_size=page_size)
            log_message(
                f"[ProductEvaluator] Fetched {len(trending_products)} products for page={page}, "
                f"page_size={page_size}, total_available={total_available}",
                additional_route="evaluator"
            )
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
        
        report = self._build_report(
            evaluations=evaluations,
            page=page,
            page_size=page_size,
            total_available=total_available,
        )
        
        log_message(
            f"[ProductEvaluator] Pipeline complete: {len(report.high_priority_products)} high, "
            f"{len(report.medium_priority_products)} medium, {len(report.low_priority_products)} low priority products",
            print_log=True,
            additional_route="evaluator"
        )
        return report

    def stream_trending_products(self, page: int = 1, page_size: int = 10) -> Generator[Dict, None, None]:
        """Stream evaluation events so callers can receive each item as soon as it is processed."""
        log_message("[ProductEvaluator] Starting streaming evaluation pipeline", print_log=True, additional_route="evaluator")

        try:
            trending_products, total_available = self.trend_analyzer.fetch_trending_products(page=page, page_size=page_size)
        except Exception as e:
            log_message("[ProductEvaluator] ERROR fetching trending products for streaming", print_log=True, additional_route="evaluator")
            log_message(f"[ProductEvaluator] Exception type: {type(e).__name__}", additional_route="evaluator")
            yield {
                "type": "fatal_error",
                "message": "Failed to fetch trending products",
                "exception_type": type(e).__name__,
            }
            return

        total_in_page = len(trending_products)
        yield {
            "type": "meta",
            "page": max(1, page),
            "page_size": max(1, page_size),
            "total_products_available": total_available,
            "total_products_to_evaluate": total_in_page,
            "total_pages": ceil(total_available / max(1, page_size)) if total_available else 0,
        }

        evaluations: List[ProductEvaluation] = []
        for idx, product in enumerate(trending_products, 1):
            try:
                evaluation = self._evaluate_single_product(product)
                evaluations.append(evaluation)
                priority = self._priority_for_score(evaluation.pop_relevance_score)
                yield {
                    "type": "item",
                    "index": idx,
                    "total": total_in_page,
                    "priority": priority,
                    "evaluation": evaluation.model_dump(mode="json"),
                }
            except Exception as e:
                log_message(f"[ProductEvaluator] ERROR streaming product '{product.name}'", print_log=True, additional_route="evaluator")
                log_message(f"[ProductEvaluator] Exception type: {type(e).__name__}", additional_route="evaluator")
                yield {
                    "type": "item_error",
                    "index": idx,
                    "total": total_in_page,
                    "product_name": product.name,
                    "exception_type": type(e).__name__,
                }

        report = self._build_report(
            evaluations=evaluations,
            page=page,
            page_size=page_size,
            total_available=total_available,
        )
        yield {
            "type": "complete",
            "report": report.model_dump(mode="json"),
        }

    def _priority_for_score(self, score: float) -> str:
        if score >= 75:
            return "high"
        if score >= 60:
            return "medium"
        return "low"

    def _prioritize_evaluations(self, evaluations: List[ProductEvaluation]) -> Tuple[List[ProductEvaluation], List[ProductEvaluation], List[ProductEvaluation]]:
        high_priority = [e for e in evaluations if e.pop_relevance_score >= 75]
        medium_priority = [e for e in evaluations if 60 <= e.pop_relevance_score < 75]
        low_priority = [e for e in evaluations if e.pop_relevance_score < 60]

        high_priority.sort(key=lambda x: x.pop_relevance_score, reverse=True)
        medium_priority.sort(key=lambda x: x.pop_relevance_score, reverse=True)
        low_priority.sort(key=lambda x: x.pop_relevance_score, reverse=True)
        return high_priority, medium_priority, low_priority

    def _build_report(self, evaluations: List[ProductEvaluation], page: int, page_size: int, total_available: int) -> TrendingReport:
        high_priority, medium_priority, low_priority = self._prioritize_evaluations(evaluations)

        try:
            insights = self._generate_summary_insights(evaluations)
            log_message(f"[ProductEvaluator] Generated {len(insights)} summary insights", additional_route="evaluator")
        except Exception as e:
            log_message("[ProductEvaluator] ERROR generating insights", print_log=True, additional_route="evaluator")
            log_message(f"[ProductEvaluator] Exception type: {type(e).__name__}", additional_route="evaluator")
            insights = []

        log_message(f"[ProductEvaluator] Creating report with {len(evaluations)} evaluations", additional_route="evaluator")
        return TrendingReport(
            generated_at=datetime.now().isoformat(),
            total_products_evaluated=len(evaluations),
            page=max(1, page),
            page_size=max(1, page_size),
            total_products_available=total_available,
            total_pages=ceil(total_available / max(1, page_size)) if total_available else 0,
            high_priority_products=high_priority,
            medium_priority_products=medium_priority,
            low_priority_products=low_priority,
            summary_insights=insights,
        )

    
    #Individual product evaluation
    def _evaluate_single_product(self, product: TrendingProduct) -> ProductEvaluation:
        """Evaluate a single trending product"""
        
        try:
            step = "business_rules.evaluate_product"
            # Business rules evaluation
            business_rules = self.business_rules.evaluate_product(product)
            log_message(f"[ProductEvaluator] [{product.name}] DONE {step}", additional_route="evaluator")
            
            step = "risk_assessor.assess_risks"
            # Risk assessment
            risk_assessment = self.risk_assessor.assess_risks(product)
            log_message(f"[ProductEvaluator] [{product.name}] DONE {step}", additional_route="evaluator")
            log_message(f"[ProductEvaluator] {product.name} - tariff_risk:{risk_assessment.tariff_risk.value}, fda:{risk_assessment.fda_concern.value}, flags:{len(risk_assessment.flags)}", additional_route="evaluator")
            
            step = "scoring_engine.calculate_pop_relevance_score"
            # Calculate PoP relevance score
            pop_score = self.scoring_engine.calculate_pop_relevance_score(
                product, business_rules, risk_assessment
            )
            log_message(f"[ProductEvaluator] [{product.name}] DONE {step} -> score:{pop_score:.1f}", additional_route="evaluator")
            
            step = "business_rules.suggest_action"
            # Suggest action
            suggested_action = self.business_rules.suggest_action(product, business_rules)
            log_message(f"[ProductEvaluator] [{product.name}] DONE {step} -> action:{suggested_action.value}", additional_route="evaluator")
            
            step = "scoring_engine.generate_reasoning"
            # Generate reasoning
            reasoning = self.scoring_engine.generate_reasoning(
                product, business_rules, risk_assessment, pop_score
            )
            log_message(f"[ProductEvaluator] [{product.name}] DONE {step}", additional_route="evaluator")
            
            step = "scoring_engine.calculate_confidence_score"
            # Calculate confidence
            confidence = self.scoring_engine.calculate_confidence_score(
                product, business_rules, risk_assessment
            )
            log_message(f"[ProductEvaluator] [{product.name}] DONE {step} -> confidence:{confidence:.1f}", additional_route="evaluator")
            
            step = "ProductEvaluation(...)"
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
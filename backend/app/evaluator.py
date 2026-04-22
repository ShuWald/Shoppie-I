from typing import Dict, Generator, List, Tuple
from datetime import datetime
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from .models import (
    TrendingProduct, ProductEvaluation, TrendingReport, 
    BusinessRuleEvaluation, RiskAssessment, SuggestedAction
)
from .trend_analyzer import TrendAnalyzer
from .business_rules import BusinessRulesEngine
from .risk_assessment import RiskAssessmentEngine
from .scoring import ScoringEngine
from .flexlog import log_message
from .evaluation_cache import EvaluationCache
from math import ceil

# Constants for batch processing thresholds
ASYNC_BATCH_THRESHOLD = 5
PARALLEL_BATCH_THRESHOLD = 10

#Pipeline manager for decision-making process
class ProductEvaluator:
    def __init__(self):
        self.trend_analyzer = TrendAnalyzer() #fetches trending products
        self.business_rules = BusinessRulesEngine() #checks company fit
        self.risk_assessor = RiskAssessmentEngine() #assesses risk
        self.scoring_engine = ScoringEngine() #assigns scores + reasoning
        self.evaluation_cache = EvaluationCache(max_items=1000)  # Increased cache size for better pagination
    
    #Main Pipeline (end-to-end workflow)
    async def evaluate_trending_products(self, page: int = 1, page_size: int = 10) -> TrendingReport:
        """Main evaluation pipeline with async processing"""
        log_message("[ProductEvaluator] Starting async evaluation pipeline", print_log=True, additional_route="evaluator")
        
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

        evaluations = await self._evaluate_request_with_cache_async(
            products=trending_products,
            page=page,
            page_size=page_size,
        )
        
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

    def stream_trending_products(self, page: int = 1, page_size: int = 10):
        """Stream evaluation events so callers can receive each item as soon as it is processed."""
        log_message("[ProductEvaluator] Starting streaming evaluation pipeline", print_log=True, additional_route="evaluator")

        try:
            trending_products, total_available = self.trend_analyzer.fetch_trending_products(page=page, page_size=page_size)
        except Exception as e:
            log_message("[ProductEvaluator] ERROR fetching trending products for streaming", print_log=True, additional_route="evaluator")
            log_message(f"[ProductEvaluator] Exception type: {type(e).__name__}", additional_route="evaluator")
            yield json.dumps({
                "type": "fatal_error",
                "message": "Failed to fetch trending products",
                "exception_type": type(e).__name__,
            }) + "\n"
            return

        total_in_page = len(trending_products)
        safe_page = max(1, page)
        safe_page_size = max(1, page_size)
        request_start = (safe_page - 1) * safe_page_size

        cached_hits, missing_indices = self.evaluation_cache.resolve_request(request_start, total_in_page)

        hit_rate = (len(cached_hits) / total_in_page * 100) if total_in_page > 0 else 0
        log_message(
            f"[ProductEvaluator] STREAM_CACHE_RESOLVE: page={safe_page}, page_size={safe_page_size}, range=[{request_start}..{request_start + total_in_page - 1}], "
            f"total={total_in_page}, hits={len(cached_hits)}, misses={len(missing_indices)}, hit_rate={hit_rate:.1f}%",
            additional_route="eval_cache_verbose",
        )

        yield json.dumps({
            "type": "meta",
            "page": safe_page,
            "page_size": safe_page_size,
            "total_products_available": total_available,
            "total_products_to_evaluate": total_in_page,
            "total_pages": ceil(total_available / max(1, page_size)) if total_available else 0,
            "cache_hits": len(cached_hits),
            "cache_misses": len(missing_indices),
        }) + "\n"

        evaluations: List[ProductEvaluation] = []
        resolved_items: Dict[int, ProductEvaluation] = {}
        stream_from_cache_count = 0
        stream_fresh_eval_count = 0
        
        # Process cached items first
        fresh_products = []
        fresh_indices = []
        
        for idx, product in enumerate(trending_products, 1):
            global_index = request_start + (idx - 1)
            if global_index in cached_hits:
                cached_evaluation = cached_hits[global_index]
                # cached_evaluations.append((idx, cached_evaluation))  # Removed unused variable
                evaluations.append(cached_evaluation)
                resolved_items[global_index] = cached_evaluation
                stream_from_cache_count += 1
                
                yield json.dumps({
                    "type": "item",
                    "index": idx,
                    "total": total_in_page,
                    "priority": self._priority_for_score(cached_evaluation.pop_relevance_score),
                    "from_cache": True,
                    "evaluation": cached_evaluation.model_dump(mode="json"),
                }) + "\n"
            else:
                fresh_products.append(product)
                fresh_indices.append((idx, global_index))
        
        # Batch process fresh products for better performance
        if fresh_products:
            try:
                batch_evaluations = self._evaluate_products_batch(fresh_products)
                
                for i, (idx, global_index) in enumerate(fresh_indices):
                    evaluation = batch_evaluations[i]
                    evaluations.append(evaluation)
                    resolved_items[global_index] = evaluation
                    stream_fresh_eval_count += 1
                    
                    yield json.dumps({
                        "type": "item",
                        "index": idx,
                        "total": total_in_page,
                        "priority": self._priority_for_score(evaluation.pop_relevance_score),
                        "from_cache": False,
                        "evaluation": evaluation.model_dump(mode="json"),
                    }) + "\n"
                        
            except Exception as e:
                log_message(f"[ProductEvaluator] ERROR in batch evaluation", print_log=True, additional_route="evaluator")
                log_message(f"[ProductEvaluator] Exception type: {type(e).__name__}", additional_route="evaluator")
                
                # Fallback to individual evaluation for failed products
                for i, (idx, global_index) in enumerate(fresh_indices):
                    product = fresh_products[i]
                    try:
                        evaluation = self._evaluate_single_product(product)
                        evaluations.append(evaluation)
                        resolved_items[global_index] = evaluation
                        stream_fresh_eval_count += 1
                        
                        yield json.dumps({
                            "type": "item",
                            "index": idx,
                            "total": total_in_page,
                            "priority": self._priority_for_score(evaluation.pop_relevance_score),
                            "from_cache": False,
                            "evaluation": evaluation.model_dump(mode="json"),
                        }) + "\n"
                    except Exception as e:
                        log_message(f"[ProductEvaluator] ERROR streaming product '{product.name}'", print_log=True, additional_route="evaluator")
                        yield json.dumps({
                            "type": "item_error",
                            "index": idx,
                            "total": total_in_page,
                            "product_name": product.name,
                            "exception_type": type(e).__name__,
                        }) + "\n"

        log_message(
            f"[ProductEvaluator] STREAM_EVALUATION_COMPLETE: page={safe_page}, page_size={safe_page_size}, "
            f"from_cache={stream_from_cache_count}, fresh_eval={stream_fresh_eval_count}, total={len(evaluations)}",
            additional_route="eval_cache_verbose",
        )

        self.evaluation_cache.store_request_items(
            start_index=request_start,
            request_count=len(trending_products),
            evaluated_items=resolved_items,
        )

        report = self._build_report(
            evaluations=evaluations,
            page=page,
            page_size=page_size,
            total_available=total_available,
        )
        yield json.dumps({
            "type": "complete",
            "report": report.model_dump(mode="json"),
        }) + "\n"

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

    def _evaluate_request_with_cache(self, products: List[TrendingProduct], page: int, page_size: int) -> List[ProductEvaluation]:
        """Evaluate a page with cache-first resolution, then compute only missing entries."""
        safe_page = max(1, page)
        safe_page_size = max(1, page_size)
        request_start = (safe_page - 1) * safe_page_size

        cached_hits, missing_indices = self.evaluation_cache.resolve_request(request_start, len(products))
        
        hit_rate = (len(cached_hits) / len(products) * 100) if len(products) > 0 else 0
        log_message(
            f"[ProductEvaluator] CACHE_RESOLVE: page={safe_page}, page_size={safe_page_size}, range=[{request_start}..{request_start + len(products) - 1}], "
            f"total={len(products)}, hits={len(cached_hits)}, misses={len(missing_indices)}, hit_rate={hit_rate:.1f}%",
            additional_route="eval_cache_verbose",
        )
        
        log_message(
            f"[ProductEvaluator] Cache check for page={safe_page}, page_size={safe_page_size}: "
            f"hits={len(cached_hits)}, misses={len(missing_indices)}",
            additional_route="evaluator",
        )

        evaluations: List[ProductEvaluation] = []
        resolved_items: Dict[int, ProductEvaluation] = {}
        failed_products: List[Dict] = []
        evaluated_from_cache_count = 0
        evaluated_fresh_count = 0
        
        # Process cached items first
        fresh_products = []
        fresh_indices = []
        
        for idx, product in enumerate(products, 1):
            global_index = request_start + (idx - 1)

            if global_index in cached_hits:
                cached_eval = cached_hits[global_index]
                evaluations.append(cached_eval)
                resolved_items[global_index] = cached_eval
                evaluated_from_cache_count += 1
                log_message(
                    f"[ProductEvaluator] Cache hit for product {idx}/{len(products)}: {product.name}",
                    additional_route="evaluator",
                )
            else:
                fresh_products.append(product)
                fresh_indices.append((idx, global_index))
        
        # Batch process fresh products for better performance
        if fresh_products:
            try:
                batch_evaluations = self._evaluate_products_batch(fresh_products)
                
                for i, (idx, global_index) in enumerate(fresh_indices):
                    evaluation = batch_evaluations[i]
                    evaluations.append(evaluation)
                    resolved_items[global_index] = evaluation
                    evaluated_fresh_count += 1
                    log_message(
                        f"[ProductEvaluator] Batch evaluated product {idx}/{len(products)}: {evaluation.product.name} "
                        f"(score: {evaluation.pop_relevance_score:.1f})",
                        additional_route="evaluator",
                    )
                        
            except Exception as e:
                log_message(f"[ProductEvaluator] ERROR in batch evaluation", print_log=True, additional_route="evaluator")
                log_message(f"[ProductEvaluator] Exception type: {type(e).__name__}", additional_route="evaluator")
                
                # Fallback to individual evaluation for failed products
                for i, (idx, global_index) in enumerate(fresh_indices):
                    product = fresh_products[i]
                    try:
                        evaluation = self._evaluate_single_product(product)
                        evaluations.append(evaluation)
                        resolved_items[global_index] = evaluation
                        evaluated_fresh_count += 1
                        log_message(
                            f"[ProductEvaluator] Evaluated product {idx}/{len(products)}: {product.name} "
                            f"(score: {evaluation.pop_relevance_score:.1f})",
                            additional_route="evaluator",
                        )
                    except Exception as e:
                        log_message(f"[ProductEvaluator] ERROR evaluating product '{product.name}'", print_log=True, additional_route="evaluator")
                        log_message(f"[ProductEvaluator] Exception type: {type(e).__name__}", additional_route="evaluator")
                        # Add to failed products list instead of silently continuing
                        failed_products.append({
                            "product_name": product.name,
                            "error": str(e),
                            "exception_type": type(e).__name__
                        })
                        continue

        log_message(
            f"[ProductEvaluator] EVALUATION_COMPLETE: page={safe_page}, page_size={safe_page_size}, "
            f"from_cache={evaluated_from_cache_count}, fresh_eval={evaluated_fresh_count}, total={len(evaluations)}",
            additional_route="eval_cache_verbose",
        )
        
        if failed_products:
            log_message(
                f"[ProductEvaluator] FAILED_EVALUATIONS: {len(failed_products)} products failed evaluation",
                print_log=True,
                additional_route="evaluator",
            )
            for failed in failed_products:
                log_message(
                    f"[ProductEvaluator] Failed: {failed['product_name']} - {failed['exception_type']}: {failed['error']}",
                    additional_route="evaluator",
                )

        self.evaluation_cache.store_request_items(
            start_index=request_start,
            request_count=len(products),
            evaluated_items=resolved_items,
        )

    async def _evaluate_request_with_cache_async(self, products: List[TrendingProduct], page: int, page_size: int) -> List[ProductEvaluation]:
        """Evaluate a page with cache-first resolution, then compute only missing entries using async."""
        safe_page = max(1, page)
        safe_page_size = max(1, page_size)
        request_start = (safe_page - 1) * safe_page_size

        cached_hits, missing_indices = self.evaluation_cache.resolve_request(request_start, len(products))
        
        hit_rate = (len(cached_hits) / len(products) * 100) if len(products) > 0 else 0
        log_message(
            f"[ProductEvaluator] CACHE_RESOLVE: page={safe_page}, page_size={safe_page_size}, range=[{request_start}..{request_start + len(products) - 1}], "
            f"total={len(products)}, hits={len(cached_hits)}, misses={len(missing_indices)}, hit_rate={hit_rate:.1f}%",
            additional_route="eval_cache_verbose",
        )
        
        log_message(
            f"[ProductEvaluator] Cache check for page={safe_page}, page_size={safe_page_size}: "
            f"hits={len(cached_hits)}, misses={len(missing_indices)}",
            additional_route="evaluator",
        )

        evaluations: List[ProductEvaluation] = []
        resolved_items: Dict[int, ProductEvaluation] = {}
        failed_products: List[Dict] = []
        evaluated_from_cache_count = 0
        evaluated_fresh_count = 0
        
        # Process cached items first
        fresh_products = []
        fresh_indices = []
        
        for idx, product in enumerate(products, 1):
            global_index = request_start + (idx - 1)

            if global_index in cached_hits:
                cached_eval = cached_hits[global_index]
                evaluations.append(cached_eval)
                resolved_items[global_index] = cached_eval
                evaluated_from_cache_count += 1
                log_message(
                    f"[ProductEvaluator] Cache hit for product {idx}/{len(products)}: {product.name}",
                    additional_route="evaluator",
                )
            else:
                fresh_products.append(product)
                fresh_indices.append((idx, global_index))
        
        # Batch process fresh products for better performance
        if fresh_products:
            try:
                batch_evaluations = self._evaluate_products_batch(fresh_products)
                
                for i, (idx, global_index) in enumerate(fresh_indices):
                    evaluation = batch_evaluations[i]
                    evaluations.append(evaluation)
                    resolved_items[global_index] = evaluation
                    evaluated_fresh_count += 1
                    log_message(
                        f"[ProductEvaluator] Batch evaluated product {idx}/{len(products)}: {evaluation.product.name} "
                        f"(score: {evaluation.pop_relevance_score:.1f})",
                        additional_route="evaluator",
                    )
                        
            except Exception as e:
                log_message(f"[ProductEvaluator] ERROR in batch evaluation", print_log=True, additional_route="evaluator")
                log_message(f"[ProductEvaluator] Exception type: {type(e).__name__}", additional_route="evaluator")
                
                # Fallback to individual evaluation for failed products
                for i, (idx, global_index) in enumerate(fresh_indices):
                    product = fresh_products[i]
                    try:
                        evaluation = self._evaluate_single_product(product)
                        evaluations.append(evaluation)
                        resolved_items[global_index] = evaluation
                        evaluated_fresh_count += 1
                        log_message(
                            f"[ProductEvaluator] Evaluated product {idx}/{len(products)}: {product.name} "
                            f"(score: {evaluation.pop_relevance_score:.1f})",
                            additional_route="evaluator",
                        )
                    except Exception as e:
                        log_message(f"[ProductEvaluator] ERROR evaluating product '{product.name}'", print_log=True, additional_route="evaluator")
                        log_message(f"[ProductEvaluator] Exception type: {type(e).__name__}", additional_route="evaluator")
                        # Add to failed products list instead of silently continuing
                        failed_products.append({
                            "product_name": product.name,
                            "error": str(e),
                            "exception_type": type(e).__name__
                        })
                        continue

        log_message(
            f"[ProductEvaluator] EVALUATION_COMPLETE: page={safe_page}, page_size={safe_page_size}, "
            f"from_cache={evaluated_from_cache_count}, fresh_eval={evaluated_fresh_count}, total={len(evaluations)}",
            additional_route="eval_cache_verbose",
        )
        
        if failed_products:
            log_message(
                f"[ProductEvaluator] FAILED_EVALUATIONS: {len(failed_products)} products failed evaluation",
                print_log=True,
                additional_route="evaluator",
            )
            for failed in failed_products:
                log_message(
                    f"[ProductEvaluator] Failed: {failed['product_name']} - {failed['exception_type']}: {failed['error']}",
                    additional_route="evaluator",
                )

        self.evaluation_cache.store_request_items(
            start_index=request_start,
            request_count=len(products),
            evaluated_items=resolved_items,
        )
        return evaluations

    async def _evaluate_products_batch_async(self, products: List[TrendingProduct]) -> List[ProductEvaluation]:
        """Evaluate multiple products using async/await for maximum performance"""
        if len(products) <= ASYNC_BATCH_THRESHOLD:
            # Use sequential processing for very small batches
            return self._evaluate_products_batch_sequential(products)
        
        async def evaluate_single_async(product: TrendingProduct) -> ProductEvaluation:
            """Evaluate a single product with all steps running concurrently"""
            try:
                # Run all evaluation steps concurrently
                business_rules_task = asyncio.create_task(
                    asyncio.to_thread(self.business_rules.evaluate_product, product)
                )
                risk_assessment_task = asyncio.create_task(
                    asyncio.to_thread(self.risk_assessor.assess_risks, product)
                )
                
                # Wait for business rules and risk assessment to complete
                business_rules, risk_assessment = await asyncio.gather(
                    business_rules_task, risk_assessment_task
                )
                
                # Calculate score, action, reasoning, confidence (these can run in parallel)
                pop_score_task = asyncio.create_task(
                    asyncio.to_thread(
                        self.scoring_engine.calculate_pop_relevance_score,
                        product, business_rules, risk_assessment
                    )
                )
                suggested_action_task = asyncio.create_task(
                    asyncio.to_thread(self.business_rules.suggest_action, product, business_rules)
                )
                reasoning_task = asyncio.create_task(
                    asyncio.to_thread(
                        self.scoring_engine.generate_reasoning,
                        product, business_rules, risk_assessment, pop_score
                    )
                )
                confidence_task = asyncio.create_task(
                    asyncio.to_thread(
                        self.scoring_engine.calculate_confidence_score,
                        product, business_rules, risk_assessment
                    )
                )
                
                # Wait for all scoring tasks to complete
                pop_score, suggested_action, reasoning, confidence = await asyncio.gather(
                    pop_score_task, suggested_action_task, reasoning_task, confidence_task
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
            except Exception as e:
                log_message(f"[ProductEvaluator] ERROR evaluating {product.name} async", additional_route="evaluator")
                raise
        
        try:
            # Use asyncio.gather to evaluate all products concurrently
            evaluation_tasks = [evaluate_single_async(product) for product in products]
            evaluations = await asyncio.gather(*evaluation_tasks, return_exceptions=False)
            
            # Filter out any failed evaluations
            return [eval for eval in evaluations if eval is not None]
            
        except Exception as e:
            log_message(f"[ProductEvaluator] ERROR in async batch evaluation", print_log=True, additional_route="evaluator")
            log_message(f"[ProductEvaluator] Exception type: {type(e).__name__}", additional_route="evaluator")
            # Fallback to sequential processing
            return self._evaluate_products_batch_sequential(products)

    def _evaluate_products_batch(self, products: List[TrendingProduct]) -> List[ProductEvaluation]:
        """Evaluate multiple products in parallel for maximum performance"""
        if len(products) <= PARALLEL_BATCH_THRESHOLD:
            # Use sequential processing for small batches
            return self._evaluate_products_batch_sequential(products)
        
        evaluations = [None] * len(products)
        
        def evaluate_single_parallel(idx_product):
            idx, product = idx_product
            try:
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
                
                return idx, ProductEvaluation(
                    product=product,
                    pop_relevance_score=pop_score,
                    business_rules=business_rules,
                    risk_assessment=risk_assessment,
                    suggested_action=suggested_action,
                    reasoning=reasoning,
                    confidence_score=confidence
                )
            except Exception as e:
                log_message(f"[ProductEvaluator] ERROR evaluating {product.name} in parallel", additional_route="evaluator")
                return idx, None
        
        try:
            # Use ThreadPoolExecutor for parallel processing
            max_workers = min(16, len(products))  # Increase to 16 workers for maximum throughput
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_idx = {
                    executor.submit(evaluate_single_parallel, (i, product)): i 
                    for i, product in enumerate(products)
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_idx):
                    idx, evaluation = future.result()
                    if evaluation is not None:
                        evaluations[idx] = evaluation
            
            # Filter out any None values (failed evaluations)
            return [eval for eval in evaluations if eval is not None]
            
        except Exception as e:
            log_message(f"[ProductEvaluator] ERROR in parallel batch evaluation", print_log=True, additional_route="evaluator")
            log_message(f"[ProductEvaluator] Exception type: {type(e).__name__}", additional_route="evaluator")
            # Fallback to sequential processing
            return self._evaluate_products_batch_sequential(products)

    def _evaluate_products_batch_sequential(self, products: List[TrendingProduct]) -> List[ProductEvaluation]:
        """Sequential batch evaluation as fallback"""
        evaluations = []
        
        try:
            for product in products:
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
                
                evaluations.append(ProductEvaluation(
                    product=product,
                    pop_relevance_score=pop_score,
                    business_rules=business_rules,
                    risk_assessment=risk_assessment,
                    suggested_action=suggested_action,
                    reasoning=reasoning,
                    confidence_score=confidence
                ))
                
        except Exception as e:
            log_message(f"[ProductEvaluator] ERROR in sequential batch evaluation", print_log=True, additional_route="evaluator")
            log_message(f"[ProductEvaluator] Exception type: {type(e).__name__}", additional_route="evaluator")
            raise
            
        return evaluations

    #Individual product evaluation (fallback)
    def _evaluate_single_product(self, product: TrendingProduct) -> ProductEvaluation:
        """Evaluate a single trending product - optimized for speed"""
        
        try:
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
        except Exception as e:
            log_message(f"[ProductEvaluator] CRITICAL ERROR in _evaluate_single_product for '{product.name}'", print_log=True, additional_route="evaluator")
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

from app.business_rules import BusinessRulesEngine
from app.models import TrendingProduct, ProductCategory

# Test the decision logic
business_rules = BusinessRulesEngine()

# Create a test product that should get NOT_RECOMMENDED
test_product = TrendingProduct(
    section="interest_over_time",
    date="2026-03-29",
    keyword="CBD Energy Drink",
    group="Energy Drinks",
    interest_score=100.0,
    category=ProductCategory.HERBAL_SUPPLEMENT,
    trend_score=40.0,  # Low trend
    market_growth_rate=20.0,  # Low growth
    consumer_interest_score=30.0,  # Low interest
    source="Test",
    trend_keywords=["cbd", "energy", "drink"]
)

evaluation = business_rules.evaluate_product(test_product)
action = business_rules.suggest_action(test_product, evaluation)

print(f"Product: {test_product.name}")
print(f"Passed rules: {sum([evaluation.organic_compatible, evaluation.traditional_remedy, evaluation.natural_ingredients, evaluation.regulatory_compliance_feasible, evaluation.market_alignment, evaluation.supply_chain_feasible])}/6")
print(f"Suggested action: {action.value}")
print(f"Business rules: {evaluation}")

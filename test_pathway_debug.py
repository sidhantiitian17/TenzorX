"""Debug the pathway data specifically."""
import sys
sys.path.insert(0, 'd:/TenzorX/Backend')

from app.engines.cost_engine import CostEngine
from app.engines.geo_pricing import GeoPricingEngine
from app.engines.comorbidity_engine import ComorbidityEngine

# Test the engines directly
cost_engine = CostEngine()
geo_engine = GeoPricingEngine()
comorbidity_engine = ComorbidityEngine()

procedure = "Nephrolithiasis Treatment"
city_tier = 2

print("="*60)
print("DEBUGGING CLINICAL PATHWAY COST CALCULATION")
print("="*60)
print(f"Procedure: {procedure}")
print(f"City Tier: {city_tier}")
print()

# Step 1: Base cost
print("Step 1: Base Cost from CostEngine")
base_cost = cost_engine.estimate(procedure, city_tier)
print(f"  Result: {base_cost}")
print(f"  Total: {base_cost.get('total', {})}")
print()

# Step 2: Geo adjustment
print("Step 2: Geo Adjustment")
tier_str = f"tier{city_tier}"
geo_adjusted = geo_engine.apply_multiplier(base_cost, tier_str)
print(f"  Result: {geo_adjusted}")
print(f"  Total: {geo_adjusted.get('total', {})}")
print()

# Step 3: Comorbidity adjustment
print("Step 3: Comorbidity Adjustment")
final_cost = comorbidity_engine.adjust(
    geo_adjusted,
    comorbidities=[],
    age=35
)
print(f"  Result keys: {list(final_cost.keys())}")
print(f"  Total: {final_cost.get('total', {})}")
print()

# Check the total_min/total_max extraction
total = final_cost.get("total", {})
if isinstance(total, dict):
    total_min = total.get("min", 0)
    total_max = total.get("max", 0)
    print(f"Extracted total_min: {total_min}, total_max: {total_max}")
else:
    print(f"ERROR: total is not a dict: {total}")

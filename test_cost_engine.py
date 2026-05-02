"""Test the cost engine with component breakdown."""
import sys
sys.path.insert(0, 'd:/TenzorX/Backend')

from app.services.cost_engine import estimate_cost_with_fallback

# Test Nephrolithiasis cost estimation
result = estimate_cost_with_fallback(
    procedure_name='Nephrolithiasis Treatment',
    pathway_cost_data=None,
    known_comorbidities=[],
    location_tier='tier-2'
)

print('='*60)
print('COST ESTIMATION TEST: Nephrolithiasis Treatment')
print('='*60)
total_min = result["total_cost_range"]["min"]
total_max = result["total_cost_range"]["max"]
print(f'Total Range: Rs {total_min:,} - Rs {total_max:,}')
print(f'Source: {result["source"]}')
print()
print('COMPONENT BREAKDOWN:')
for item in result['breakdown_items']:
    label = item["label"]
    min_val = item["min"]
    max_val = item["max"]
    print(f'  {label}: Rs {min_val:,} - Rs {max_val:,}')
print()

# Verify component costs are not zero
has_zero = any(item['min'] == 0 and item['max'] == 0 for item in result['breakdown_items'])
if has_zero:
    print('WARNING: Some components have zero costs!')
else:
    print('SUCCESS: All components have non-zero costs!')
    
# Test with pathway data
print()
print('='*60)
print('TEST WITH PATHWAY DATA (Knowledge Graph fallback)')
print('='*60)
pathway_data = {
    "total_min": 180000,
    "total_max": 220000,
    "pathway_steps": []
}
result2 = estimate_cost_with_fallback(
    procedure_name='Nephrolithiasis Treatment',
    pathway_cost_data=pathway_data,
    known_comorbidities=[],
    location_tier='tier-2'
)
print(f'Total Range: Rs {result2["total_cost_range"]["min"]:,} - Rs {result2["total_cost_range"]["max"]:,}')
print(f'Source: {result2["source"]}')
print()
print('COMPONENT BREAKDOWN:')
for item in result2['breakdown_items']:
    label = item["label"]
    min_val = item["min"]
    max_val = item["max"]
    print(f'  {label}: Rs {min_val:,} - Rs {max_val:,}')

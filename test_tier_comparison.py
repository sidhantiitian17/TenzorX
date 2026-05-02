"""Test tier comparison data from API."""
import requests

def test_tier_comparison():
    url = 'http://localhost:8000/api/v1/chat'
    data = {
        'message': 'I have kidney stone, tell me treatment option',
        'session_id': 'test-session-tier-001',
        'location': 'Raipur',
        'patient_profile': {'age': 35, 'comorbidities': []}
    }

    print('Testing Tier Comparison Data...')
    
    try:
        response = requests.post(url, json=data, timeout=60)
        result = response.json()
        
        rp = result.get('results_panel', {})
        cost_estimate = rp.get('cost_estimate', {})
        
        print('='*60)
        print('TIER COST COMPARISON')
        print('='*60)
        
        tier_data = cost_estimate.get('tier_cost_comparison', {})
        if tier_data:
            print(f"  Budget:    Rs {tier_data.get('budget', {}).get('min', 0):,} - Rs {tier_data.get('budget', {}).get('max', 0):,}")
            print(f"  Mid-tier:  Rs {tier_data.get('mid_tier', {}).get('min', 0):,} - Rs {tier_data.get('mid_tier', {}).get('max', 0):,}")
            print(f"  Premium:   Rs {tier_data.get('premium', {}).get('min', 0):,} - Rs {tier_data.get('premium', {}).get('max', 0):,}")
            
            # Verify non-zero
            budget_min = tier_data.get('budget', {}).get('min', 0)
            premium_min = tier_data.get('premium', {}).get('min', 0)
            
            if budget_min > 0 and premium_min > 0:
                print("\n✅ SUCCESS: All tiers have real cost values!")
            else:
                print("\n❌ FAIL: Some tiers have zero values")
        else:
            print("❌ FAIL: No tier_cost_comparison data found")
            print(f"Available keys in cost_estimate: {list(cost_estimate.keys())}")

    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    test_tier_comparison()

"""Test the cost breakdown from the API."""
import requests
import json

def test_cost_breakdown():
    url = 'http://localhost:8000/api/v1/chat'
    data = {
        'message': 'I have kidney stone, tell me treatment option',
        'session_id': 'test-session-cost-001',
        'location': 'Raipur',
        'patient_profile': {
            'age': 35,
            'comorbidities': []
        }
    }

    print('Testing Cost Breakdown from API...')
    print(f"Query: {data['message']}")
    print()

    try:
        response = requests.post(url, json=data, timeout=60)
        result = response.json()

        print('='*60)
        print('COST ESTIMATE DETAILS')
        print('='*60)

        rp = result.get('results_panel', {})
        cost = rp.get('cost_estimate', {})
        
        if cost:
            total = cost.get('total_cost_range', {})
            print(f"Total Cost Range: Rs {total.get('min', 0):,} - Rs {total.get('max', 0):,}")
            print(f"Cost Source: {cost.get('cost_source', 'unknown')}")
            print(f"Geo Multiplier: {cost.get('geo_multiplier', 1.0)}")
            print()
            
            # Check cost breakdown items
            breakdown = cost.get('cost_breakdown_items', [])
            if breakdown:
                print('COMPONENT BREAKDOWN:')
                print('-' * 40)
                for item in breakdown:
                    label = item.get('label', '')
                    min_val = item.get('min', 0)
                    max_val = item.get('max', 0)
                    print(f"  {label}: Rs {min_val:,} - Rs {max_val:,}")
                print()
                
                # Check for zero values
                has_zero = any(item.get('min', 0) == 0 and item.get('max', 0) == 0 for item in breakdown)
                if has_zero:
                    print('❌ FAIL: Some components have zero costs!')
                else:
                    print('✅ SUCCESS: All components have real cost values!')
            else:
                print('❌ FAIL: No cost breakdown items found!')
        else:
            print('❌ FAIL: No cost estimate data found!')

        print()
        print('='*60)

    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_cost_breakdown()

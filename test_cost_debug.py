"""Debug the cost estimate issue."""
import requests
import json

def test_cost_debug():
    url = 'http://localhost:8000/api/v1/chat'
    data = {
        'message': 'I have kidney stone, tell me treatment option',
        'session_id': 'test-session-debug-001',
        'location': 'Raipur',
        'patient_profile': {
            'age': 35,
            'comorbidities': []
        }
    }

    print('Debugging Cost Estimate...')

    try:
        response = requests.post(url, json=data, timeout=60)
        result = response.json()
        
        rp = result.get('results_panel', {})
        
        # Check if cost_estimate exists
        print(f"Type of cost_estimate: {type(rp.get('cost_estimate'))}")
        print(f"cost_estimate is None: {rp.get('cost_estimate') is None}")
        
        cost = rp.get('cost_estimate')
        if cost:
            print(f"\nCost Estimate Keys: {list(cost.keys())}")
            print(f"\nTotal Cost Range: {cost.get('total_cost_range')}")
            print(f"\nCost Breakdown Items: {cost.get('cost_breakdown_items')}")
            
            if cost.get('cost_breakdown_items'):
                print("\nComponent Breakdown:")
                for item in cost['cost_breakdown_items']:
                    print(f"  - {item.get('label')}: Rs {item.get('min'):,} - Rs {item.get('max'):,}")
        else:
            print("\nNo cost_estimate data found in results_panel")
            print(f"\nResults panel keys: {list(rp.keys())}")
            
            # Check pathway for cost data
            pathway = rp.get('pathway', {})
            print(f"\nPathway total_min: {pathway.get('total_min')}")
            print(f"Pathway total_max: {pathway.get('total_max')}")

    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_cost_debug()

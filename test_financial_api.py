"""Test financial engine output from API."""
import requests
import json

def test_financial():
    url = 'http://localhost:8000/api/v1/chat'
    data = {
        'message': 'I have kidney stone, tell me treatment option',
        'session_id': 'test-session-fin-001',
        'location': 'Raipur',
        'patient_profile': {'age': 35, 'comorbidities': []}
    }

    print('Testing Financial Engine from API...')
    
    try:
        response = requests.post(url, json=data, timeout=60)
        result = response.json()
        
        rp = result.get('results_panel', {})
        
        print('='*60)
        print('RESULTS PANEL KEYS')
        print('='*60)
        for key in rp.keys():
            print(f"  - {key}")
        print()
        
        # Check cost_estimate
        cost = rp.get('cost_estimate')
        print(f'cost_estimate type: {type(cost)}')
        print(f'cost_estimate is None: {cost is None}')
        
        if cost:
            print(f'\nCost Estimate Keys: {list(cost.keys())}')
            print(f"Total Range: {cost.get('total_cost_range')}")
            print(f"\nCost Breakdown Items:")
            for item in cost.get('cost_breakdown_items', []):
                print(f"  - {item.get('label')}: Rs {item.get('min'):,} - Rs {item.get('max'):,}")
        else:
            print('\nNo cost_estimate found')
            
        # Also check pathway
        pathway = rp.get('pathway', {})
        print(f"\nPathway total_min: {pathway.get('total_min')}")
        print(f"Pathway total_max: {pathway.get('total_max')}")

    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_financial()

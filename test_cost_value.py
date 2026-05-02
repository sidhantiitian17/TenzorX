"""Test to check the actual cost_estimate value."""
import requests
import json

def test_api():
    url = 'http://localhost:8000/api/v1/chat'
    data = {
        'message': 'I have kidney stone, tell me treatment option',
        'session_id': 'test-session-costval-001',
        'location': 'Raipur',
        'patient_profile': {'age': 35, 'comorbidities': []}
    }

    print('Testing API - checking cost_estimate value...')
    
    try:
        response = requests.post(url, json=data, timeout=60)
        result = response.json()
        
        rp = result.get('results_panel', {})
        
        print('='*60)
        print('COST_ESTIMATE VALUE')
        print('='*60)
        
        if 'cost_estimate' in rp:
            cost = rp['cost_estimate']
            print(f'cost_estimate exists: True')
            print(f'cost_estimate value: {repr(cost)}')
            
            if cost is None:
                print('\nCOST_ESTIMATE IS NONE')
                print('This means the financial engine did not run or returned None')
            elif isinstance(cost, dict):
                print(f'\ncost_estimate is a dict with keys: {list(cost.keys())}')
                if 'total_cost_range' in cost:
                    print(f"  total_cost_range: {cost['total_cost_range']}")
                if 'cost_breakdown_items' in cost:
                    print(f"  cost_breakdown_items count: {len(cost.get('cost_breakdown_items', []))}")
            else:
                print(f'\nUnexpected type: {type(cost)}')
        else:
            print('cost_estimate key NOT FOUND in results_panel')

    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_api()

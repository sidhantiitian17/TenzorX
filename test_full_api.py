"""Test the full API response with all details."""
import requests
import json

def test_full_api():
    url = 'http://localhost:8000/api/v1/chat'
    data = {
        'message': 'I have kidney stone, tell me treatment option',
        'session_id': 'test-session-full-001',
        'location': 'Raipur',
        'patient_profile': {
            'age': 35,
            'comorbidities': []
        }
    }

    print('Testing Full API Response...')
    print(f"Query: {data['message']}")
    print()

    try:
        response = requests.post(url, json=data, timeout=60)
        result = response.json()
        
        print('='*60)
        print('FULL RESPONSE STRUCTURE')
        print('='*60)
        print(json.dumps(result, indent=2, default=str)[:3000])
        print()
        
        # Check results panel
        rp = result.get('results_panel', {})
        print('RESULTS PANEL KEYS:')
        for key in rp.keys():
            print(f"  - {key}")
        print()
        
        # Check cost estimate
        cost = rp.get('cost_estimate')
        if cost:
            print('COST ESTIMATE FOUND!')
            print(f"  Keys: {list(cost.keys())}")
        else:
            print('NO COST ESTIMATE IN RESULTS PANEL')

    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_full_api()

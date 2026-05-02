"""Test the chat API with full response printing."""
import requests
import json

def test_api():
    url = 'http://localhost:8000/api/v1/chat'
    data = {
        'message': 'I have kidney stone, tell me treatment option',
        'session_id': 'test-session-direct-001',
        'location': 'Raipur',
        'patient_profile': {'age': 35, 'comorbidities': []}
    }

    print('Testing API with full response...')
    
    try:
        response = requests.post(url, json=data, timeout=60)
        result = response.json()
        
        # Print full response
        print('='*60)
        print('FULL RESPONSE (first 5000 chars)')
        print('='*60)
        print(json.dumps(result, indent=2, default=str)[:5000])
        
        # Check if there's an error
        if 'error' in result:
            print(f"\nERROR FOUND: {result['error']}")
        
        # Check results_panel
        rp = result.get('results_panel', {})
        print(f"\n\nResults Panel has cost_estimate key: {'cost_estimate' in rp}")
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_api()

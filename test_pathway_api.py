"""Test pathway data from API."""
import requests

def test_pathway():
    url = 'http://localhost:8000/api/v1/chat'
    data = {
        'message': 'I have kidney stone, tell me treatment option',
        'session_id': 'test-session-pathway-001',
        'location': 'Raipur',
        'patient_profile': {'age': 35, 'comorbidities': []}
    }

    print('Testing Pathway Data from API...')
    
    try:
        response = requests.post(url, json=data, timeout=60)
        result = response.json()
        
        rp = result.get('results_panel', {})
        pathway = rp.get('pathway', {})
        
        print('='*60)
        print('PATHWAY DATA')
        print('='*60)
        print(f"total_min: {pathway.get('total_min')}")
        print(f"total_max: {pathway.get('total_max')}")
        print(f"geo_multiplier: {pathway.get('geo_multiplier')}")
        print()
        print(f"cost_breakdown: {pathway.get('cost_breakdown', {})}")
        print()
        
        if pathway.get('total_min', 0) > 0:
            print('✅ SUCCESS: Pathway has valid cost data!')
        else:
            print('❌ FAIL: Pathway total_min is 0 or missing')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    test_pathway()

"""Test pathway and clinical phases data."""
import requests

def test_pathway():
    url = 'http://localhost:8000/api/v1/chat'
    data = {
        'message': 'I have kidney stone, tell me treatment option',
        'session_id': 'test-session-phases-001',
        'location': 'Raipur',
        'patient_profile': {'age': 35, 'comorbidities': []}
    }

    print('Testing Pathway Data...')
    
    try:
        response = requests.post(url, json=data, timeout=60)
        result = response.json()
        
        rp = result.get('results_panel', {})
        pathway = rp.get('pathway', {})
        
        print('='*60)
        print('PATHWAY STEPS')
        print('='*60)
        steps = pathway.get('pathway_steps', [])
        for step in steps:
            print(f"  Step {step.get('step')}: {step.get('name')}")
            print(f"    cost_min: {step.get('cost_min')}, cost_max: {step.get('cost_max')}")
        
        print()
        print('='*60)
        print('CLINICAL PHASES')
        print('='*60)
        phases = pathway.get('clinical_phases', [])
        for phase in phases:
            print(f"  {phase.get('name')}")
            print(f"    cost_min: {phase.get('cost_min')}, cost_max: {phase.get('cost_max')}")
        
        print()
        print('='*60)
        print(f"Pathway total_min: {pathway.get('total_min')}")
        print(f"Pathway total_max: {pathway.get('total_max')}")

    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    test_pathway()

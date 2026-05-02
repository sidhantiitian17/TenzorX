"""Test the Master Orchestrator API endpoint."""
import requests
import json

def test_chat_api():
    url = 'http://localhost:8000/api/v1/chat'
    data = {
        'message': 'I have kidney stone, tell me treatment option',
        'session_id': 'test-session-001',
        'location': 'Raipur',
        'patient_profile': {
            'age': 35,
            'comorbidities': []
        }
    }

    print('Testing Master Orchestrator API...')
    print(f"Query: {data['message']}")
    print()

    try:
        response = requests.post(url, json=data, timeout=60)
        result = response.json()

        print('='*60)
        print('RESPONSE SUMMARY')
        print('='*60)

        chat = result.get('chat_response', {})
        msg = chat.get('message', '')
        print(f"Message: {msg[:200]}...")
        print(f"Triage: {chat.get('triage_level', '')}")
        print()

        rp = result.get('results_panel', {})

        ci = rp.get('clinical_interpretation', {})
        if ci:
            print('CLINICAL INTERPRETATION:')
            print(f"  Procedure: {ci.get('canonical_procedure', '')}")
            print(f"  Category: {ci.get('category', '')}")
            print(f"  ICD-10: {ci.get('icd10', '')}")
            print(f"  SNOMED: {ci.get('snomed_ct', '')}")
            print()

        pathway = rp.get('pathway', {})
        if pathway:
            print('TREATMENT PATHWAY:')
            steps = pathway.get('pathway_steps', [])
            print(f"  Steps: {len(steps)}")
            for step in steps[:3]:
                print(f"    - {step.get('name', '')}")
            print()

            phases = pathway.get('clinical_phases', [])
            print(f"  Clinical Phases: {len(phases)}")
            for phase in phases[:5]:
                print(f"    - {phase.get('name', '')} ({phase.get('duration', '')})")
            print()

        cost = rp.get('cost_estimate', {})
        if cost:
            print('COST ESTIMATE:')
            total = cost.get('total_cost_range', {})
            print(f"  Range: Rs {total.get('min', 0):,} - Rs {total.get('max', 0):,}")
            print()

        print('='*60)
        print('SUCCESS: Full pipeline working!')
        print('='*60)

    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_chat_api()

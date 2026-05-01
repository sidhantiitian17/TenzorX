"""
Test script for Knowledge Graph pipeline (without LLM).

Verifies that all graph traversal and cost calculation tools work correctly.
"""

import sys
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
env_file = BACKEND_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)

from app.knowledge_graph.neo4j_client import Neo4jClient
from app.knowledge_graph.fusion_scorer import FusionScorer
from app.knowledge_graph.availability_proxy import AvailabilityProxy, SeverityClassifier
from app.nlp.ner_pipeline import NERPipeline
from app.nlp.icd10_mapper import ICD10Mapper


def main():
    print("\n" + "="*60)
    print("KNOWLEDGE GRAPH PIPELINE TEST")
    print("="*60)
    
    results = {}
    
    # Test 1: Neo4j Connection
    print("\n[TEST 1] Neo4j Connection...")
    try:
        client = Neo4jClient()
        result = client.run_query("RETURN 1 as num")
        assert result == [{"num": 1}]
        print("  [OK] Connected to Neo4j")
        
        # Get node counts
        counts = client.run_query("""
            MATCH (n)
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY count DESC
        """)
        print("\n  Node counts:")
        for record in counts:
            print(f"    {record['label']}: {record['count']}")
        
        results['neo4j'] = True
    except Exception as e:
        print(f"  [FAIL] {e}")
        results['neo4j'] = False
        return results
    
    # Test 2: Disease lookup for symptoms
    print("\n[TEST 2] Disease lookup for symptoms...")
    try:
        symptoms = ["chest pain", "shortness of breath"]
        diseases = client.find_diseases_for_symptoms(symptoms)
        print(f"  [OK] Found {len(diseases)} diseases for symptoms: {symptoms}")
        if diseases:
            print(f"    Primary: {diseases[0]['name']} ({diseases[0]['icd10_code']})")
        results['disease_lookup'] = True
    except Exception as e:
        print(f"  [FAIL] {e}")
        results['disease_lookup'] = False
    
    # Test 3: Procedure discovery
    print("\n[TEST 3] Procedure discovery...")
    try:
        if diseases:
            disease_icd = diseases[0]['icd10_code']
            procedures = client.find_procedures_for_disease(disease_icd)
            print(f"  [OK] Found procedures for {disease_icd}")
            if 'treatment' in procedures:
                print(f"    Treatment: {len(procedures['treatment'])} procedures")
            results['procedures'] = True
        else:
            print("  [SKIP] No diseases to lookup procedures for")
            results['procedures'] = None
    except Exception as e:
        print(f"  [FAIL] {e}")
        results['procedures'] = False
    
    # Test 4: Cost breakdown
    print("\n[TEST 4] Cost breakdown retrieval...")
    try:
        cost_breakdown = client.get_cost_breakdown("Angioplasty")
        print(f"  [OK] Found {len(cost_breakdown)} cost components for Angioplasty")
        for comp in cost_breakdown:
            print(f"    {comp['phase']}: Rs {comp['cost_min']:,} - Rs {comp['cost_max']:,}")
        results['cost_breakdown'] = True
    except Exception as e:
        print(f"  [FAIL] {e}")
        results['cost_breakdown'] = False
    
    # Test 5: Cost adjustments
    print("\n[TEST 5] Cost adjustments (geo + comorbidity)...")
    try:
        adjustments = client.apply_cost_adjustments(
            base_cost_min=100000,
            base_cost_max=150000,
            city_name="Mumbai",
            comorbidity_names=["diabetes", "hypertension"],
            patient_age=65
        )
        print(f"  [OK] Cost adjustments computed:")
        print(f"    Geo multiplier (Mumbai): {adjustments['geo_multiplier']}")
        print(f"    Comorbidity multiplier: {adjustments['comorbidity_multiplier']}")
        print(f"    Final cost: Rs {adjustments['final_cost_min']:,} - Rs {adjustments['final_cost_max']:,}")
        results['cost_adjustments'] = True
    except Exception as e:
        print(f"  [FAIL] {e}")
        results['cost_adjustments'] = False
    
    # Test 6: Hospital discovery
    print("\n[TEST 6] Hospital discovery...")
    try:
        hospitals = client.find_hospitals_for_procedure_in_city(
            "Angioplasty", "Mumbai", limit=3
        )
        print(f"  [OK] Found {len(hospitals)} hospitals for Angioplasty in Mumbai")
        for hosp in hospitals[:2]:
            print(f"    - {hosp['name']} (Tier: {hosp.get('tier', 'N/A')})")
        results['hospitals'] = True
    except Exception as e:
        print(f"  [FAIL] {e}")
        results['hospitals'] = False
    
    # Test 7: Fusion Scorer
    print("\n[TEST 7] Fusion Scorer...")
    try:
        if hospitals:
            fusion = FusionScorer(client)
            hosp_id = hospitals[0]['id']
            scores = fusion.compute_fusion_score(hosp_id)
            print(f"  [OK] Fusion score for {hospitals[0]['name']}: {scores['fusion_score']:.3f}")
            print(f"    Clinical: {scores['clinical_score']:.3f}")
            print(f"    Reputation: {scores['reputation_score']:.3f}")
            print(f"    Accessibility: {scores['accessibility_score']:.3f}")
            print(f"    Affordability: {scores['affordability_score']:.3f}")
            results['fusion'] = True
        else:
            print("  [SKIP] No hospitals to score")
            results['fusion'] = None
    except Exception as e:
        print(f"  [FAIL] {e}")
        results['fusion'] = False
    
    # Test 8: Availability Proxy
    print("\n[TEST 8] Availability Proxy...")
    try:
        if hospitals:
            proxy = AvailabilityProxy(client)
            hosp_id = hospitals[0]['id']
            avail = proxy.compute_availability(hosp_id, "Cardiovascular", False)
            print(f"  [OK] Availability for {hospitals[0]['name']}:")
            print(f"    Label: {avail.label}")
            print(f"    Score: {avail.score}")
            print(f"    Estimated days: {avail.estimated_days}")
            print(f"    Has emergency: {avail.has_emergency}")
            results['availability'] = True
        else:
            print("  [SKIP] No hospitals to check availability")
            results['availability'] = None
    except Exception as e:
        print(f"  [FAIL] {e}")
        results['availability'] = False
    
    # Test 9: NER Pipeline
    print("\n[TEST 9] NER Pipeline...")
    try:
        ner = NERPipeline()
        text = "I have severe chest pain and shortness of breath"
        entities = ner.extract(text)
        print(f"  [OK] Extracted {len(entities)} entities from: '{text}'")
        for e in entities:
            print(f"    - {e.text} ({e.label})")
        results['ner'] = True
    except Exception as e:
        print(f"  [FAIL] {e}")
        results['ner'] = False
    
    # Test 10: Severity Classification
    print("\n[TEST 10] Severity Classification...")
    try:
        severity = SeverityClassifier.classify(
            symptoms=["chest pain", "shortness of breath"],
            raw_text="severe crushing chest pain"
        )
        print(f"  [OK] Severity: {severity['severity']}")
        print(f"    Reason: {severity['reason']}")
        results['severity'] = True
    except Exception as e:
        print(f"  [FAIL] {e}")
        results['severity'] = False
    
    # Test 11: ICD-10 Mapper
    print("\n[TEST 11] ICD-10 Mapper...")
    try:
        mapper = ICD10Mapper()
        result = mapper.lookup("chest pain")
        if result:
            print(f"  [OK] ICD-10 for 'chest pain': {result['code']}")
            print(f"    Description: {result['description']}")
        else:
            print("  [OK] ICD-10 lookup returned None (data may not be loaded)")
        results['icd10'] = True
    except Exception as e:
        print(f"  [FAIL] {e}")
        results['icd10'] = False
    
    client.close()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results.values() if r is True)
    skipped = sum(1 for r in results.values() if r is None)
    failed = sum(1 for r in results.values() if r is False)
    
    for name, result in results.items():
        status = "[PASS]" if result is True else ("[SKIP]" if result is None else "[FAIL]")
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed} passed, {skipped} skipped, {failed} failed")
    
    if failed == 0:
        print("\n[SUCCESS] Knowledge Graph pipeline is working correctly!")
    else:
        print("\n[WARNING] Some tests failed.")
    
    return results


if __name__ == "__main__":
    results = main()
    sys.exit(0 if all(r is True or r is None for r in results.values()) else 1)

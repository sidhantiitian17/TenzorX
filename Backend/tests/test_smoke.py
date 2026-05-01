"""
Quick Smoke Test (Run First After Any Change)

5-test validation of the core ICD-10 pipeline.
Run immediately after fixing the ICD-10 issue.
"""

import sys
sys.path.insert(0, "d:/TenzorX/Backend")


def test_smoke_icd10_loader():
    """[1/5] ICD-10 loaded successfully"""
    from app.nlp import icd10_mapper
    # Clear singleton cache to ensure fresh load
    icd10_mapper._icd10_index = None
    idx = icd10_mapper.load_icd10()
    print(f"[1/5] ICD-10 loaded: {len(idx)} keywords")
    assert len(idx) > 100, f"Index too small: {len(idx)} keywords"
    return True


def test_smoke_lookup_chest_pain():
    """[2/5] chest pain lookup works"""
    from app.nlp.icd10_mapper import lookup_icd10
    r = lookup_icd10("chest pain")
    assert r, "No results for chest pain"
    print(f"[2/5] chest pain -> {r[0]['code']} ({r[0]['description']})")
    return True


def test_smoke_ner_pipeline():
    """[3/5] NER extracts entities with ICD codes"""
    from app.nlp.ner_pipeline import extract_and_standardize
    result = extract_and_standardize("I have chest pain and diabetes")
    assert result['entities'], "NER returned no entities"
    print(f"[3/5] NER entities: {result['icd_summary']}")
    return True


def test_smoke_severity_classifier():
    """[4/5] Severity classification works"""
    from app.nlp.ner_pipeline import extract_and_standardize
    from app.services.classifier import classify_severity
    result = extract_and_standardize("I have chest pain and diabetes")
    sev = classify_severity(result['entities'], result['raw_text'])
    print(f"[4/5] Severity: {sev}")
    return True


def test_smoke_cost_engine():
    """[5/5] Cost engine applies geographic multiplier"""
    from app.engines.cost_engine import calculate_adjusted_cost
    cost = calculate_adjusted_cost(300000, city_tier=3)
    print(f"[5/5] Tier 3 cost (knee replacement): Rs {cost:,}")
    assert 230000 <= cost <= 260000, f"Tier 3 cost out of range: {cost}"
    return True


if __name__ == "__main__":
    print("Running smoke tests...\n")
    
    tests = [
        test_smoke_icd10_loader,
        test_smoke_lookup_chest_pain,
        test_smoke_ner_pipeline,
        test_smoke_severity_classifier,
        test_smoke_cost_engine,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"FAIL: {test.__name__}: {e}")
            failed += 1
    
    print(f"\n{'=' * 50}")
    if failed == 0:
        print("ALL SMOKE TESTS PASSED")
        sys.exit(0)
    else:
        print(f"FAILED: {failed}/{len(tests)} tests")
        sys.exit(1)

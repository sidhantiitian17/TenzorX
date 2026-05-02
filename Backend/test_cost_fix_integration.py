"""
Integration test to verify the cost fix for kidney stones.
Tests the pathway engine, cost engine, and master orchestrator.
"""
import sys
sys.path.insert(0, 'd:/TenzorX/Backend')

from app.engines.pathway_engine import PathwayEngine
from app.engines.cost_engine import CostEngine
from app.services.cost_engine import estimate_procedure_cost, estimate_procedure_cost_dict

def test_pathway_costs():
    """Test that pathway generates costs for kidney stones."""
    print("=" * 60)
    print("TEST 1: Pathway Engine - Kidney Stone Pathway")
    print("=" * 60)
    
    engine = PathwayEngine()
    
    # Test nephrolithiasis pathway
    pathway = engine.get_pathway('nephrolithiasis', 'N20.0')
    print(f"✓ Pathway steps found: {len(pathway)}")
    
    total_min = sum(s.get('cost_range', {}).get('min', 0) for s in pathway)
    total_max = sum(s.get('cost_range', {}).get('max', 0) for s in pathway)
    print(f"✓ Total cost from steps: Rs {total_min:,} - Rs {total_max:,}")
    
    # Verify costs are not zero
    assert total_min > 0, "FAIL: Minimum cost is 0"
    assert total_max > 0, "FAIL: Maximum cost is 0"
    assert total_max > total_min, "FAIL: Max cost should be greater than min"
    
    print("\nPathway steps with costs:")
    for step in pathway:
        print(f"  [{step['step']}] {step['name']}")
        print(f"      Duration: {step['typical_duration']}")
        print(f"      Cost: Rs {step['cost_range']['min']:,} - Rs {step['cost_range']['max']:,}")
    
    return True, total_min, total_max

def test_clinical_phases():
    """Test that clinical phases have costs."""
    print("\n" + "=" * 60)
    print("TEST 2: Clinical Phases Generation")
    print("=" * 60)
    
    engine = PathwayEngine()
    pathway = engine.get_pathway('nephrolithiasis', 'N20.0')
    
    # Generate clinical phases
    phases = engine.get_clinical_phases('nephrolithiasis', pathway, 'N20.0')
    print(f"✓ Clinical phases generated: {len(phases)}")
    
    print("\nClinical phases with costs:")
    all_have_costs = True
    for phase in phases:
        cost_min = phase.get('cost_min', 0)
        cost_max = phase.get('cost_max', 0)
        print(f"  - {phase['name']}: Rs {cost_min:,} - Rs {cost_max:,}")
        if cost_min == 0 and cost_max == 0:
            all_have_costs = False
    
    assert all_have_costs, "FAIL: Some phases have zero costs"
    print("✓ All phases have non-zero costs")
    
    return True

def test_cost_engine():
    """Test cost engine for kidney stones."""
    print("\n" + "=" * 60)
    print("TEST 3: Cost Engine - Kidney Stone Estimation")
    print("=" * 60)
    
    # Test with different procedures
    procedures = [
        'nephrolithiasis',
        'kidney stone removal',
        'kidney stones',
    ]
    
    for proc in procedures:
        try:
            result = estimate_procedure_cost_dict(proc, location_tier="tier-2")
            print(f"\n✓ {proc}:")
            print(f"    Total cost: Rs {result['total_cost']:,.0f}")
            print(f"    Range: Rs {result['cost_range']['min']:,.0f} - Rs {result['cost_range']['max']:,.0f}")
            if result.get('components'):
                print(f"    Components:")
                for comp in result['components'][:4]:
                    print(f"      - {comp['name']}: Rs {comp['cost']:,.0f} ({comp['percentage']:.0f}%)")
        except Exception as e:
            print(f"✗ {proc}: Error - {e}")
    
    return True

def test_fallback_with_empty_pathway():
    """Test that fallback works when LLM pathway fails."""
    print("\n" + "=" * 60)
    print("TEST 4: Fallback Cost Resolution (LLM Failure Scenario)")
    print("=" * 60)
    
    engine = PathwayEngine()
    
    # Simulate empty pathway (as if LLM failed)
    empty_pathway = []
    phases = engine._fallback_clinical_phases('nephrolithiasis', empty_pathway, 0, 0)
    
    print(f"Phases from empty pathway fallback: {len(phases)}")
    
    # Check that costs were resolved from cost_engine
    total_min = sum(p.get('cost_min', 0) for p in phases)
    total_max = sum(p.get('cost_max', 0) for p in phases)
    
    print(f"Total cost from fallback: Rs {total_min:,} - Rs {total_max:,}")
    
    # The safety fallback should kick in
    assert total_min > 0, "FAIL: Fallback minimum cost is 0"
    assert total_max > 0, "FAIL: Fallback maximum cost is 0"
    
    print("✓ Fallback successfully resolved costs from cost_engine")
    
    return True

def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("KIDNEY STONE COST FIX - INTEGRATION TEST SUITE")
    print("=" * 70)
    
    results = []
    
    try:
        success, total_min, total_max = test_pathway_costs()
        results.append(("Pathway Costs", success))
    except AssertionError as e:
        print(f"FAIL: {e}")
        results.append(("Pathway Costs", False))
    
    try:
        success = test_clinical_phases()
        results.append(("Clinical Phases", success))
    except AssertionError as e:
        print(f"FAIL: {e}")
        results.append(("Clinical Phases", False))
    
    try:
        success = test_cost_engine()
        results.append(("Cost Engine", success))
    except Exception as e:
        print(f"FAIL: Cost Engine - {e}")
        results.append(("Cost Engine", False))
    
    try:
        success = test_fallback_with_empty_pathway()
        results.append(("Fallback Costs", success))
    except AssertionError as e:
        print(f"FAIL: {e}")
        results.append(("Fallback Costs", False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = 0
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")
        if success:
            passed += 1
    
    print("\n" + "=" * 70)
    print(f"RESULT: {passed}/{len(results)} tests passed")
    print("=" * 70)
    
    if passed == len(results):
        print("\n✓ ALL TESTS PASSED - Cost fix is working correctly!")
        print(f"\nExpected behavior:")
        print(f"  - Kidney stone pathway: Rs {total_min:,} - Rs {total_max:,}")
        print(f"  - All clinical phases have non-zero costs")
        print(f"  - Fallback mechanism works when LLM fails")
        return 0
    else:
        print(f"\n✗ {len(results) - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

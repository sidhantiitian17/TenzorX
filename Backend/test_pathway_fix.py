"""Test script to verify kidney stone pathway fix."""
import sys
sys.path.insert(0, 'd:/TenzorX/Backend')

from app.engines.pathway_engine import PathwayEngine

def test_kidney_stone_pathway():
    engine = PathwayEngine()
    
    # Test nephrolithiasis
    print("Testing 'nephrolithiasis' pathway:")
    pathway = engine.get_pathway('nephrolithiasis')
    print(f"  Steps found: {len(pathway)}")
    for step in pathway[:3]:
        print(f"  Step {step['step']}: {step['name']}")
        print(f"    Cost: Rs {step['cost_range']['min']:,} - Rs {step['cost_range']['max']:,}")
    
    # Test kidney stone removal
    print("\nTesting 'kidney stone removal' pathway:")
    pathway2 = engine.get_pathway('kidney stone removal')
    print(f"  Steps found: {len(pathway2)}")
    
    # Test clinical phases generation
    if pathway:
        print("\nTesting clinical phases generation:")
        phases = engine.get_clinical_phases('nephrolithiasis', pathway, 'N20.0')
        print(f"  Phases found: {len(phases)}")
        for phase in phases[:3]:
            print(f"  - {phase['name']}: Rs {phase['cost_min']:,} - Rs {phase['cost_max']:,}")
        
        total_min = sum(s.get('cost_range', {}).get('min', 0) for s in pathway)
        total_max = sum(s.get('cost_range', {}).get('max', 0) for s in pathway)
        print(f"\n  Total cost range: Rs {total_min:,} - Rs {total_max:,}")
    
    return len(pathway) > 0

if __name__ == "__main__":
    success = test_kidney_stone_pathway()
    print(f"\n{'PASS' if success else 'FAIL'}: Kidney stone pathway {'found' if success else 'NOT found'}")
    sys.exit(0 if success else 1)

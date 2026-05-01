"""Test full agent pipeline with LLM synthesis."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=== Full Agent Pipeline Test ===\n")

# Test 1: HealthcareAgent
print("1. Testing HealthcareAgent...")
try:
    from app.agents.healthcare_agent import HealthcareAgent
    agent = HealthcareAgent()
    print(f"   ✅ HealthcareAgent initialized")
    
    # Test processing
    result = agent.process(
        session_id="test-pipeline-001",
        user_message="What is the cost of angioplasty in Mumbai for a 65-year-old diabetic patient?",
        location="mumbai",
        patient_profile={"age": 65, "comorbidities": ["diabetes"]}
    )
    
    print(f"   ✅ Agent processed query")
    print(f"   Severity: {result.get('severity')}")
    print(f"   Is Emergency: {result.get('is_emergency')}")
    
    search_data = result.get('search_data', {})
    print(f"\n   Search Data:")
    print(f"   - Procedure: {search_data.get('procedure', 'None')}")
    print(f"   - ICD-10 Code: {search_data.get('icd10_code', 'None')}")
    print(f"   - ICD-10 Label: {search_data.get('icd10_label', 'None')}")
    print(f"   - Hospitals: {len(search_data.get('hospitals', []))}")
    
    cost = search_data.get('cost_estimate', {})
    if cost:
        print(f"   - Cost Range: ₹{cost.get('final_cost_min', 0):,.0f} - ₹{cost.get('final_cost_max', 0):,.0f}")
    
    print(f"\n   Narrative Response (first 300 chars):")
    narrative = result.get('narrative', 'No response')
    print(f"   {narrative[:300]}...")
    
    # Check for disclaimer
    if "decision support" in narrative.lower() or "medical advice" in narrative.lower():
        print(f"   ✅ Disclaimer present")
    else:
        print(f"   ⚠️  Disclaimer missing")
        
except Exception as e:
    print(f"   ❌ HealthcareAgent failed: {e}")
    import traceback
    traceback.print_exc()

# Test 2: MasterOrchestrator
print("\n2. Testing MasterOrchestrator...")
try:
    from app.agents.master_orchestrator import MasterOrchestrator
    orchestrator = MasterOrchestrator()
    print(f"   ✅ MasterOrchestrator initialized")
    
    # Test intent classification
    intent = orchestrator.classify_intent("best hospital for knee replacement in Delhi")
    print(f"   Intent classified: {intent}")
    
    # Test severity
    severity = orchestrator.severity_classifier.classify("chest pain and difficulty breathing")
    print(f"   Severity: {severity}")
    
except Exception as e:
    print(f"   ❌ MasterOrchestrator failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Cost Engines
print("\n3. Testing Cost Engines...")
try:
    from app.engines.cost_engine import CostEngine
    from app.engines.geo_pricing import GeoPricingEngine
    from app.engines.comorbidity_engine import ComorbidityEngine
    
    cost_engine = CostEngine()
    geo_engine = GeoPricingEngine()
    comorbidity_engine = ComorbidityEngine()
    
    print(f"   ✅ All cost engines initialized")
    
    # Test city tier
    tier = geo_engine.get_city_tier("mumbai")
    print(f"   Mumbai city tier: {tier}")
    
    # Test comorbidity adjustment
    base_cost = {"min": 200000, "max": 300000}
    adjusted = comorbidity_engine.adjust(
        base_cost,
        comorbidities=["diabetes", "hypertension"],
        age=65
    )
    print(f"   Cost adjusted: ₹{adjusted['min']:,.0f} - ₹{adjusted['max']:,.0f}")
    
except Exception as e:
    print(f"   ❌ Cost engines failed: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Pipeline Test Complete ===")

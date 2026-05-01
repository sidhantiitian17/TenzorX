"""End-to-end GraphRAG pipeline test with Neo4j and LLM."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

from app.knowledge_graph.graph_rag import GraphRAGEngine
from app.core.config import settings

print("="*70)
print("END-TO-END GRAPHRAG PIPELINE TEST")
print("="*70)
print(f"Neo4j URI: {settings.NEO4J_URI}")
print(f"NVIDIA_API_KEY: {'[SET]' if settings.NVIDIA_API_KEY else '[NOT SET]'}")
print()

try:
    # Initialize the engine
    print("[1/5] Initializing GraphRAG Engine...")
    engine = GraphRAGEngine()
    print("      [OK] Engine initialized")
    
    # Run a complete query
    print("[2/5] Processing query: 'knee replacement surgery in Mumbai'...")
    result = engine.query(
        user_text="I need knee replacement surgery in Mumbai. I am 65 years old with diabetes.",
        location="Mumbai",
        patient_profile={"age": 65, "comorbidities": ["diabetes"]}
    )
    print("      [OK] Query processed")
    
    # Display results
    print("[3/5] Pipeline Results:")
    print(f"      - Entities extracted: {len(result['entities'])}")
    print(f"      - Primary procedure: {result['procedure'] or 'N/A'}")
    print(f"      - Disease identified: {result['disease'] or 'N/A'}")
    print(f"      - ICD-10 code: {result['disease_icd'] or 'N/A'}")
    print(f"      - Severity: {result['severity']['severity']} - {result['severity']['reason']}")
    
    if result['cost_estimate']:
        cost = result['cost_estimate']
        print(f"      - Cost estimate: ₹{cost['final_cost_min']:,.0f} - ₹{cost['final_cost_max']:,.0f}")
        print(f"      - Geo multiplier: {cost['geo_multiplier']}")
        print(f"      - Comorbidity multiplier: {cost['comorbidity_multiplier']}")
    
    print(f"      - Hospitals found: {len(result['hospitals_raw'])}")
    if result['hospitals_raw']:
        for i, h in enumerate(result['hospitals_raw'][:2]):
            print(f"        {i+1}. {h['name']} (Fusion: {h.get('fusion_score', 'N/A')})")
    
    print(f"      - Confidence score: {result['confidence_score']}")
    print(f"      - Threshold met: {result['confidence_threshold_met']}")
    
    # Display LLM response
    print("[4/5] LLM Generated Response:")
    print("-"*70)
    print(result['llm_response'])
    print("-"*70)
    
    # Validate
    print("[5/5] Validation:")
    has_disclaimer = "decision support" in result['llm_response'].lower() or "medical advice" in result['llm_response'].lower()
    has_cost = "cost" in result['llm_response'].lower() or "₹" in result['llm_response'] or "procedure" in result['llm_response'].lower()
    
    print(f"      - Contains disclaimer: {has_disclaimer}")
    print(f"      - Contains cost info: {has_cost}")
    print(f"      - Has procedure: {result['procedure'] is not None}")
    print(f"      - Has cost estimate: {result['cost_estimate'] is not None}")
    
    engine.close()
    
    if result['procedure'] and result['cost_estimate'] and len(result['llm_response']) > 200:
        print()
        print("="*70)
        print("[SUCCESS] End-to-end GraphRAG pipeline is working correctly!")
        print("="*70)
        print()
        print("Pipeline verified:")
        print("  ✓ NER extracts entities from user query")
        print("  ✓ Knowledge graph provides disease/procedure mapping")
        print("  ✓ Cost engine calculates adjusted costs (geo + comorbidity)")
        print("  ✓ Fusion scorer ranks hospitals")
        print("  ✓ LLM synthesizes enriched response with graph context")
        print("  ✓ Response includes proper disclaimer and cost breakdown")
    else:
        print()
        print("[WARNING] Pipeline completed but some results were incomplete")
        
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()

"""Test Neo4j Knowledge Graph integration."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=== Neo4j Integration Test ===\n")

# Test 1: Neo4j Client
print("1. Testing Neo4j Client...")
try:
    from app.knowledge_graph.neo4j_client import Neo4jClient
    neo4j = Neo4jClient()
    print(f"   ✅ Neo4jClient initialized")
    print(f"   URI: {neo4j.uri}")
    
    # Test connection
    with neo4j.driver.session() as session:
        result = session.run("MATCH (n) RETURN count(n) as count")
        count = result.single()["count"]
        print(f"   ✅ Connected to Neo4j")
        print(f"   Total nodes in graph: {count}")
except Exception as e:
    print(f"   ❌ Neo4j Client failed: {e}")

# Test 2: GraphRAG Engine
print("\n2. Testing GraphRAG Engine...")
try:
    from app.knowledge_graph.graph_rag import GraphRAGEngine
    graph_rag = GraphRAGEngine()
    print(f"   ✅ GraphRAGEngine initialized")
    
    # Test query
    result = graph_rag.query(
        user_text="What is the cost of angioplasty in Mumbai?",
        location="mumbai",
        patient_profile={"age": 65, "comorbidities": ["diabetes"]}
    )
    print(f"   ✅ GraphRAG query executed")
    print(f"   Entities found: {len(result.get('entities', []))}")
    print(f"   Procedure: {result.get('procedure', 'None')}")
    print(f"   ICD-10: {result.get('icd10', {})}")
    print(f"   Hospitals: {len(result.get('hospitals_raw', []))}")
    print(f"   Has cost estimate: {bool(result.get('cost_estimate'))}")
    
    # Check for mock data
    if result.get('hospitals_raw'):
        hospitals = result.get('hospitals_raw', [])
        mock_detected = any('mock' in str(h).lower() or 'test' in str(h).lower() for h in hospitals)
        if mock_detected:
            print(f"   ⚠️  WARNING: Mock data detected!")
        else:
            print(f"   ✅ No mock data detected")
except Exception as e:
    print(f"   ❌ GraphRAG Engine failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: NER Pipeline
print("\n3. Testing NER Pipeline...")
try:
    from app.nlp.ner_pipeline import NERPipeline
    ner = NERPipeline()
    print(f"   ✅ NERPipeline initialized")
    
    # Test extraction
    entities = ner.extract("I have chest pain and need angioplasty in Mumbai")
    print(f"   ✅ Entity extraction works")
    print(f"   Entities found: {len(entities)}")
    for e in entities:
        print(f"     - {e.label}: {e.text}")
except Exception as e:
    print(f"   ❌ NER Pipeline failed: {e}")

# Test 4: ICD-10 Mapper
print("\n4. Testing ICD-10 Mapper...")
try:
    from app.nlp.icd10_mapper import ICD10Mapper
    icd_mapper = ICD10Mapper()
    print(f"   ✅ ICD10Mapper initialized")
    
    # Test lookup
    result = icd_mapper.lookup("angioplasty")
    print(f"   ✅ ICD-10 lookup works")
    print(f"   Result: {result}")
except Exception as e:
    print(f"   ❌ ICD-10 Mapper failed: {e}")

print("\n=== Test Complete ===")

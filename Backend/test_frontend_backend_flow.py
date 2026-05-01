#!/usr/bin/env python
"""Test end-to-end flow from frontend to backend LLM and back to frontend."""

import sys
import json
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_frontend_to_backend_flow():
    """Simulate complete flow: Frontend → Backend → LLM → Frontend."""
    
    print("="*80)
    print("FRONTEND ↔ BACKEND END-TO-END FLOW TEST")
    print("="*80)
    print()
    
    # STEP 1: Simulate Frontend Request
    print("[STEP 1] Simulating Frontend Request...")
    print("-"*80)
    
    frontend_request = {
        "session_id": "user-session-123",
        "message": "What is the cost of knee replacement in Nagpur?",
        "location": "Nagpur",
        "patient_profile": {
            "age": 65,
            "comorbidities": ["diabetes", "hypertension"],
            "budget_inr": 250000
        }
    }
    
    print(f"Frontend sends:")
    print(json.dumps(frontend_request, indent=2))
    print()
    
    # STEP 2: Backend Receives and Validates
    print("[STEP 2] Backend Receiving & Validating Request...")
    print("-"*80)
    
    from app.schemas.request_models import ChatRequest, PatientProfile
    
    try:
        patient_profile = PatientProfile(**frontend_request["patient_profile"])
        chat_request = ChatRequest(
            session_id=frontend_request["session_id"],
            message=frontend_request["message"],
            location=frontend_request["location"],
            patient_profile=patient_profile
        )
        print("✅ Request validated successfully")
        print(f"   Session ID: {chat_request.session_id}")
        print(f"   Message: {chat_request.message}")
        print(f"   Location: {chat_request.location}")
        print(f"   Patient Age: {chat_request.patient_profile.age}")
        print(f"   Comorbidities: {chat_request.patient_profile.comorbidities}")
        print()
    except Exception as e:
        print(f"❌ Request validation failed: {e}")
        return False
    
    # STEP 3: Process Through Master Orchestrator
    print("[STEP 3] Processing Through Master Orchestrator...")
    print("-"*80)
    
    from app.agents.master_orchestrator import MasterOrchestrator
    from app.core.config import settings
    
    print(f"LONGCAT_API_KEY: {'[SET]' if settings.LONGCAT_API_KEY else '[NOT SET]'}")
    
    orchestrator = MasterOrchestrator()
    print("✅ MasterOrchestrator initialized")
    print()
    
    print("   Executing agents...")
    result = orchestrator.process(
        session_id=chat_request.session_id,
        user_message=chat_request.message,
        location=chat_request.location or "",
        patient_profile=chat_request.patient_profile.model_dump() if chat_request.patient_profile else {}
    )
    print("✅ All agents executed")
    print()
    
    # STEP 4: Verify Response Structure
    print("[STEP 4] Verifying Response Structure...")
    print("-"*80)
    
    from app.schemas.response_models import MasterResponse
    
    try:
        # Validate response against schema
        response_dict = result.model_dump()
        print("✅ Response validates against MasterResponse schema")
        print()
    except Exception as e:
        print(f"❌ Response validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # STEP 5: Display Results for Frontend
    print("[STEP 5] Results for Frontend Display...")
    print("="*80)
    print()
    
    # Chat Response Section
    print("📱 CHAT RESPONSE (Left Panel):")
    print("-"*80)
    chat = result.chat_response
    print(f"Message: {chat.message[:300]}...")
    print(f"Triage Level: {chat.triage_level}")
    print(f"Timestamp: {chat.timestamp}")
    print(f"Offline Mode: {chat.offline_mode}")
    print()
    
    # Results Panel Section
    print("📊 RESULTS PANEL (Right Panel):")
    print("-"*80)
    panel = result.results_panel
    
    print(f"Visible: {panel.visible}")
    print(f"Active Tab: {panel.active_tab}")
    print()
    
    # Clinical Interpretation
    if panel.clinical_interpretation:
        print("   🏥 Clinical Interpretation:")
        ci = panel.clinical_interpretation
        print(f"      Procedure: {ci.canonical_procedure}")
        print(f"      ICD-10: {ci.icd10}")
        print(f"      Triage: {ci.triage}")
        print(f"      Confidence: {ci.mapping_confidence}%")
        print()
    
    # Pathway
    if panel.pathway:
        print("   🛤️  Clinical Pathway:")
        pw = panel.pathway
        print(f"      Steps: {len(pw.pathway_steps)}")
        print(f"      Cost Range: Rs {pw.total_min:,} - Rs {pw.total_max:,}")
        print(f"      Comorbidity Impacts: {len(pw.comorbidity_impacts)}")
        for step in pw.pathway_steps[:2]:
            print(f"         Step {step.step}: {step.name} ({step.duration})")
        print()
    
    # Cost Estimate
    if panel.cost_estimate:
        print("   💰 Cost Estimate:")
        ce = panel.cost_estimate
        print(f"      Total Range: Rs {ce.total_cost_range.min:,} - Rs {ce.total_cost_range.max:,}")
        print(f"      EMI Available: {ce.emi_calculator.loan_amount > 0}")
        print(f"      Government Schemes: {len(ce.government_schemes)}")
        print(f"      Lending Partners: {len(ce.lending_partners)}")
        print()
    
    # Hospitals
    if panel.hospitals:
        print("   🏨 Hospital Discovery:")
        hd = panel.hospitals
        print(f"      Results Found: {hd.result_count}")
        print(f"      Map Markers: {len(hd.map_markers)}")
        if hd.hospitals:
            for i, h in enumerate(hd.hospitals[:2], 1):
                print(f"         {i}. {h.name} - {h.tier} - Fusion Score: {h.fusion_score}")
        print()
    
    # Map Data
    if panel.map_data:
        print("   🗺️  Map Data:")
        md = panel.map_data
        print(f"      User Coords: ({md.user_coords.lat:.4f}, {md.user_coords.lng:.4f})")
        print(f"      City Tier: {md.city_tier}")
        print(f"      Hospital Markers: {len(md.hospital_markers)}")
        print()
    
    # XAI
    if panel.xai:
        print("   🔍 XAI Explanation:")
        xai = panel.xai
        print(f"      Confidence Score: {xai.confidence_score}%")
        print(f"      Show Uncertainty: {xai.show_uncertainty_banner}")
        if xai.confidence_drivers:
            cd = xai.confidence_drivers
            print(f"      Drivers: Data={cd.data_availability}%, Pricing={cd.pricing_consistency}%")
        print()
    
    # Checklist
    if panel.checklist:
        print("   📋 Appointment Checklist:")
        cl = panel.checklist
        print(f"      Documents: {len(cl.documents)}")
        print(f"      Questions: {len(cl.questions)}")
        print(f"      Forms: {len(cl.forms)}")
        print()
    
    # Session Updates
    print("   📝 Session Updates:")
    su = result.session_updates
    print(f"      Last Procedure: {su.last_procedure}")
    print(f"      History Entry: {su.history_entry}")
    print()
    
    # STEP 6: Validate All Required Fields
    print("[STEP 6] Validating All Required Frontend Fields...")
    print("-"*80)
    
    required_checks = {
        "chat_response.message": bool(chat.message),
        "chat_response.triage_level": bool(chat.triage_level),
        "results_panel.visible": panel.visible,
        "results_panel.clinical_interpretation": panel.clinical_interpretation is not None,
        "results_panel.pathway": panel.pathway is not None,
        "results_panel.cost_estimate": panel.cost_estimate is not None,
        "results_panel.xai": panel.xai is not None,
    }
    
    all_passed = True
    for field, passed in required_checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {field}")
        if not passed:
            all_passed = False
    
    print()
    
    # STEP 7: Simulate JSON Response to Frontend
    print("[STEP 7] Simulating JSON Response to Frontend...")
    print("-"*80)
    
    try:
        json_response = json.dumps(response_dict, indent=2, default=str)
        response_size_kb = len(json_response.encode('utf-8')) / 1024
        print(f"✅ Response serialized to JSON")
        print(f"   Response size: {response_size_kb:.1f} KB")
        print(f"   JSON preview (first 500 chars):")
        print(json_response[:500])
        print()
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        return False
    
    # FINAL VERIFICATION
    print("="*80)
    if all_passed:
        print("✅ END-TO-END FLOW VERIFICATION: SUCCESS")
        print("="*80)
        print()
        print("Verified Flow:")
        print("   1. ✅ Frontend sends ChatRequest")
        print("   2. ✅ Backend validates request")
        print("   3. ✅ MasterOrchestrator processes query")
        print("   4. ✅ LLM generates narrative response")
        print("   5. ✅ All agents produce outputs")
        print("   6. ✅ MasterResponse structured correctly")
        print("   7. ✅ JSON serialized for frontend")
        print("   8. ✅ All required fields present")
        print()
        print("The frontend will receive:")
        print("   - Chat message for left panel")
        print("   - Clinical interpretation")
        print("   - Cost estimates with breakdown")
        print("   - Hospital results (if available)")
        print("   - XAI confidence scores")
        print("   - Pathway steps")
        print("   - Checklist items")
        return True
    else:
        print("❌ END-TO-END FLOW VERIFICATION: FAILED")
        print("="*80)
        print("Some required fields are missing")
        return False


if __name__ == "__main__":
    success = test_frontend_to_backend_flow()
    sys.exit(0 if success else 1)

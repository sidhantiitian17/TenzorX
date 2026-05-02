"""
Chat API route - Master Orchestrator Integration.

Primary conversational endpoint using the Master Orchestrator per instructionagent.md Section 4.
This endpoint provides the full Master Response Schema with all 7 agents.
"""

import logging
from fastapi import APIRouter, HTTPException
from app.schemas.request_models import ChatRequest
from app.schemas.response_models import (
    MasterResponse,
    ChatResponseData,
    ResultsPanelData,
    NERTriageOutput,
    ClinicalPathwayOutput,
    HospitalDiscoveryOutput,
    FinancialEngineOutput,
    GeoSpatialOutput,
    XAIExplainerOutput,
    AppointmentPaperworkOutput,
)
from app.agents.master_orchestrator import get_master_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()
orchestrator = get_master_orchestrator()

# Medical disclaimer for fallback responses
MANDATORY_MEDICAL_DISCLAIMER = (
    "This system provides decision support only and does not constitute medical advice or diagnosis"
)


@router.post("", response_model=MasterResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Master Orchestrator Chat Endpoint.
    
    Per instructionagent.md Section 4.3 - Master Response Schema:
    - Orchestrates all 7 agents: NER+Triage, Clinical Pathway, Hospital Discovery,
      Financial Engine, Geo-Spatial, XAI Explainer, Appointment & Paperwork
    - Returns structured response with full context for frontend rendering
    
    Args:
        request: ChatRequest with message, session_id, location, patient_profile
        
    Returns:
        MasterResponse with complete agent outputs
    """
    logger.info(f"📝 Master Orchestrator request: session={request.session_id}, message='{request.message[:50]}...'")
    
    try:
        # Process through Master Orchestrator
        result = orchestrator.process(
            session_id=request.session_id,
            user_message=request.message,
            location=request.location or "",
            patient_profile=request.patient_profile.model_dump() if request.patient_profile else {},
        )
        
        logger.info(f"✅ Master Orchestrator complete: {len(result.chat_response.message)} chars, "
                     f"triage={result.chat_response.triage_level}, "
                     f"hospitals={len(result.results_panel.hospitals.hospitals) if result.results_panel.hospitals else 0}")
        
        return result
        
    except RuntimeError as e:
        # LLM service unavailable - return graceful fallback that references actual query
        logger.warning(f"⚠️ LLM service unavailable, returning contextual fallback: {e}")
        
        # Extract condition from user message for contextual response
        user_message = request.message
        message_lower = user_message.lower()
        
        # Try to identify the health concern from the query
        concern = "your health concern"
        conditions = [
            ("kidney stone", "kidney stones"), ("kidney", "kidney condition"),
            ("heart", "heart condition"), ("chest pain", "chest pain"),
            ("diabetes", "diabetes"), ("sugar", "diabetes"),
            ("thyroid", "thyroid condition"), ("blood pressure", "blood pressure"),
            ("knee", "knee condition"), ("joint", "joint condition"),
            ("fracture", "fracture"), ("bone", "bone condition"),
            ("cancer", "cancer"), ("tumor", "tumor"),
            ("pregnancy", "pregnancy"), ("gynec", "gynecological concern"),
            ("eye", "eye condition"), ("vision", "vision concern"),
            ("tooth", "dental concern"), ("dental", "dental concern"),
            ("asthma", "asthma"), ("breathing", "breathing concern"),
            ("headache", "headache"), ("migraine", "migraine"),
            ("fever", "fever"), ("cold", "cold"), ("cough", "cough"),
            ("stomach", "stomach issue"), ("digestion", "digestive issue"),
        ]
        for keyword, condition_name in conditions:
            if keyword in message_lower:
                concern = condition_name
                break
        
        # Build contextual fallback response
        contextual_message = (
            f"**I understand you're asking about {concern}.** "
            f"I'm currently processing your query: \"{user_message[:80]}{'...' if len(user_message) > 80 else ''}\"\n\n"
            f"⚠️ The AI analysis service is temporarily experiencing high load or is unavailable. "
            f"Here's what I can tell you:\n\n"
            f"- Your query about **{concern}** has been received and logged\n"
            f"- The system is working to provide you with hospital and cost information\n"
            f"- Please try again in a moment for a complete, personalized response\n\n"
            f"**In the meantime:**\n"
            f"- If this is an emergency, call **112** immediately\n"
            f"- For urgent concerns, visit your nearest hospital\n"
            f"- For non-urgent questions, please retry your query shortly\n\n"
            f"{MANDATORY_MEDICAL_DISCLAIMER}"
        )
        
        # Build minimal fallback response with context
        fallback_response = MasterResponse(
            session_id=request.session_id,
            chat_response=ChatResponseData(
                message=contextual_message,
                triage_level="GREEN",
                confidence_score=0.5,
                disclaimer=MANDATORY_MEDICAL_DISCLAIMER,
            ),
            results_panel=ResultsPanelData(
                ner_triage=NERTriageOutput(
                    severity="GREEN",
                    rationale="Query received (LLM unavailable - operating in fallback mode)",
                    extracted_conditions=[],
                    icd10_codes=[],
                ),
                clinical_pathway=None,
                hospitals=HospitalDiscoveryOutput(agent="hospital_discovery", result_count=0, hospitals=[], map_markers=[]),
                map_data=GeoSpatialOutput(agent="geo_spatial", user_coords=None, city_tier=2, hospital_markers=[], map_config={}),
                cost_estimate=FinancialEngineOutput(agent="financial_engine", dti_ratio=0, risk_flag="Unknown", emi_options={}, government_schemes=[], lending_partners=[], call_to_action="Consult healthcare provider directly"),
                xai=XAIExplainerOutput(agent="xai_explainer", confidence_score=0.5, confidence_verdict="Fallback mode - limited analysis"),
                checklist=AppointmentPaperworkOutput(agent="appointment_paperwork", availability_proxy={}, documents=[], questions=[], forms=[]),
            ),
        )
        
        return fallback_response
        
    except Exception as e:
        logger.error(f"❌ Master Orchestrator failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

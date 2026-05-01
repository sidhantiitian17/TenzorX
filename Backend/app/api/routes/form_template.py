"""
Form Template API route.

Returns pre-filled PDF/TXT form templates for download.
Per instructionagent.md Section 6: GET /api/form-template/{form_name}

Supported forms:
- patient_registration
- medical_history_declaration
- consent_for_surgery
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/form-template", tags=["Form Templates"])

# Form templates (in production, these would be PDF generation or file serving)
FORM_TEMPLATES = {
    "patient_registration": {
        "title": "Patient Registration Form",
        "description": "Initial patient registration for hospital admission",
        "content": """
================================================================================
                         PATIENT REGISTRATION FORM
================================================================================

PERSONAL INFORMATION:

Full Name: _______________________________________
Date of Birth: _______________  Age: _______  Gender: _______

Aadhaar Number: ____________________  PAN: ____________________

Contact Number: ____________________  Email: ____________________

Address: _________________________________________________________
         _________________________________________________________
         City: ____________________  State: _______  PIN: _________


EMERGENCY CONTACT:

Name: _______________________________________
Relationship: ____________________  Phone: ____________________


INSURANCE INFORMATION (if applicable):

Insurance Provider: _______________________________________
Policy Number: ____________________
TPA Name: _______________________________________


DECLARATION:

I hereby declare that the information provided above is true and accurate
to the best of my knowledge. I consent to the hospital's terms and conditions.

Signature: _________________________  Date: _______________

================================================================================
                    For Hospital Use Only
================================================================================

Patient ID: ____________________  Date of Registration: _______________

Admitted By: _________________________  Signature: _________________________

================================================================================
""",
    },
    
    "medical_history_declaration": {
        "title": "Medical History Declaration",
        "description": "Patient medical history and current condition disclosure",
        "content": """
================================================================================
                      MEDICAL HISTORY DECLARATION
================================================================================

PATIENT INFORMATION:

Name: _______________________________________
Date: _______________  Age: _______  Gender: _______


CURRENT COMPLAINTS:

Please describe your current symptoms and concerns:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________


PAST MEDICAL HISTORY:

Have you had any of the following? (Check all that apply)

[ ] Diabetes          [ ] Hypertension    [ ] Heart Disease
[ ] Asthma            [ ] Kidney Disease  [ ] Liver Disease
[ ] Cancer            [ ] Stroke          [ ] Seizures/Epilepsy
[ ] Blood Disorders   [ ] Thyroid Issues  [ ] Other: ________________


CURRENT MEDICATIONS:

Please list all medications you are currently taking:

1. _______________________________________  Dosage: ________________
2. _______________________________________  Dosage: ________________
3. _______________________________________  Dosage: ________________
4. _______________________________________  Dosage: ________________


ALLERGIES:

Do you have any allergies? (Medications, food, etc.)
_________________________________________________________________


PREVIOUS SURGERIES/HOSPITALIZATIONS:

Please list any previous surgeries or hospital admissions:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________


FAMILY MEDICAL HISTORY:

Are there any hereditary conditions in your family?
_________________________________________________________________


LIFESTYLE INFORMATION:

Do you smoke? [ ] Yes  [ ] No  [ ] Former smoker
Do you consume alcohol? [ ] Yes  [ ] No  [ ] Occasionally
Exercise frequency: _______________________________________


DECLARATION:

I declare that I have provided accurate and complete information about my
medical history to the best of my knowledge. I understand that withholding
information may affect my treatment.

Patient Signature: _________________________  Date: _______________

================================================================================
""",
    },
    
    "consent_for_surgery": {
        "title": "Consent for Surgery/Procedure",
        "description": "Informed consent for surgical procedures",
        "content": """
================================================================================
                     CONSENT FOR SURGERY/PROCEDURE
================================================================================

PATIENT INFORMATION:

Name: _______________________________________
Age: _______  Gender: _______  Patient ID: ____________________


PROCEDURE INFORMATION:

Proposed Procedure: _______________________________________
Surgeon Name: _______________________________________
Date of Procedure: _______________


RISKS AND COMPLICATIONS:

The following risks and complications have been explained to me:

[ ] Bleeding requiring transfusion
[ ] Infection
[ ] Adverse reaction to anesthesia
[ ] Blood clots (DVT/PE)
[ ] Damage to surrounding structures
[ ] Need for additional procedures
[ ] Failure to resolve the condition
[ ] Death (rare but possible)

I understand that every surgical procedure carries inherent risks.


ALTERNATIVES DISCUSSED:

The following alternatives to surgery have been discussed:
_________________________________________________________________
_________________________________________________________________


POST-OPERATIVE CARE:

I understand the following about my recovery:
- Expected hospital stay: _______ days
- Restrictions after surgery: _________________________________
- Follow-up appointments required: ____________________________


CONSENT:

I, the undersigned, hereby consent to undergo the surgical procedure as
explained to me by the surgeon. I understand the risks, benefits, and
alternatives. I have had the opportunity to ask questions and all my
questions have been answered satisfactorily.


Patient/Guardian Signature: _________________________  Date: _______________

Witness Signature: _________________________  Name: _________________________

Surgeon Signature: _________________________  Date: _______________

================================================================================
""",
    },
    
    "insurance_pre_auth": {
        "title": "Insurance Pre-Authorization Request",
        "description": "Pre-authorization form for insurance/TPA",
        "content": """
================================================================================
                INSURANCE PRE-AUTHORIZATION REQUEST
================================================================================

HOSPITAL INFORMATION:

Hospital Name: _______________________________________
Hospital ID: ____________________  Contact: ____________________


PATIENT INFORMATION:

Patient Name: _______________________________________
Patient ID: ____________________  Age/Sex: _______/_______

Policy Number: ____________________
Insurance/TPA: _______________________________________


TREATMENT DETAILS:

Proposed Treatment: _______________________________________
Diagnosis (ICD-10): ____________________

Expected Admission: _______________  Expected Discharge: _______________

ESTIMATED COSTS:

Room Charges: Rs _____________
Procedure/Surgery: Rs _____________
Medicines/Consumables: Rs _____________
Investigations: Rs _____________
Other Charges: Rs _____________
----------------------------------------
TOTAL ESTIMATED: Rs _____________


DOCTOR'S CERTIFICATION:

I certify that the proposed treatment is medically necessary for the patient.

Doctor Name: _______________________________________
Registration No: ____________________  Signature: _________________________
Date: _______________


================================================================================
                    For TPA/Insurance Use Only
================================================================================

Pre-Auth ID: ____________________  Status: ____________________
Approved Amount: Rs _____________  Remarks: ____________________

Authorized By: _________________________  Date: _______________

================================================================================
""",
    },
}


@router.get(
    "/{form_name}",
    response_class=PlainTextResponse,
    status_code=status.HTTP_200_OK,
    summary="Get form template",
    description="Returns a pre-filled form template for download. "
                "Per instructionagent.md Section 6.",
)
async def get_form_template(form_name: str):
    """
    Get a form template by name.
    
    Args:
        form_name: One of: patient_registration, medical_history_declaration,
                   consent_for_surgery, insurance_pre_auth
                   
    Returns:
        Plain text form template
        
    Per instructionagent.md Section 6:
    GET /api/form-template/{form_name}
    form_name one of: patient_registration, medical_history_declaration, consent_for_surgery
    """
    try:
        logger.info(f"Form template requested: {form_name}")
        
        # Normalize form name
        form_name = form_name.lower().strip()
        
        if form_name not in FORM_TEMPLATES:
            available = ", ".join(FORM_TEMPLATES.keys())
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Form '{form_name}' not found. Available forms: {available}",
            )
        
        template = FORM_TEMPLATES[form_name]
        
        # In production, this could generate a PDF
        # For now, return plain text
        content = template["content"]
        
        logger.info(f"Returning form template: {template['title']}")
        
        # Return with headers that suggest a download
        return PlainTextResponse(
            content=content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f'attachment; filename="{form_name}.txt"',
                "X-Form-Title": template["title"],
                "X-Form-Description": template["description"],
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve form template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve form template: {str(e)}",
        )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List available form templates",
    description="Returns a list of all available form templates with metadata.",
)
async def list_form_templates():
    """
    List all available form templates.
    
    Returns:
        List of form template metadata
    """
    try:
        templates = [
            {
                "name": name,
                "title": data["title"],
                "description": data["description"],
                "url": f"/api/form-template/{name}",
            }
            for name, data in FORM_TEMPLATES.items()
        ]
        
        return {
            "count": len(templates),
            "templates": templates,
        }
        
    except Exception as e:
        logger.error(f"Failed to list form templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list form templates: {str(e)}",
        )

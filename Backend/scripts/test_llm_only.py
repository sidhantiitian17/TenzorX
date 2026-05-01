"""Test LLM synthesis with Knowledge Graph context."""
import sys
from pathlib import Path
import os

# Fix Unicode encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

from app.core.nvidia_client import NvidiaClient
from app.core.config import settings

print("="*60)
print("LLM SYNTHESIS TEST")
print("="*60)
print(f"NVIDIA_API_KEY: {'[SET]' if settings.NVIDIA_API_KEY else '[NOT SET]'}")
print()

llm = NvidiaClient(temperature=0.15, max_tokens=1024)

graph_context = """
{
  "procedure": "Angioplasty",
  "disease": "Coronary Artery Disease",
  "icd10": "I25.10",
  "cost_estimate": {
    "final_cost_min": 250000,
    "final_cost_max": 400000,
    "geo_multiplier": 1.0,
    "comorbidity_multiplier": 1.2
  },
  "hospitals": [
    {"name": "Apollo Hospital", "tier": "premium", "fusion_score": 0.85}
  ],
  "pathway": [
    {"phase": "pre_procedure", "cost_min": 15000, "cost_max": 25000},
    {"phase": "procedure", "cost_min": 200000, "cost_max": 350000},
    {"phase": "hospital_stay", "cost_min": 25000, "cost_max": 35000},
    {"phase": "post_procedure", "cost_min": 10000, "cost_max": 15000}
  ]
}
"""

system_prompt = """You are HealthNav, an AI healthcare navigator for Indian patients.
You use a Neo4j Knowledge Graph to provide accurate, grounded healthcare information.
You NEVER diagnose. You provide DECISION SUPPORT ONLY.

Response Rules:
1. ALWAYS end with: "⚕ This is decision support only — not medical advice."
2. Show costs as PHASED BREAKDOWNS (pre/procedure/stay/post) with adjusted ranges.
3. Reference fusion scores when explaining hospital rankings.
4. Be helpful, accurate, and empathetic. Use simple language.
"""

user_message = f"""
Patient query: What is the cost of angioplasty in Mumbai?

Knowledge Graph Context:
{graph_context}

Provide a helpful response with cost breakdown and hospital recommendations.
"""

print("Sending request to NVIDIA LLM...")
print()

try:
    response = llm.simple_prompt(
        prompt=user_message,
        system_prompt=system_prompt
    )
    
    print("="*60)
    print("LLM RESPONSE")
    print("="*60)
    print(response)
    print("="*60)
    
    # Validate response
    has_disclaimer = "decision support" in response.lower() or "medical advice" in response.lower()
    has_cost = any(x in response for x in ["250000", "400000", "Rs", "₹", "cost", "procedure"])
    
    print()
    print("VALIDATION:")
    print(f"  Contains disclaimer: {has_disclaimer}")
    print(f"  Contains cost info: {has_cost}")
    
    if has_disclaimer:
        print()
        print("[SUCCESS] LLM can synthesize responses using Knowledge Graph context!")
        print("[PASS] The LLM pipeline is working correctly.")
    else:
        print()
        print("[WARNING] Response missing disclaimer, but LLM is responding.")
        
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()

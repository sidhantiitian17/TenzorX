"""Simple LLM test."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app.core.nvidia_client import LLMClient

print("Initializing LLMClient...")
llm = LLMClient(temperature=0.15, max_tokens=256)

print(f"Model: {llm.model}")
print(f"API URL: {llm.__dict__.get('_api_url', 'using default')}")

print("\nSending test prompt...")
try:
    response = llm.simple_prompt(
        prompt="Hello! Please confirm you are working and say 'Longcat AI is responding properly.'",
        system_prompt="You are a helpful AI assistant."
    )
    print(f"\n✅ SUCCESS!")
    print(f"Response: {response}")
except Exception as e:
    print(f"\n❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

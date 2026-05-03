#!/usr/bin/env python
"""Quick LLM test"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("NVIDIA_API_KEY", "")
print("API Key: CONFIGURED" if api_key else "API Key: NOT SET")

if not api_key or "your-nvidia-api-key" in api_key:
    print("\n❌ NVIDIA_API_KEY not configured properly!")
    sys.exit(1)

try:
    from app.core.nvidia_client import NvidiaClient
    
    print("\n🔄 Initializing NvidiaClient...")
    client = NvidiaClient(temperature=0.15, max_tokens=100)
    
    print("🔄 Sending test prompt to NVIDIA LLM...")
    response = client.simple_prompt(
        prompt="Say 'Hello, I am working!' and confirm you are Mistral Large 3.",
        system_prompt="You are a helpful AI assistant."
    )
    
    print("\n✅ LLM RESPONSE:")
    print("=" * 50)
    print(response)
    print("=" * 50)
    print("\n🎉 LLM IS RESPONDING!")
    
except Exception as e:
    print(f"\n❌ LLM TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

"""Configuration verification script."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

print("=== Environment Variables ===")
lc_key = os.getenv("LONGCAT_API_KEY")
print(f"LONGCAT_API_KEY: {'SET (' + lc_key[:10] + '...)' if lc_key else 'NOT SET'}")
print(f"LONGCAT_BASE_URL: {os.getenv('LONGCAT_BASE_URL', 'NOT SET')}")
print(f"NEO4J_URI: {'SET' if os.getenv('NEO4J_URI') else 'NOT SET'}")
print(f"NEO4J_USER: {'SET' if os.getenv('NEO4J_USER') else 'NOT SET'}")
print(f"NEO4J_PASSWORD: {'SET' if os.getenv('NEO4J_PASSWORD') else 'NOT SET'}")

# Check settings module
from app.core.config import settings
print("\n=== Settings Module ===")
print(f"LONGCAT_BASE_URL: {settings.LONGCAT_BASE_URL}")
print(f"LONGCAT_API_KEY: {'SET' if settings.LONGCAT_API_KEY else 'NOT SET'}")
print(f"NEO4J_URI: {settings.NEO4J_URI}")

# Check client configuration
from app.core.nvidia_client import LONGCAT_API_URL, LONGCAT_MODEL
print("\n=== LLM Client ===")
print(f"LONGCAT_API_URL: {LONGCAT_API_URL}")
print(f"LONGCAT_MODEL: {LONGCAT_MODEL}")

print("\n✅ Configuration check complete")

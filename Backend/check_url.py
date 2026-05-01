"""Check the Longcat API URL."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app.core.nvidia_client import LONGCAT_API_URL
print(f"LONGCAT_API_URL: {repr(LONGCAT_API_URL)}")
print(f"URL length: {len(LONGCAT_API_URL)}")
print(f"Ends with 'completions': {LONGCAT_API_URL.endswith('completions')}")

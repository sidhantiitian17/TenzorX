"""Check the Longcat API URL - fresh import."""
import sys
import os

# Clear any cached modules
for mod in list(sys.modules.keys()):
    if 'app' in mod:
        del sys.modules[mod]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Re-import fresh
from app.core.nvidia_client import LONGCAT_API_URL
print(f"LONGCAT_API_URL: {repr(LONGCAT_API_URL)}")
print(f"Contains newline: {'\\n' in LONGCAT_API_URL}")

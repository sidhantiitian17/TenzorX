"""
Downloads the 2022 ICD-10 CM JSON dataset from GitHub.

Source: https://github.com/smog1210/2022-ICD-10-CM-JSON
"""

import requests
import json
import os
from pathlib import Path

URL = "https://raw.githubusercontent.com/smog1210/2022-ICD-10-CM-JSON/master/icd10cm_codes_2022.json"
OUTPUT = "data/icd10_2022.json"


def download_icd10():
    """Download ICD-10 CM 2022 data."""
    print(f"Downloading ICD-10 CM 2022 data...")
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ ICD-10 data saved to {OUTPUT}")
        print(f"  Total codes: {len(data)}")
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Download failed: {e}")
        print("  Please check your internet connection and try again.")
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON received: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


if __name__ == "__main__":
    download_icd10()

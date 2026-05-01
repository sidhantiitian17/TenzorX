"""
Downloads the 2022 ICD-10-CM JSON from the official CMS-derived GitHub repository.
Source: https://github.com/smog1210/2022-ICD-10-CM-JSON
"""

import os
import json
import urllib.request
import logging
import sys

logger = logging.getLogger(__name__)

ICD10_URL = (
    "https://raw.githubusercontent.com/smog1210/2022-ICD-10-CM-JSON"
    "/master/icd10cm_codes_2022.json"
)
DATA_DIR = "data"
ICD10_PATH = os.path.join(DATA_DIR, "icd10_2022.json")


def download_icd10():
    """Download ICD-10 CM 2022 data."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(ICD10_PATH):
        logger.info(f"ICD-10 data already exists at {ICD10_PATH}")
        try:
            with open(ICD10_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Validated existing file: {len(data)} codes")
            return True
        except Exception as e:
            logger.warning(f"Existing file invalid, re-downloading: {e}")
    
    try:
        logger.info(f"Downloading ICD-10 data from {ICD10_URL} ...")
        urllib.request.urlretrieve(ICD10_URL, ICD10_PATH)
        # Validate it is valid JSON
        with open(ICD10_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"ICD-10 download successful. Total codes: {len(data)}")
        return True
    except Exception as e:
        logger.error(f"Failed to download ICD-10 data: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    success = download_icd10()
    sys.exit(0 if success else 1)

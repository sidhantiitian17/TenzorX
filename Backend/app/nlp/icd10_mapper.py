"""
ICD-10 Code Mapper.

Maps extracted medical entities to ICD-10 CM codes using JSON lookup
and LLM-assisted fuzzy matching when direct lookup fails.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

from app.core.nvidia_client import NvidiaClient

logger = logging.getLogger(__name__)


class ICD10Mapper:
    """
    Maps medical entity text to ICD-10 CM codes.
    Uses 2022 ICD-10 CM JSON dataset as controlled vocabulary.
    LLM used for fuzzy matching when direct lookup fails.
    """

    DEFAULT_DATA_PATH = "data/icd10_2022.json"

    def __init__(self, icd10_json_path: Optional[str] = None):
        self.llm = NvidiaClient(temperature=0.0, max_tokens=512)
        
        data_path = icd10_json_path or self.DEFAULT_DATA_PATH
        self.code_map: Dict[str, str] = {}  # code -> description
        self.desc_map: Dict[str, str] = {}  # description_lower -> code
        
        self._load_data(data_path)

    def _load_data(self, data_path: str):
        """Load ICD-10 data from JSON file."""
        # Get the directory of this file (icd10_mapper.py)
        module_dir = Path(__file__).parent.resolve()
        backend_dir = module_dir.parent.parent  # app/nlp -> app -> Backend
        
        # Try multiple path strategies
        paths_to_try = [
            Path(data_path),  # As provided
            backend_dir / data_path,  # Relative to Backend dir
            module_dir / data_path,  # Relative to module dir
            Path(os.getcwd()) / data_path,  # Relative to cwd
            Path(os.getcwd()) / "Backend" / data_path,  # Backend subdir from cwd
        ]
        
        path = None
        for p in paths_to_try:
            if p.exists():
                path = p
                break
        
        if path is None:
            logger.error(f"ICD-10 data file not found. Tried: {[str(p) for p in paths_to_try]}")
            return

        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
            
            # Build lookup maps
            self._flatten_data(raw)
            
            # Build reverse map
            self.desc_map = {
                v.lower(): k for k, v in self.code_map.items()
            }
            
            logger.info(f"ICD-10 mapper loaded: {len(self.code_map)} codes")
            
        except Exception as e:
            logger.error(f"Failed to load ICD-10 data: {e}")

    def _flatten_data(self, data: Any, result: Optional[Dict[str, str]] = None):
        """Flatten nested ICD-10 JSON structure."""
        if result is None:
            result = {}
            
        if isinstance(data, dict):
            # Check if this is a code entry
            if "code" in data and "description" in data:
                code = data["code"]
                desc = data["description"]
                result[code] = desc
            
            # Recurse into nested structures
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    self._flatten_data(value, result)
                    
        elif isinstance(data, list):
            for item in data:
                self._flatten_data(item, result)
                
        self.code_map = result

    def lookup(self, term: str) -> Optional[Dict[str, str]]:
        """
        Look up ICD-10 code for a medical term.
        
        Step 1: Direct substring match in description map
        Step 2: LLM-assisted mapping if not found
        
        Args:
            term: Medical term or condition name
            
        Returns:
            Dict with "code" and "description" or None
        """
        term_lower = term.lower().strip()
        
        # Direct match
        if term_lower in self.desc_map:
            code = self.desc_map[term_lower]
            return {"code": code, "description": self.code_map[code]}
        
        # Partial substring match
        for desc, code in self.desc_map.items():
            if term_lower in desc or desc in term_lower:
                return {"code": code, "description": self.code_map[code]}
        
        # Word-level matching for compound terms
        term_words = set(term_lower.split())
        best_match = None
        best_score = 0
        
        for desc, code in self.desc_map.items():
            desc_words = set(desc.split())
            overlap = len(term_words & desc_words)
            if overlap > best_score and overlap >= len(term_words) * 0.5:
                best_score = overlap
                best_match = (code, desc)
        
        if best_match:
            return {"code": best_match[0], "description": best_match[1]}
        
        # LLM-assisted fuzzy mapping as fallback
        return self._llm_map(term)

    def _llm_map(self, term: str) -> Optional[Dict[str, str]]:
        """
        Use NVIDIA LLM to suggest the best ICD-10 code.
        
        Args:
            term: Medical term to map
            
        Returns:
            Dict with "code" and "description" or None
        """
        system_prompt = (
            "You are a medical coding assistant. Given a medical term or symptom, "
            "return ONLY the best matching ICD-10 CM code and its official description. "
            "Format: CODE|DESCRIPTION. Example: M17.11|Primary osteoarthritis, right knee. "
            "If unknown, return: UNKNOWN|unknown"
        )
        
        try:
            response = self.llm.simple_prompt(
                prompt=f"Find ICD-10 CM code for: {term}",
                system_prompt=system_prompt,
                temperature=0.0,
                max_tokens=100,
            )
            
            if "|" in response and "UNKNOWN" not in response.upper():
                parts = response.strip().split("|", 1)
                if len(parts) == 2:
                    code, description = parts
                    return {
                        "code": code.strip(),
                        "description": description.strip()
                    }
        except Exception as e:
            logger.warning(f"LLM mapping failed for '{term}': {e}")
        
        return None

    def batch_lookup(self, terms: List[str]) -> List[Dict[str, Any]]:
        """
        Map multiple terms and return all successful mappings.
        
        Args:
            terms: List of medical terms
            
        Returns:
            List of dicts with "term", "code", and "description"
        """
        results = []
        for term in terms:
            result = self.lookup(term)
            if result:
                results.append({
                    "term": term,
                    "code": result["code"],
                    "description": result["description"]
                })
        return results

    def get_description(self, code: str) -> Optional[str]:
        """Get description for an ICD-10 code."""
        return self.code_map.get(code)

    def search_by_description(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        """Search for codes by partial description match."""
        query_lower = query.lower()
        matches = []
        
        for code, desc in self.code_map.items():
            if query_lower in desc.lower():
                matches.append({"code": code, "description": desc})
                if len(matches) >= limit:
                    break
        
        return matches


# =============================================================================
# Module-level functions for test compatibility (TC-01 to TC-10)
# =============================================================================

_icd10_index: Optional[dict] = None  # lazy-loaded singleton

# Get module directory for reliable path resolution
_MODULE_DIR = Path(__file__).parent.resolve()
_BACKEND_DIR = _MODULE_DIR.parent.parent

SEARCH_PATHS = [
    _BACKEND_DIR / "data" / "icd10_2022.json",
    _BACKEND_DIR / "data" / "icd10_fallback.json",
    _MODULE_DIR / "data" / "icd10_2022.json",
    _MODULE_DIR / "data" / "icd10_fallback.json",
    Path("data/icd10_2022.json"),
    Path("data/icd10_fallback.json"),
    Path("Backend/data/icd10_2022.json"),
    Path("Backend/data/icd10_fallback.json"),
]


def _build_index(raw) -> dict:
    """
    Build a keyword -> [ICD codes] lookup dictionary.
    Supports both list-of-dicts and dict-with-code-keys formats.
    """
    index = {}
    
    # Handle dict format where keys are codes and values are descriptions
    if isinstance(raw, dict):
        for code, desc in raw.items():
            if not code or not desc:
                continue
            # Index every meaningful word in the description
            for word in str(desc).lower().split():
                word = word.strip(".,;:!?()")
                if len(word) > 2:  # skip very short words
                    index.setdefault(word, []).append({"code": code, "description": str(desc)})
    # Handle list format
    elif isinstance(raw, list):
        for entry in raw:
            code = entry.get("code", entry.get("Code", "")) if isinstance(entry, dict) else ""
            desc = entry.get("description", entry.get("desc", entry.get("Description", ""))) if isinstance(entry, dict) else ""
            if not code or not desc:
                continue
            # Index every meaningful word in the description
            for word in str(desc).lower().split():
                word = word.strip(".,;:!?()")
                if len(word) > 2:  # skip very short words
                    index.setdefault(word, []).append({"code": code, "description": str(desc)})
    return index


def load_icd10() -> dict:
    """
    Returns keyword index. Tries all paths. Auto-downloads if missing.
    Raises RuntimeError only if ALL fallbacks fail.
    
    This function is idempotent (singleton caching works) - TC-05.
    """
    global _icd10_index
    if _icd10_index is not None:
        return _icd10_index

    for path in SEARCH_PATHS:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                # Normalize: only if the dict has 'codes' or 'data' key
                if isinstance(raw, dict):
                    # Check if it's a wrapped format with codes/data key
                    if "codes" in raw or "data" in raw:
                        raw = raw.get("codes", raw.get("data"))
                    # Otherwise keep it as-is (it's already {code: desc} format)
                _icd10_index = _build_index(raw)
                logger.info(
                    f"ICD-10 loaded from '{path}'. "
                    f"Index size: {len(_icd10_index)} keywords."
                )
                return _icd10_index
            except Exception as e:
                logger.warning(f"Failed to load ICD-10 from '{path}': {e}")

    # Last resort: attempt download
    logger.warning("ICD-10 file not found in any location. Attempting download...")
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from setup_data import download_icd10
        if download_icd10():
            return load_icd10()  # recursive retry after download
    except Exception as e:
        logger.error(f"Auto-download failed: {e}")

    raise RuntimeError(
        "ICD-10 data unavailable. Run `python setup_data.py` to download it. "
        "Alternatively, ensure 'data/icd10_fallback.json' exists."
    )


def lookup_icd10(symptom_phrase: str, top_k: int = 3) -> list[dict]:
    """
    Maps a symptom phrase to the top_k most likely ICD-10 codes.
    
    Args:
        symptom_phrase: Free-text symptom, e.g. "severe chest pain"
        top_k: Maximum number of ICD codes to return
        
    Returns:
        List of dicts: [{"code": "R07.9", "description": "Chest pain, unspecified"}, ...]
        Returns empty list if no matches found (TC-09).
    """
    index = load_icd10()
    scores: dict[str, dict] = {}

    keywords = symptom_phrase.lower().split()
    for word in keywords:
        word = word.strip(".,;:!?()")
        matches = index.get(word, [])
        for match in matches:
            code = match["code"]
            scores[code] = scores.get(code, {"code": code, "description": match["description"], "score": 0})
            scores[code]["score"] += 1

    ranked = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
    return [{"code": r["code"], "description": r["description"]} for r in ranked[:top_k]]

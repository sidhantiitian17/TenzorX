"""
Named Entity Recognition (NER) Pipeline.

Uses spaCy with scispaCy for biomedical entity recognition,
plus custom rule-based matchers for Indian medical terminology.
"""

import re
import logging
from dataclasses import dataclass
from typing import List, Set

try:
    import spacy
except ImportError:
    spacy = None

logger = logging.getLogger(__name__)


@dataclass
class MedicalEntity:
    """Represents a medical entity extracted from text."""
    text: str
    label: str  # SYMPTOM | CONDITION | BODY_PART | PROCEDURE | DRUG
    start: int
    end: int
    normalized: str  # lowercased, stripped


class NERPipeline:
    """
    Extracts medical entities from free-text patient input.
    Uses scispaCy for biomedical NER + custom rule matcher.
    """

    # Custom symptom keywords for Indian context
    CUSTOM_SYMPTOMS: Set[str] = {
        "chest pain", "breathlessness", "shortness of breath",
        "radiating pain", "knee pain", "hip pain", "back pain",
        "blurred vision", "high fever", "low appetite", "fatigue",
        "swelling", "numbness", "palpitations", "dizziness",
        "headache", "nausea", "vomiting", "cough", "cold",
        "fever", "weakness", "tiredness", "sweating", "chills",
        "body ache", "joint pain", "muscle pain", "stomach pain",
        "abdominal pain", "diarrhea", "constipation", "heartburn",
        "loss of appetite", "weight loss", "weight gain",
        "difficulty breathing", "wheezing", "sore throat",
        "runny nose", "blocked nose", "ear pain", "toothache",
        "chest tightness", "irregular heartbeat", "fainting",
        "seizures", "tremors", "paralysis", "burning sensation",
        "itching", "rash", "skin discoloration", "hair loss",
    }

    # Custom procedure keywords
    CUSTOM_PROCEDURES: Set[str] = {
        "angioplasty", "bypass", "cabg", "knee replacement",
        "hip replacement", "cataract surgery", "dialysis",
        "chemotherapy", "lasik", "appendectomy", "cholecystectomy",
        "mri", "ct scan", "echocardiogram", "ecg", "ultrasound",
        "x-ray", "blood test", "urine test", "biopsy",
        "endoscopy", "colonoscopy", "bronchoscopy",
        "delivery", "cesarean", "c-section", "hysterectomy",
        "prostate surgery", "kidney stone removal", "gallstone removal",
        "hernia repair", "spine surgery", "brain surgery",
        "heart valve replacement", "pacemaker implant",
        "stent placement", "coronary angiography",
    }

    # Body parts
    CUSTOM_BODY_PARTS: Set[str] = {
        "head", "chest", "heart", "lungs", "liver", "kidney",
        "stomach", "abdomen", "back", "spine", "neck", "throat",
        "knee", "hip", "shoulder", "elbow", "wrist", "ankle",
        "eye", "ear", "nose", "mouth", "teeth", "skin",
        "arm", "leg", "hand", "foot", "brain", "bones",
        "muscles", "joints", "blood vessels", "nerves",
    }

    def __init__(self):
        self.nlp = None
        self._load_model()

    def _load_model(self):
        """Load spaCy model for biomedical NER."""
        if spacy is None:
            logger.warning("spaCy not available. Using rule-based NER only.")
            return

        # Try to load scispaCy model first, fall back to general English
        model_priority = ["en_core_sci_sm", "en_core_web_sm", "en_core_web_md"]
        
        for model_name in model_priority:
            try:
                self.nlp = spacy.load(model_name)
                logger.info(f"Loaded spaCy model: {model_name}")
                return
            except OSError:
                continue
        
        logger.warning("No spaCy model available. Using rule-based NER only.")

    def extract(self, text: str) -> List[MedicalEntity]:
        """
        Extract medical entities from patient input text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Deduplicated list of MedicalEntity objects
        """
        if not text or not text.strip():
            return []

        text_lower = text.lower()
        entities: List[MedicalEntity] = []

        # spaCy / scispaCy entity extraction
        if self.nlp:
            try:
                doc = self.nlp(text_lower)
                for ent in doc.ents:
                    label = self._map_spacy_label(ent.label_)
                    if label:
                        entities.append(MedicalEntity(
                            text=ent.text,
                            label=label,
                            start=ent.start_char,
                            end=ent.end_char,
                            normalized=ent.text.strip().lower(),
                        ))
            except Exception as e:
                logger.warning(f"spaCy NER failed: {e}")

        # Custom rule-based matching
        entities.extend(self._match_custom_patterns(text_lower))

        # Deduplicate by normalized text
        return self._deduplicate(entities)

    def _map_spacy_label(self, spacy_label: str) -> str:
        """Map spaCy/scispaCy labels to our label scheme."""
        label_map = {
            "DISEASE": "CONDITION",
            "CHEMICAL": "DRUG",
            "ANATOMY": "BODY_PART",
            "PROCEDURE": "PROCEDURE",
            "SYMPTOM": "SYMPTOM",
            "ENTITY": "CONDITION",  # scispaCy generic entity
        }
        return label_map.get(spacy_label)

    def _match_custom_patterns(self, text: str) -> List[MedicalEntity]:
        """Match custom keyword patterns in text."""
        entities = []
        
        # Match symptoms
        for symptom in self.CUSTOM_SYMPTOMS:
            for match in re.finditer(r'\b' + re.escape(symptom) + r'\b', text):
                entities.append(MedicalEntity(
                    text=symptom,
                    label="SYMPTOM",
                    start=match.start(),
                    end=match.end(),
                    normalized=symptom,
                ))
        
        # Match procedures
        for procedure in self.CUSTOM_PROCEDURES:
            for match in re.finditer(r'\b' + re.escape(procedure) + r'\b', text):
                entities.append(MedicalEntity(
                    text=procedure,
                    label="PROCEDURE",
                    start=match.start(),
                    end=match.end(),
                    normalized=procedure,
                ))
        
        # Match body parts
        for body_part in self.CUSTOM_BODY_PARTS:
            for match in re.finditer(r'\b' + re.escape(body_part) + r'\b', text):
                entities.append(MedicalEntity(
                    text=body_part,
                    label="BODY_PART",
                    start=match.start(),
                    end=match.end(),
                    normalized=body_part,
                ))
        
        return entities

    def _deduplicate(self, entities: List[MedicalEntity]) -> List[MedicalEntity]:
        """Remove duplicate entities based on normalized text."""
        seen: Set[str] = set()
        unique: List[MedicalEntity] = []
        
        for e in entities:
            key = f"{e.normalized}:{e.label}"
            if key not in seen:
                seen.add(key)
                unique.append(e)
        
        return unique

    def extract_symptoms(self, text: str) -> List[str]:
        """Convenience method to extract only symptom entities."""
        return [e.normalized for e in self.extract(text) if e.label == "SYMPTOM"]

    def extract_procedures(self, text: str) -> List[str]:
        """Convenience method to extract only procedure entities."""
        return [e.normalized for e in self.extract(text) if e.label == "PROCEDURE"]

    def extract_conditions(self, text: str) -> List[str]:
        """Convenience method to extract only condition entities."""
        return [e.normalized for e in self.extract(text) if e.label == "CONDITION"]

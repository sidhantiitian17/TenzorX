"""
NLP module for medical text processing.

Provides Named Entity Recognition, ICD-10 mapping, and sentiment analysis.
"""

from app.nlp.ner_pipeline import NERPipeline, MedicalEntity
from app.nlp.icd10_mapper import ICD10Mapper
from app.nlp.sentiment_absa import ABSAPipeline

__all__ = ["NERPipeline", "MedicalEntity", "ICD10Mapper", "ABSAPipeline"]

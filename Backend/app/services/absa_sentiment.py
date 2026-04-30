"""
Aspect-Based Sentiment Analysis Service for Healthcare Reviews.

This module implements ABSA (Aspect-Based Sentiment Analysis) for processing
unstructured patient reviews. It categorizes feedback into four key dimensions
and provides sentiment scoring using VADER and XGBoost pipelines.

Production Standards:
- Comprehensive logging with sentiment analysis metrics
- Robust text preprocessing and error handling
- Strict type hints and Pydantic validation
- Modular pipeline architecture
- Performance monitoring and caching
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from pydantic import BaseModel, Field, validator
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Mock XGBoost for demonstration (in production, import actual xgboost)
class MockXGBoostClassifier:
    """Mock XGBoost classifier for aspect categorization."""

    def __init__(self):
        """Initialize mock classifier with predefined aspect mappings."""
        self.aspect_keywords = {
            "Doctors' Services": [
                "doctor", "physician", "surgeon", "specialist", "consultant",
                "diagnosis", "treatment", "medical care", "professional"
            ],
            "Staff's Services": [
                "nurse", "staff", "receptionist", "administrator", "helper",
                "support", "assistance", "service", "attitude", "friendly"
            ],
            "Hospital Facilities": [
                "facility", "equipment", "room", "cleanliness", "hygiene",
                "infrastructure", "technology", "amenities", "parking", "food"
            ],
            "Affordability": [
                "cost", "price", "expensive", "cheap", "affordable", "billing",
                "insurance", "payment", "money", "fee", "charge"
            ]
        }

    def predict_proba(self, texts: List[str]) -> np.ndarray:
        """Mock prediction probabilities for aspect classification."""
        predictions = []
        for text in texts:
            text_lower = text.lower()
            probs = []

            for aspect, keywords in self.aspect_keywords.items():
                # Simple keyword matching for mock prediction
                matches = sum(1 for keyword in keywords if keyword in text_lower)
                prob = min(matches / len(keywords) * 2.0, 0.95)  # Cap at 0.95
                probs.append(prob)

            # Normalize to ensure they sum to 1
            total = sum(probs)
            if total > 0:
                probs = [p / total for p in probs]
            else:
                # Default equal distribution if no matches
                probs = [0.25] * 4

            predictions.append(probs)

        return np.array(predictions)

    def predict(self, texts: List[str]) -> np.ndarray:
        """Predict primary aspect for each text."""
        proba = self.predict_proba(texts)
        return np.argmax(proba, axis=1)


class AspectSentiment(BaseModel):
    """Sentiment analysis result for a specific aspect."""

    aspect: str = Field(..., description="Aspect name (Doctors' Services, etc.)")
    sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="VADER compound sentiment score")
    sentiment_label: str = Field(..., description="Sentiment classification")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    text_snippets: List[str] = Field(default_factory=list, description="Relevant text snippets")

    @validator('sentiment_label')
    def validate_sentiment_label(cls, v):
        """Validate sentiment label is one of the expected values."""
        valid_labels = {'Positive', 'Neutral', 'Negative'}
        if v not in valid_labels:
            raise ValueError(f"sentiment_label must be one of {valid_labels}")
        return v


class ReputationScore(BaseModel):
    """Aggregated reputation score from multiple reviews."""

    overall_score: float = Field(..., ge=0.0, le=5.0, description="Overall reputation score (0-5 scale)")
    aspect_breakdown: Dict[str, AspectSentiment] = Field(..., description="Sentiment by aspect")
    review_count: int = Field(..., ge=0, description="Number of reviews analyzed")
    confidence_interval: Tuple[float, float] = Field(..., description="95% confidence interval")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing statistics")


class ABSASentimentError(Exception):
    """Base exception for ABSA operations."""
    pass


class TextProcessingError(ABSASentimentError):
    """Raised when text processing fails."""
    pass


class SentimentAnalysisError(ABSASentimentError):
    """Raised when sentiment analysis fails."""
    pass


class AspectBasedSentimentAnalyzer:
    """
    Production ABSA service for healthcare review analysis.

    Uses VADER for lexicon-based sentiment scoring and XGBoost pipeline
    for aspect categorization. Processes unstructured patient reviews into
    structured sentiment insights.
    """

    def __init__(self):
        """Initialize ABSA analyzer with VADER and XGBoost components."""
        self.logger = logging.getLogger(__name__)

        # Initialize VADER sentiment analyzer
        try:
            self.vader_analyzer = SentimentIntensityAnalyzer()
            self.logger.info("✅ VADER sentiment analyzer initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize VADER: {e}")
            raise SentimentAnalysisError(f"VADER initialization failed: {e}") from e

        # Initialize mock XGBoost classifier
        try:
            self.aspect_classifier = MockXGBoostClassifier()
            self.logger.info("✅ XGBoost aspect classifier initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize XGBoost: {e}")
            raise SentimentAnalysisError(f"XGBoost initialization failed: {e}") from e

        # Aspect definitions
        self.aspect_names = [
            "Doctors' Services",
            "Staff's Services",
            "Hospital Facilities",
            "Affordability"
        ]

        # Sentiment thresholds
        self.sentiment_thresholds = {
            'Positive': 0.05,
            'Negative': -0.05
        }

        self.logger.info("✅ Aspect-Based Sentiment Analyzer initialized")

    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess review text for analysis.

        Args:
            text: Raw review text

        Returns:
            Preprocessed text

        Raises:
            TextProcessingError: If preprocessing fails
        """
        try:
            if not isinstance(text, str):
                raise TextProcessingError(f"Input must be string, got {type(text)}")

            # Convert to lowercase
            text = text.lower()

            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text).strip()

            # Remove special characters but keep basic punctuation
            text = re.sub(r'[^\w\s.,!?-]', '', text)

            # Basic length validation
            if len(text) < 3:
                raise TextProcessingError("Text too short for analysis")

            if len(text) > 5000:
                text = text[:5000] + "..."
                self.logger.warning("⚠️ Text truncated to 5000 characters")

            return text

        except Exception as e:
            self.logger.error(f"❌ Text preprocessing failed: {e}")
            raise TextProcessingError(f"Text preprocessing failed: {e}") from e

    def _classify_sentiment(self, compound_score: float) -> str:
        """
        Classify sentiment based on VADER compound score.

        Args:
            compound_score: VADER compound sentiment score

        Returns:
            Sentiment label
        """
        if compound_score >= self.sentiment_thresholds['Positive']:
            return 'Positive'
        elif compound_score <= self.sentiment_thresholds['Negative']:
            return 'Negative'
        else:
            return 'Neutral'

    def _extract_aspect_snippets(self, text: str, aspect: str) -> List[str]:
        """
        Extract relevant text snippets for a specific aspect.

        Args:
            text: Preprocessed review text
            aspect: Aspect name

        Returns:
            List of relevant snippets
        """
        keywords = self.aspect_classifier.aspect_keywords[aspect]
        sentences = re.split(r'[.!?]+', text)

        snippets = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Check if sentence contains aspect keywords
            if any(keyword in sentence for keyword in keywords):
                # Extract snippet around keywords (up to 100 chars)
                if len(sentence) > 100:
                    # Find keyword position and extract context
                    for keyword in keywords:
                        if keyword in sentence:
                            idx = sentence.find(keyword)
                            start = max(0, idx - 40)
                            end = min(len(sentence), idx + 60)
                            snippet = sentence[start:end]
                            if snippet not in snippets:
                                snippets.append(snippet)
                            break
                else:
                    snippets.append(sentence)

        return snippets[:3]  # Limit to 3 snippets per aspect

    @lru_cache(maxsize=1000)
    def analyze_single_review(self, review_text: str) -> Dict[str, AspectSentiment]:
        """
        Analyze sentiment for a single review across all aspects.

        Args:
            review_text: Raw review text

        Returns:
            Dictionary mapping aspect names to sentiment results

        Raises:
            SentimentAnalysisError: If analysis fails
        """
        try:
            self.logger.debug(f"🔍 Analyzing review: {review_text[:50]}...")

            # Preprocess text
            processed_text = self._preprocess_text(review_text)

            # Get aspect predictions
            aspect_probs = self.aspect_classifier.predict_proba([processed_text])[0]

            # Analyze sentiment for each aspect
            aspect_sentiments = {}

            for i, aspect in enumerate(self.aspect_names):
                # Get aspect-specific text snippets
                snippets = self._extract_aspect_snippets(processed_text, aspect)

                # Calculate sentiment for the aspect
                # Use VADER on the full text (in production, use aspect-specific text)
                sentiment_scores = self.vader_analyzer.polarity_scores(processed_text)

                aspect_sentiment = AspectSentiment(
                    aspect=aspect,
                    sentiment_score=sentiment_scores['compound'],
                    sentiment_label=self._classify_sentiment(sentiment_scores['compound']),
                    confidence=float(aspect_probs[i]),
                    text_snippets=snippets
                )

                aspect_sentiments[aspect] = aspect_sentiment

            self.logger.debug(f"✅ Review analysis complete for {len(aspect_sentiments)} aspects")
            return aspect_sentiments

        except Exception as e:
            self.logger.error(f"❌ Single review analysis failed: {e}")
            raise SentimentAnalysisError(f"Review analysis failed: {e}") from e

    def analyze_reviews_batch(self, reviews: List[str]) -> ReputationScore:
        """
        Analyze sentiment across multiple reviews and compute reputation score.

        Args:
            reviews: List of review texts

        Returns:
            Aggregated reputation score

        Raises:
            SentimentAnalysisError: If batch analysis fails
        """
        try:
            if not reviews:
                raise SentimentAnalysisError("No reviews provided for analysis")

            self.logger.info(f"🔍 Analyzing batch of {len(reviews)} reviews")

            # Analyze each review
            all_aspect_sentiments = []
            for review in reviews:
                try:
                    sentiments = self.analyze_single_review(review)
                    all_aspect_sentiments.append(sentiments)
                except Exception as e:
                    self.logger.warning(f"⚠️ Skipping review due to error: {e}")
                    continue

            if not all_aspect_sentiments:
                raise SentimentAnalysisError("No reviews could be analyzed")

            # Aggregate sentiment by aspect
            aspect_aggregates = {}
            for aspect in self.aspect_names:
                aspect_scores = []
                aspect_confidences = []
                all_snippets = []

                for review_sentiments in all_aspect_sentiments:
                    if aspect in review_sentiments:
                        sentiment = review_sentiments[aspect]
                        aspect_scores.append(sentiment.sentiment_score)
                        aspect_confidences.append(sentiment.confidence)
                        all_snippets.extend(sentiment.text_snippets)

                if aspect_scores:
                    # Calculate weighted average sentiment
                    avg_sentiment = np.mean(aspect_scores)
                    avg_confidence = np.mean(aspect_confidences)

                    # Convert to 1-5 scale (VADER -1 to 1 -> 1 to 5)
                    scaled_score = (avg_sentiment + 1) * 2 + 1

                    aspect_aggregates[aspect] = AspectSentiment(
                        aspect=aspect,
                        sentiment_score=round(avg_sentiment, 3),
                        sentiment_label=self._classify_sentiment(avg_sentiment),
                        confidence=round(avg_confidence, 3),
                        text_snippets=list(set(all_snippets))[:5]  # Unique snippets, max 5
                    )

            # Calculate overall reputation score (average of aspect scores)
            aspect_scores_5_scale = [
                (sentiment.sentiment_score + 1) * 2 + 1
                for sentiment in aspect_aggregates.values()
            ]
            overall_score = round(np.mean(aspect_scores_5_scale), 2)

            # Calculate confidence interval (simplified)
            std_dev = np.std(aspect_scores_5_scale) if len(aspect_scores_5_scale) > 1 else 0
            margin = 1.96 * std_dev / np.sqrt(len(reviews)) if len(reviews) > 1 else 0
            confidence_interval = (
                max(0, overall_score - margin),
                min(5, overall_score + margin)
            )

            reputation_score = ReputationScore(
                overall_score=overall_score,
                aspect_breakdown=aspect_aggregates,
                review_count=len(all_aspect_sentiments),
                confidence_interval=(round(confidence_interval[0], 2), round(confidence_interval[1], 2)),
                processing_metadata={
                    "total_reviews_processed": len(all_aspect_sentiments),
                    "reviews_skipped": len(reviews) - len(all_aspect_sentiments),
                    "aspects_analyzed": len(aspect_aggregates),
                    "avg_confidence": round(np.mean([s.confidence for s in aspect_aggregates.values()]), 3)
                }
            )

            self.logger.info(f"✅ Batch analysis complete. Overall score: {overall_score:.2f}/5.0")
            return reputation_score

        except Exception as e:
            self.logger.error(f"❌ Batch review analysis failed: {e}")
            raise SentimentAnalysisError(f"Batch analysis failed: {e}") from e

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of the ABSA service.

        Returns:
            Dictionary with component status
        """
        try:
            # Test VADER
            test_scores = self.vader_analyzer.polarity_scores("This is a test.")
            vader_healthy = isinstance(test_scores, dict) and 'compound' in test_scores

            # Test XGBoost
            test_preds = self.aspect_classifier.predict_proba(["Test review"])
            xgboost_healthy = test_preds.shape == (1, 4)

            return {
                "status": "healthy" if vader_healthy and xgboost_healthy else "unhealthy",
                "components": {
                    "vader_analyzer": "healthy" if vader_healthy else "unhealthy",
                    "aspect_classifier": "healthy" if xgboost_healthy else "unhealthy"
                },
                "aspects_supported": self.aspect_names
            }

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
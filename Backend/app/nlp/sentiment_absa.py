"""
Aspect-Based Sentiment Analysis (ABSA) Pipeline.

Analyzes patient reviews for sentiment across four key aspects:
- Doctors' Services
- Staff's Services  
- Hospital Facilities
- Affordability
"""

import re
import logging
from typing import List, Dict, Any

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

logger = logging.getLogger(__name__)


class ABSAPipeline:
    """
    Aspect-Based Sentiment Analysis on patient reviews.
    Uses VADER for compound sentiment scoring + keyword-based aspect extraction.
    """

    # Aspect keywords for Indian healthcare context
    ASPECT_KEYWORDS = {
        "doctors_services": [
            "doctor", "surgeon", "physician", "specialist", "consultation",
            "diagnosis", "treatment", "expertise", "bedside", "competent",
            "experience", "knowledgeable", "listened", "explained", "skilled",
            "professional", "caring", "dedicated", "thorough", "patient",
            "attentive", "communicative", "approachable", "confident",
        ],
        "staff_services": [
            "nurse", "staff", "attendant", "reception", "admin", "responsive",
            "helpful", "rude", "slow", "efficient", "friendly", "care",
            "supportive", "attentive", "polite", "cooperative", "courteous",
            "respectful", "prompt", "diligent", "hospitable", "warm",
        ],
        "hospital_facilities": [
            "clean", "hygiene", "equipment", "room", "ward", "icu", "bed",
            "infrastructure", "modern", "outdated", "crowded", "spacious",
            "parking", "cafeteria", "ambience", "ac", "air conditioning",
            "ventilation", "lighting", "maintenance", "renovated", "sterile",
            "organized", "comfortable", "accessible", "elevator", "lift",
        ],
        "affordability": [
            "cost", "price", "bill", "expensive", "cheap", "affordable",
            "transparent", "hidden charges", "overcharged", "value",
            "insurance", "cashless", "payment", "emi", "loan", "budget",
            "reasonable", "economical", "costly", "pricey", "inexpensive",
            "refund", "discount", "package", "estimate", "quotation",
        ],
    }

    # VADER thresholds
    POSITIVE_THRESHOLD = 0.05
    NEGATIVE_THRESHOLD = -0.05

    def __init__(self):
        self.vader = None
        if VADER_AVAILABLE:
            try:
                self.vader = SentimentIntensityAnalyzer()
                logger.info("VADER sentiment analyzer loaded")
            except Exception as e:
                logger.warning(f"Failed to load VADER: {e}")
        else:
            logger.warning("VADER not available. Install with: pip install vaderSentiment")

    def analyze_review(self, review_text: str) -> Dict[str, Dict[str, Any]]:
        """
        Analyze a single review and return sentiment per aspect.
        
        Args:
            review_text: Patient review text
            
        Returns:
            Dict mapping aspect names to sentiment data
        """
        if not review_text or not review_text.strip():
            return {aspect: {"score": 0, "label": "neutral", "mention_count": 0}
                    for aspect in self.ASPECT_KEYWORDS}
        
        sentences = self._split_sentences(review_text)
        aspect_sentiments: Dict[str, List[float]] = {
            aspect: [] for aspect in self.ASPECT_KEYWORDS
        }

        for sentence in sentences:
            sentence_lower = sentence.lower()
            matched_aspect = None
            max_matches = 0

            # Assign sentence to the aspect with most keyword matches
            for aspect, keywords in self.ASPECT_KEYWORDS.items():
                matches = sum(1 for kw in keywords if kw in sentence_lower)
                if matches > max_matches:
                    max_matches = matches
                    matched_aspect = aspect

            if matched_aspect and max_matches > 0:
                score = self._get_sentiment_score(sentence)
                aspect_sentiments[matched_aspect].append(score)

        # Aggregate per aspect
        result: Dict[str, Dict[str, Any]] = {}
        for aspect, scores in aspect_sentiments.items():
            if scores:
                avg = sum(scores) / len(scores)
                result[aspect] = {
                    "score": round(avg, 3),
                    "label": self._label(avg),
                    "mention_count": len(scores),
                }
            else:
                result[aspect] = {"score": 0, "label": "neutral", "mention_count": 0}

        return result

    def analyze_batch(self, reviews: List[str]) -> Dict[str, Any]:
        """
        Analyze a batch of reviews and return aggregated hospital sentiment report.
        
        Args:
            reviews: List of patient review texts
            
        Returns:
            Aggregated sentiment report with reputation score
        """
        if not reviews:
            return {
                "reputation_score": 50,
                "overall_sentiment": "neutral",
                "overall_positive_pct": 50,
                "aspects": {
                    aspect: {"avg_score": 0, "label": "neutral", 
                            "positive_pct": 50, "mention_count": 0}
                    for aspect in self.ASPECT_KEYWORDS
                }
            }
        
        all_aspect_scores: Dict[str, List[float]] = {
            aspect: [] for aspect in self.ASPECT_KEYWORDS
        }

        for review in reviews:
            result = self.analyze_review(review)
            for aspect, data in result.items():
                if data["mention_count"] > 0:
                    all_aspect_scores[aspect].append(data["score"])

        # Aggregate across all reviews
        overall_scores: List[float] = []
        aggregated: Dict[str, Any] = {}
        
        for aspect, scores in all_aspect_scores.items():
            if scores:
                avg = sum(scores) / len(scores)
                overall_scores.append(avg)
                
                positive_count = sum(1 for s in scores if s >= self.POSITIVE_THRESHOLD)
                positive_pct = round(positive_count / len(scores) * 100)
                
                aggregated[aspect] = {
                    "avg_score": round(avg, 3),
                    "label": self._label(avg),
                    "positive_pct": positive_pct,
                    "mention_count": len(scores),
                }
            else:
                aggregated[aspect] = {
                    "avg_score": 0, 
                    "label": "neutral",
                    "positive_pct": 50, 
                    "mention_count": 0
                }

        # Calculate overall reputation score (maps [-1,1] to [0,100])
        overall_avg = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        reputation_score = round((overall_avg + 1) / 2 * 100)
        
        # Calculate overall positive percentage
        if overall_scores:
            overall_positive = sum(1 for s in overall_scores if s >= self.POSITIVE_THRESHOLD)
            overall_positive_pct = round(overall_positive / len(overall_scores) * 100)
        else:
            overall_positive_pct = 50

        return {
            "reputation_score": max(0, min(100, reputation_score)),
            "overall_sentiment": self._label(overall_avg),
            "overall_positive_pct": overall_positive_pct,
            "aspects": aggregated,
        }

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting on sentence boundaries
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 5]

    def _get_sentiment_score(self, text: str) -> float:
        """Get compound sentiment score using VADER or fallback."""
        if self.vader:
            scores = self.vader.polarity_scores(text)
            return scores["compound"]
        
        # Fallback: simple keyword-based scoring
        text_lower = text.lower()
        positive_words = ["good", "great", "excellent", "best", "amazing", "wonderful", 
                         "helpful", "clean", "professional", "skilled", "efficient"]
        negative_words = ["bad", "terrible", "worst", "poor", "awful", "horrible",
                         "rude", "dirty", "unprofessional", "slow", "expensive"]
        
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        
        if pos_count > neg_count:
            return 0.5
        elif neg_count > pos_count:
            return -0.5
        return 0.0

    def _label(self, score: float) -> str:
        """Convert sentiment score to label."""
        if score >= self.POSITIVE_THRESHOLD:
            return "positive"
        elif score <= self.NEGATIVE_THRESHOLD:
            return "negative"
        return "neutral"

    def get_aspect_summary(self, reviews: List[str]) -> str:
        """Generate a human-readable summary of aspect sentiments."""
        analysis = self.analyze_batch(reviews)
        aspects = analysis["aspects"]
        
        summary_parts = []
        for aspect_name, data in aspects.items():
            if data["mention_count"] > 0:
                label = data["label"]
                display_name = aspect_name.replace("_", " ").title()
                summary_parts.append(f"{display_name}: {label} ({data['positive_pct']}% positive)")
        
        if not summary_parts:
            return "No specific aspects mentioned in reviews."
        
        return " | ".join(summary_parts)

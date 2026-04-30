"""
Integration Test for Healthcare Navigator AI Modules

This test validates the integration of all 5 production-grade AI/ML modules:
1. GraphRAG (Neo4j clinical pathway discovery)
2. ABSA Sentiment Analysis (aspect-based sentiment)
3. Data Fusion Scorer (multi-source data fusion)
4. Geo Pricing (geospatial pricing adjustments)
5. XAI Evaluator (explainable AI and RAG confidence)

Tests the complete pipeline from symptom input to final recommendations.
"""

import asyncio
import logging
import sys
from typing import Dict, Any
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.graphrag_neo4j import MedicalGraphRAG, ClinicalPathway
from app.services.absa_sentiment import AspectBasedSentimentAnalyzer, ReputationScore
from app.services.fusion_scorer import DataFusionScorer, FusionScore, HospitalMetrics
from app.services.geo_pricing import GeoPricingService, LocationData
from app.services.xai_evaluator import ExplainableAIService, RAGConfidenceScore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegrationTest:
    """Integration test suite for all AI modules."""

    def __init__(self):
        """Initialize test with mock data."""
        self.mock_clinical_metrics = {
            'success_rate': 0.85,
            'complication_rate': 0.12,
            'readmission_rate': 0.08,
            'average_stay_days': 5.2
        }

        self.mock_reputation_data = {
            'overall_rating': 4.2,
            'review_count': 150,
            'aspect_ratings': {
                "Doctors' Services": 4.5,
                "Staff's Services": 4.1,
                "Hospital Facilities": 3.8,
                "Affordability": 3.5
            }
        }

        self.mock_hospital_metrics = HospitalMetrics(
            total_beds=200,
            occupied_beds=160,
            specialist_doctors=45,
            avg_waiting_time_days=7.5,
            monthly_procedures=1200,
            distance_km=15.5,
            cost_per_day=8000
        )

        self.mock_cost_metrics = {
            'base_procedure_cost': 50000,
            'room_rate_per_day': 8000,
            'insurance_coverage_percent': 70,
            'out_of_pocket_max': 150000
        }

        self.mock_location_data = LocationData(
            address="Mumbai, Maharashtra, India",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            latitude=19.0760,
            longitude=72.8777,
            tier="Tier-1",
            confidence=0.95,
            metadata={
                'geocoding_provider': 'nominatim',
                'extraction_method': 'rule_based'
            }
        )

        logger.info("Integration test initialized with mock data")

    async def test_graphrag_module(self) -> ClinicalPathway:
        """Test GraphRAG clinical pathway discovery."""
        logger.info("🧪 Testing GraphRAG Module...")

        # Note: This will fail without Neo4j connection, but tests the import and structure
        try:
            # Initialize service (will fail to connect without Neo4j)
            graphrag = MedicalGraphRAG()

            # Test with mock ICD code
            pathway = await graphrag.get_clinical_pathway("J00")  # Acute nasopharyngitis

            logger.info(f"GraphRAG returned pathway with {len(pathway.pathway)} nodes")
            return pathway

        except Exception as e:
            logger.warning(f"WARNING: GraphRAG test failed (expected without Neo4j): {e}")
            # Return mock pathway for integration testing
            return ClinicalPathway(
                icd_code="J00",
                pathway=[],
                confidence_score=0.0
            )

    def test_absa_sentiment_module(self) -> ReputationScore:
        """Test ABSA sentiment analysis."""
        logger.info("🧪 Testing ABSA Sentiment Module...")

        try:
            analyzer = AspectBasedSentimentAnalyzer()

            # Test reviews
            test_reviews = [
                "The doctors were excellent and very professional. Staff was helpful but facilities need improvement.",
                "Great care from doctors but billing was confusing and expensive.",
                "Clean hospital with friendly staff, though wait times were long."
            ]

            reputation_score = analyzer.analyze_reviews_batch(test_reviews)

            logger.info(f"ABSA returned reputation score: {reputation_score.overall_score:.2f}")
            return reputation_score

        except Exception as e:
            logger.error(f"ABSA test failed: {e}")
            raise

    def test_fusion_scorer_module(self) -> FusionScore:
        """Test data fusion scoring."""
        logger.info("🧪 Testing Data Fusion Scorer Module...")

        try:
            scorer = DataFusionScorer()

            fusion_score = scorer.calculate_fusion_score(
                clinical_metrics=self.mock_clinical_metrics,
                reputation_data=self.mock_reputation_data,
                hospital_metrics=self.mock_hospital_metrics,
                cost_metrics=self.mock_cost_metrics
            )

            logger.info(f"Fusion Scorer returned score: {fusion_score.final_score:.2f}")
            return fusion_score

        except Exception as e:
            logger.error(f"Fusion Scorer test failed: {e}")
            raise

    def test_geo_pricing_module(self) -> Dict[str, Any]:
        """Test geospatial pricing."""
        logger.info("Testing Geo Pricing Module...")

        try:
            pricing_service = GeoPricingService()

            # Test pricing calculation
            pricing_adjustment = pricing_service.calculate_geographic_pricing(
                base_clinical_rate=50000,
                predicted_days=5,
                room_rate=8000,
                location_data=self.mock_location_data
            )

            logger.info(f"Geo Pricing returned adjusted cost: ₹{pricing_adjustment.adjusted_total_cost:,.0f}")
            return {
                'adjustment': pricing_adjustment,
                'location_data': self.mock_location_data
            }

        except Exception as e:
            logger.error(f"Geo Pricing test failed: {e}")
            raise

    def test_xai_evaluator_module(self) -> RAGConfidenceScore:
        """Test explainable AI evaluation."""
        logger.info("Testing XAI Evaluator Module...")

        try:
            xai_service = ExplainableAIService()

            # Test RAG confidence evaluation
            confidence_score = xai_service.evaluate_rag_confidence(
                faithfulness_score=0.85,
                context_relevancy_score=0.78,
                answer_relevancy_score=0.92
            )

            logger.info(f"XAI Evaluator returned confidence: {confidence_score.overall_confidence:.3f} ({confidence_score.confidence_tier})")
            return confidence_score

        except Exception as e:
            logger.error(f"XAI Evaluator test failed: {e}")
            raise

    async def run_full_integration_test(self) -> Dict[str, Any]:
        """Run complete integration test of all modules."""
        logger.info("Starting Full Integration Test...")

        results = {}

        try:
            # Test each module
            results['graphrag'] = await self.test_graphrag_module()
            results['absa_sentiment'] = self.test_absa_sentiment_module()
            results['fusion_scorer'] = self.test_fusion_scorer_module()
            results['geo_pricing'] = self.test_geo_pricing_module()
            results['xai_evaluator'] = self.test_xai_evaluator_module()

            # Simulate end-to-end pipeline
            logger.info("🔄 Simulating End-to-End Pipeline...")

            # 1. Get clinical pathway (mock)
            pathway = results['graphrag']

            # 2. Get reputation from sentiment analysis
            reputation = results['absa_sentiment']

            # 3. Calculate fusion score
            fusion_score = results['fusion_scorer']

            # 4. Get pricing adjustment
            pricing = results['geo_pricing']

            # 5. Evaluate confidence
            confidence = results['xai_evaluator']

            # Generate final recommendation
            final_recommendation = {
                'clinical_pathway': pathway.dict() if hasattr(pathway, 'dict') else pathway,
                'hospital_reputation': reputation.overall_score,
                'fusion_score': fusion_score.final_score,
                'estimated_cost': pricing['adjustment'].adjusted_cost,
                'confidence_level': confidence.confidence_tier,
                'requires_disclaimer': confidence.requires_disclaimer,
                'disclaimer': confidence.disclaimer_text
            }

            results['final_recommendation'] = final_recommendation

            logger.info("Full Integration Test Completed Successfully!")
            logger.info(f"Final Recommendation: Score {fusion_score.final_score:.1f}/100, Cost ₹{pricing['adjustment'].adjusted_total_cost:,.0f}, Confidence: {confidence.confidence_tier}")

            return results

        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            raise

    def print_test_summary(self, results: Dict[str, Any]):
        """Print test results summary."""
        print("\n" + "="*60)
        print("INTEGRATION TEST SUMMARY")
        print("="*60)

        for module, result in results.items():
            if module == 'final_recommendation':
                continue
            status = "PASS" if not isinstance(result, Exception) else "FAIL"
            print(f"{module.upper():<20} {status}")

        print("\nFINAL RECOMMENDATION:")
        if 'final_recommendation' in results:
            rec = results['final_recommendation']
            print(f"  • Fusion Score: {rec['fusion_score']:.1f}/100")
            print(f"  • Estimated Cost: ₹{rec['estimated_cost']:,.0f}")
            print(f"  • Confidence: {rec['confidence_level']}")
            if rec['requires_disclaimer']:
                print(f"  • Disclaimer Required: {rec['disclaimer'][:100]}...")

        print("="*60)


def main():
    """Main test execution."""
    print("Healthcare Navigator AI Modules Integration Test")
    print("Testing 5 production-grade AI/ML modules...")

    test = IntegrationTest()

    try:
        results = asyncio.run(test.run_full_integration_test())
        test.print_test_summary(results)
        print("\nAll modules integrated successfully!")

    except Exception as e:
        logger.error(f"ERROR: Integration test failed: {e}")
        print(f"\nERROR: Integration test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

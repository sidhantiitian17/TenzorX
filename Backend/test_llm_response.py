#!/usr/bin/env python
"""Test script to verify Longcat AI LLM is responding properly.

USAGE OPTIONS:
1. Run default tests:                    python test_llm_response.py
2. Test with custom prompt (CLI):        python test_llm_response.py "your prompt here"
3. Interactive mode:                     python test_llm_response.py --interactive
4. Quick mode (skip built-in tests):     python test_llm_response.py --quick

EDIT THE CUSTOM_PROMPT BELOW to test your specific use case:
"""

import os
import sys
import logging
import argparse
from dotenv import load_dotenv

# ============================================================================
# EDIT THIS VARIABLE FOR CUSTOM PROMPT TESTING
# ============================================================================
CUSTOM_PROMPT = "What is the cost of angioplasty in Nagpur for a 65-year-old diabetic patient?"
CUSTOM_SYSTEM = "You are HealthNav, a healthcare navigator AI for Indian patients."
CUSTOM_LOCATION = "nagpur"
# ============================================================================

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_api_key():
    """Check if Longcat AI API key is configured."""
    api_key = os.getenv("LONGCAT_API_KEY", "")
    if not api_key:
        logger.error("❌ LONGCAT_API_KEY not set properly!")
        logger.error("   Set it in .env file: LONGCAT_API_KEY=your-key-here")
        return None
    logger.info("✅ LONGCAT_API_KEY is configured.")
    return api_key


def test_custom_prompt(client, prompt=None, system=None, location=None):
    """Test LLM with a custom prompt."""
    prompt = prompt or CUSTOM_PROMPT
    system = system or CUSTOM_SYSTEM
    location = location or CUSTOM_LOCATION
    
    logger.info("\n" + "=" * 70)
    logger.info("🧪 CUSTOM PROMPT TEST")
    logger.info("=" * 70)
    logger.info(f"Prompt: {prompt}")
    logger.info(f"System: {system}")
    logger.info(f"Location: {location}")
    logger.info("=" * 70)
    
    try:
        # Test through the full agent pipeline
        logger.info("\n📡 Testing through HealthcareAgent (full pipeline)...")
        from app.agents.healthcare_agent import HealthcareAgent
        
        agent = HealthcareAgent()
        result = agent.process(
            session_id="test-custom-001",
            user_message=prompt,
            location=location,
            patient_profile={"age": 65, "comorbidities": ["diabetes"]}
        )
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ AGENT RESPONSE (Full Pipeline)")
        logger.info("=" * 70)
        logger.info(f"\nSeverity: {result.get('severity', 'N/A')}")
        logger.info(f"Is Emergency: {result.get('is_emergency', False)}")
        logger.info(f"\n--- NARRATIVE RESPONSE ---")
        print(f"\n{result.get('narrative', 'No response')}")
        
        search_data = result.get('search_data', {})
        if search_data:
            logger.info(f"\n--- SEARCH DATA ---")
            logger.info(f"Procedure: {search_data.get('procedure', 'N/A')}")
            logger.info(f"ICD-10: {search_data.get('icd10_code', 'N/A')}")
            logger.info(f"Hospitals found: {len(search_data.get('hospitals', []))}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Custom prompt test failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback to direct LLM test
        logger.info("\n📡 Falling back to direct LLMClient test...")
        try:
            response = client.simple_prompt(
                prompt=prompt,
                system_prompt=system
            )
            logger.info("\n" + "=" * 70)
            logger.info("✅ DIRECT LLM RESPONSE (Fallback)")
            logger.info("=" * 70)
            print(f"\n{response}")
            return True
        except Exception as e2:
            logger.error(f"❌ Direct LLM test also failed: {e2}")
            return False


def run_default_tests(client):
    """Run the default built-in tests."""
    logger.info("=" * 70)
    logger.info("Running Default Test Suite")
    logger.info("=" * 70)
    
    tests_passed = 0
    tests_total = 3
    
    # Test 1: Simple greeting
    try:
        logger.info("\n🧪 Test 1: Simple greeting prompt")
        response1 = client.simple_prompt(
            "Say hello and introduce yourself as an AI healthcare navigator."
        )
        logger.info(f"✅ Response: {response1[:150]}...")
        tests_passed += 1
    except Exception as e:
        logger.error(f"❌ Test 1 failed: {e}")
    
    # Test 2: Healthcare context
    try:
        logger.info("\n🧪 Test 2: Healthcare context prompt")
        response2 = client.simple_prompt(
            "A patient asks: 'What is the cost of knee replacement surgery in India?' Provide a helpful, brief response.",
            system_prompt="You are a helpful healthcare navigator AI for Indian patients."
        )
        logger.info(f"✅ Response: {response2[:200]}...")
        tests_passed += 1
    except Exception as e:
        logger.error(f"❌ Test 2 failed: {e}")
    
    # Test 3: Multi-turn conversation
    try:
        logger.info("\n🧪 Test 3: Multi-turn conversation")
        messages = [
            {"role": "user", "content": "Where can I find affordable angioplasty in Nagpur?"},
        ]
        response3 = client.chat(
            messages=messages,
            system_prompt="You are HealthNav, a healthcare navigator for Indian Tier 2/3 cities."
        )
        logger.info(f"✅ Response: {response3[:200]}...")
        tests_passed += 1
    except Exception as e:
        logger.error(f"❌ Test 3 failed: {e}")
    
    return tests_passed, tests_total


def interactive_mode(client):
    """Interactive prompt testing."""
    logger.info("\n" + "=" * 70)
    logger.info("🎮 INTERACTIVE MODE (type 'quit' to exit)")
    logger.info("=" * 70)
    
    from app.agents.healthcare_agent import HealthcareAgent
    agent = HealthcareAgent()
    session_id = "interactive-test"
    
    while True:
        print("\n" + "-" * 50)
        user_input = input("\nEnter your prompt (or 'quit'): ").strip()
        
        if user_input.lower() in ('quit', 'exit', 'q'):
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        try:
            print("\n🤖 Processing...")
            result = agent.process(
                session_id=session_id,
                user_message=user_input,
                location="nagpur",
                patient_profile={}
            )
            
            print("\n" + "=" * 50)
            print("📝 RESPONSE:")
            print("=" * 50)
            print(result.get('narrative', 'No response'))
            print("=" * 50)
            print(f"Severity: {result.get('severity', 'N/A')}")
            print(f"Session: {result.get('session_id')}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Test Longcat AI LLM via OpenAI-compatible API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python test_llm_response.py                    # Run default tests
  python test_llm_response.py "your prompt"      # Test custom prompt
  python test_llm_response.py --quick           # Quick mode (custom prompt only)
  python test_llm_response.py --interactive     # Interactive mode
        '''
    )
    parser.add_argument('prompt', nargs='?', help='Custom prompt to test')
    parser.add_argument('--quick', '-q', action='store_true', help='Quick mode - skip built-in tests')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--system', '-s', help='Custom system prompt')
    parser.add_argument('--location', '-l', default='nagpur', help='Location for healthcare queries')
    
    args = parser.parse_args()
    
    # Check API key
    if not check_api_key():
        return False
    
    # Initialize client
    try:
        from app.core.nvidia_client import LLMClient
        client = LLMClient(
            temperature=0.15,
            max_tokens=1024
        )
        logger.info(f"✅ LLMClient initialized with model: {client.model}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize LLMClient: {e}")
        return False
    
    # Interactive mode
    if args.interactive:
        interactive_mode(client)
        return True
    
    # Custom prompt test
    if args.prompt or args.quick:
        success = test_custom_prompt(
            client, 
            prompt=args.prompt or CUSTOM_PROMPT,
            system=args.system or CUSTOM_SYSTEM,
            location=args.location
        )
        return success
    
    # Default: run all tests
    tests_passed, tests_total = run_default_tests(client)
    
    # Also run custom prompt test
    logger.info("\n" + "=" * 70)
    logger.info("Now testing with custom prompt from file...")
    logger.info("=" * 70)
    custom_success = test_custom_prompt(client)
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Default tests passed: {tests_passed}/{tests_total}")
    logger.info(f"Custom prompt test: {'✅ PASSED' if custom_success else '❌ FAILED'}")
    
    if tests_passed == tests_total and custom_success:
        logger.info("\n🎉 ALL TESTS PASSED - LLM IS RESPONDING PROPERLY!")
        return True
    else:
        logger.info("\n⚠️  Some tests failed. Check logs above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

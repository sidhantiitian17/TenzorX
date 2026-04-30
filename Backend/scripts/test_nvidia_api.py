"""
Quick NVIDIA API validation script.

This script tests whether the NVIDIA API is reachable using the direct requests implementation.
Useful for debugging connectivity issues.

Usage:
    python scripts/test_nvidia_api.py

Prerequisites:
    requests library installed (pip install requests)
    NVIDIA_API_KEY set in .env file or environment variables
"""

import sys
import logging
import os

# Add Backend to path for importing settings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_nvidia_endpoint_connectivity():
    """Test that the NVIDIA API endpoint is reachable using API key from environment."""
    try:
        import requests
    except ImportError:
        logger.warning("⚠️  requests library not installed. Skipping connectivity test.")
        logger.info("   Install with: pip install requests")
        return None

    try:
        from app.core.config import settings

        endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
        api_key = ""

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "mistralai/mistral-large-3-675b-instruct-2512",
            "messages": [{"role": "user", "content": "Test message for validation"}],
            "max_tokens": 10,
            "temperature": 0.1,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stream": False
        }

        logger.info(f"🌐 Testing NVIDIA API endpoint: {endpoint}")
        response = requests.post(endpoint, headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            logger.info(f"✅ NVIDIA API is reachable (HTTP {response.status_code})")
            return True
        elif response.status_code == 401:
            logger.error(f"❌ Authentication failed (HTTP {response.status_code})")
            logger.error("   Check your NVIDIA_API_KEY in .env file")
            return False
        elif response.status_code == 429:
            logger.warning(f"⚠️  Rate limit exceeded (HTTP {response.status_code})")
            return None
        else:
            logger.error(f"❌ API error (HTTP {response.status_code}): {response.text}")
            return False

    except requests.exceptions.Timeout:
        logger.error("❌ Connection timeout - NVIDIA API took too long to respond")
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False


def test_direct_api_initialization():
    """Test that the direct NVIDIA API call function works."""
    try:
        sys.path.insert(0, 'd:/TenzorX/Backend')
        from app.services.langchain_agent import _call_nvidia_api

        logger.info("🔧 Testing direct NVIDIA API call...")

        # Test with a simple message
        messages = [{"role": "user", "content": "Hello, this is a test."}]
        response = _call_nvidia_api(messages, "test-session")

        if response and len(response.strip()) > 0:
            logger.info("✅ Direct API call successful")
            logger.info(f"   Response preview: {response[:100]}...")
            return True
        else:
            logger.error("❌ Direct API call returned empty response")
            return False

    except RuntimeError as e:
        logger.error(f"❌ Direct API call failed: {e}")
        return False
    except ImportError as e:
        logger.warning(f"⚠️  Could not import app modules: {e}")
        logger.info("   Make sure you're running from the Backend directory")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False


def main():
    """Run all validation tests."""
    logger.info("=" * 70)
    logger.info("NVIDIA LLM Integration Validation")
    logger.info("=" * 70)

    results = {
        "Endpoint Connectivity": test_nvidia_endpoint_connectivity(),
        "Direct API Init": test_direct_api_initialization(),
    }

    logger.info("=" * 70)
    logger.info("Validation Results:")
    logger.info("=" * 70)

    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️  SKIP"
        logger.info(f"{test_name:.<40} {status}")

    # Overall status
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)

    logger.info("=" * 70)
    if failed == 0:
        if passed == len(results):
            logger.info("✅ All tests passed! Your setup is ready.")
            return 0
        else:
            logger.info("⚠️  Some tests were skipped. Check dependencies.")
            return 1
    else:
        logger.info(f"❌ {failed} test(s) failed. Fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

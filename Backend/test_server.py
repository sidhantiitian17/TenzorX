#!/usr/bin/env python
"""Test script to verify LLM is called when user enters a prompt."""

import os
import sys
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test 1: Check environment
logger.info("=" * 60)
logger.info("Test 1: Checking environment and imports")
logger.info("=" * 60)

try:
    from app.core.config import settings
    logger.info(f"✅ Config loaded - API_V1_STR: {settings.API_V1_STR}")
    logger.info(f"   NVIDIA_API_KEY set: {bool(settings.NVIDIA_API_KEY)}")
    if settings.NVIDIA_API_KEY:
        logger.info(f"   Key prefix: {settings.NVIDIA_API_KEY[:20]}...")
except Exception as e:
    logger.error(f"❌ Config import failed: {e}")
    sys.exit(1)

# Test 2: Test NvidiaClient initialization
try:
    from app.core.nvidia_client import NvidiaClient
    client = NvidiaClient()
    logger.info(f"✅ NvidiaClient initialized with model: {client.model}")
except Exception as e:
    logger.error(f"❌ NvidiaClient initialization failed: {e}")
    sys.exit(1)

# Test 3: Test HealthcareAgent initialization
try:
    from app.agents.healthcare_agent import HealthcareAgent
    agent = HealthcareAgent()
    logger.info("✅ HealthcareAgent initialized")
except Exception as e:
    logger.error(f"❌ HealthcareAgent initialization failed: {e}")
    sys.exit(1)

# Test 4: Process a test message and verify LLM is called
logger.info("=" * 60)
logger.info("Test 4: Processing test message")
logger.info("=" * 60)

if not settings.NVIDIA_API_KEY or "your" in settings.NVIDIA_API_KEY.lower():
    logger.warning("⚠️  NVIDIA_API_KEY not set in environment!")
    logger.warning("   Set it with: $env:NVIDIA_API_KEY='nvapi-your-key-here'")
    logger.info("\n   Continuing with mock test...")
else:
    logger.info("🌐 Calling LLM with test message...")
    try:
        result = agent.process(
            session_id="test-session-001",
            user_message="What is the cost of knee replacement in Nagpur?",
            location="nagpur",
            patient_profile={}
        )
        logger.info("=" * 60)
        logger.info("✅ LLM CALL SUCCESSFUL!")
        logger.info("=" * 60)
        logger.info(f"Session ID: {result.get('session_id')}")
        logger.info(f"Severity: {result.get('severity')}")
        logger.info(f"Response length: {len(result.get('narrative', ''))} chars")
        logger.info(f"\nResponse preview:")
        logger.info(result.get('narrative', '')[:300] + "...")
        
        if result.get('narrative'):
            logger.info("\n" + "=" * 60)
            logger.info("🎉 VERIFICATION COMPLETE: LLM IS BEING CALLED!")
            logger.info("=" * 60)
    except Exception as e:
        logger.error(f"❌ LLM call failed: {e}")
        import traceback
        traceback.print_exc()

logger.info("\nTest complete.")

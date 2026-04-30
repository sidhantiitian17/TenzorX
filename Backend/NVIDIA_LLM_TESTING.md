# NVIDIA LLM Integration Testing Guide

## Quick Validation

### 1. **Check NVIDIA API Connectivity**

Run the validation script to test your setup before starting the backend:

```bash
cd Backend
python scripts/test_nvidia_api.py
```

This script validates:

- ✅ NVIDIA_API_KEY environment variable is set
- ✅ NVIDIA API endpoint is reachable
- ✅ LangChain ChatOpenAI can be initialized

### 2. **Set Environment Variables**

Create or update `.env` in `Backend/` directory:

```bash
NVIDIA_API_KEY=your-actual-api-key-here
DEBUG=true
LOG_LEVEL=DEBUG
```

### 3. **Run Unit Tests**

Test that the LLM is being called correctly:

```bash
pip install pytest pytest-mock

# Run all LangChain integration tests
pytest tests/test_langchain_integration.py -v

# Run specific test
pytest tests/test_langchain_integration.py::TestNVIDIALLMIntegration::test_process_query_invokes_chain -v

# Run with detailed output
pytest tests/test_langchain_integration.py -v -s
```

### 4. **Run Backend with Verbose Logging**

The backend now includes detailed logging showing when the LLM is called:

```bash
# Set log level to DEBUG to see all LLM calls
DEBUG=true
LOG_LEVEL=DEBUG

python main.py
```

You'll see logs like:
```
📋 Triage endpoint called
Phase 2 complete - Severity: Red
🤖 Phase 3: Calling NVIDIA LLM agent...
🚀 Calling NVIDIA LLM for session_id=mvp-session-1
✅ NVIDIA LLM successfully returned response for session_id=mvp-session-1
✅ LLM response received (1250 chars)
✅ Triage complete
```

### 5. **Test the Triage Endpoint**

Send a request to verify LLM integration:

```bash
curl -X POST "http://localhost:8000/api/v1/triage" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I have severe chest pain and shortness of breath",
    "location": {
      "city": "Mumbai",
      "tier": "Tier-1"
    },
    "financial_profile": {
      "budget_limit": 500000,
      "gross_monthly_income": 150000,
      "existing_emis": 25000
    }
  }'
```

Expected response includes `agent_response` field with the LLM-generated text.

## Error Handling

The system now detects and reports:

### API Key Issues

```text
❌ NVIDIA API authentication failed: Invalid or expired NVIDIA_API_KEY
```

### Connection Issues

```text
❌ Failed to connect to NVIDIA API endpoint: https://integrate.api.nvidia.com/v1
```

### Timeout Issues (>30s)

```text
❌ NVIDIA API timeout (30s exceeded)
```

### Rate Limiting

```text
❌ NVIDIA API rate limit exceeded. Please retry later.
```

## Log Levels

| Level  | What you see                      | Use case                      |
|--------|----------------------------------|-------------------------------|
| DEBUG  | All function calls, context formatting | Troubleshooting prompt issue |
| INFO   | LLM calls, response received, timing | Production monitoring         |
| WARNING| Non-critical failures (financial calc errors) | Alert on edge cases     |
| ERROR  | API failures, auth errors, timeouts | Critical debugging           |

## Missing NVIDIA_API_KEY?

If you don't have an API key yet, get one from:
1. Go to <https://build.nvidia.com/mistralai/mistral-large>
2. Sign in or create account
3. Copy your API key
4. Add to `.env`: `NVIDIA_API_KEY=nvapi-...`

## Production Deployment

Before deploying to production:

1. ✅ Run validation script successfully
2. ✅ Run full test suite without errors
3. ✅ Test triage endpoint with sample queries
4. ✅ Set `DEBUG=false` and `LOG_LEVEL=INFO`
5. ✅ Use secure API key management (AWS Secrets, K8s Secrets, etc.)
6. ✅ Monitor timeout errors and adjust as needed

## Troubleshooting

| Issue                  | Solution                                      |
|------------------------|-----------------------------------------------|
| "NVIDIA_API_KEY not found" | Add to .env and restart backend            |
| "Timeout exceeded"     | Increase API response time or check network  |
| "401 Unauthorized"     | Verify API key is current (keys expire)      |
| "Response took too long" | NVIDIA API may be overloaded, retry |
| "Empty LLM response" | Prompt template issue or model limitation |

## See Also

- [LangChain Documentation](https://python.langchain.com/)
- [NVIDIA API Docs](https://build.nvidia.com/)
- [Mistral Model Card](https://docs.mistral.ai/)

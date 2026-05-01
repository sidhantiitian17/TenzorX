#!/usr/bin/env python
"""Simple script to start the FastAPI server with logging."""

import uvicorn
import logging

# Configure logging to see LLM calls
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    print("=" * 60)
    print("Starting TenzorX Healthcare Navigator Backend")
    print("=" * 60)
    print("\nServer will start at: http://localhost:8000")
    print("API docs available at: http://localhost:8000/docs")
    print("\nTo test LLM, send a POST request to: http://localhost:8000/api/v1/chat")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True
    )

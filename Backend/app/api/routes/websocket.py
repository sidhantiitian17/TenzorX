"""
WebSocket API route for streaming LLM responses.

Per instructionagent.md Section 12:
- WebSocket: For streaming LLM responses (chat typing indicator)
- Use `/ws/chat/{session_id}`

Note: This requires WebSocket support to be enabled in the application.
"""

import logging
import json
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.agents.master_orchestrator import get_master_orchestrator
from app.agents.memory_manager import add_user_message, add_ai_message

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])

# Active connections store
_active_connections: Dict[str, WebSocket] = {}


@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for streaming chat responses.
    
    Allows real-time streaming of LLM responses with typing indicators.
    
    Args:
        websocket: WebSocket connection
        session_id: User session identifier
        
    Per instructionagent.md Section 12:
    - WebSocket: For streaming LLM responses (chat typing indicator)
    - Use `/ws/chat/{session_id}`
    
    Message Protocol:
    - Client sends: {"type": "message", "content": "user message", "location": "city", "patient_profile": {...}}
    - Server responds with chunks: {"type": "chunk", "content": "partial text"}
    - Server ends with: {"type": "complete", "final_response": {...}}
    """
    try:
        await websocket.accept()
        _active_connections[session_id] = websocket
        
        logger.info(f"WebSocket connection established for session: {session_id}")
        
        # Send connection acknowledgment
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "WebSocket connection established",
        })
        
        # Process messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                msg_type = message_data.get("type", "message")
                
                if msg_type == "message":
                    # Process user message
                    user_message = message_data.get("content", "")
                    location = message_data.get("location", "")
                    patient_profile = message_data.get("patient_profile", {})
                    
                    logger.info(f"WebSocket message received: {user_message[:50]}...")
                    
                    # Send typing indicator
                    await websocket.send_json({
                        "type": "typing",
                        "status": "started",
                    })
                    
                    # Process through orchestrator
                    orchestrator = get_master_orchestrator()
                    
                    # Add user message to history
                    add_user_message(session_id, user_message)
                    
                    try:
                        # Get response (non-streaming for now, can be enhanced)
                        response = orchestrator.process(
                            session_id=session_id,
                            user_message=user_message,
                            location=location,
                            patient_profile=patient_profile,
                        )
                        
                        # Simulate streaming by sending chunks of the narrative
                        narrative = response.chat_response.message
                        words = narrative.split()
                        chunk_size = 5
                        
                        for i in range(0, len(words), chunk_size):
                            chunk = " ".join(words[i:i+chunk_size])
                            await websocket.send_json({
                                "type": "chunk",
                                "content": chunk + " ",
                            })
                            # Small delay for typing effect
                            await asyncio.sleep(0.05)
                        
                        # Send final complete message with full data
                        await websocket.send_json({
                            "type": "complete",
                            "final_response": {
                                "message": response.chat_response.message,
                                "triage_level": response.chat_response.triage_level,
                                "results_panel": {
                                    "visible": response.results_panel.visible,
                                    "active_tab": response.results_panel.active_tab,
                                    "hospital_count": len(response.results_panel.hospitals.hospitals) if response.results_panel.hospitals else 0,
                                    "has_cost_estimate": response.results_panel.cost_estimate is not None,
                                },
                            },
                        })
                        
                        # Add AI response to history
                        add_ai_message(session_id, response.chat_response.message)
                        
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Failed to process message: {str(e)}",
                        })
                
                elif msg_type == "ping":
                    # Keep-alive ping
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": message_data.get("timestamp"),
                    })
                
                elif msg_type == "disconnect":
                    # Client requested disconnect
                    logger.info(f"Client requested disconnect for session {session_id}")
                    break
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for session {session_id}")
                break
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format",
                })
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                })
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        # Cleanup
        if session_id in _active_connections:
            del _active_connections[session_id]
        logger.info(f"WebSocket connection closed for session: {session_id}")


@router.get("/ws/status")
async def get_websocket_status():
    """
    Get WebSocket connection status.
    
    Returns:
        Active connection count and session IDs
    """
    return {
        "active_connections": len(_active_connections),
        "sessions": list(_active_connections.keys()),
    }

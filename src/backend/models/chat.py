"""
Chat-related Pydantic models
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., description="User's message", min_length=1)
    thread_id: Optional[str] = Field(None, description="Conversation thread ID (auto-generated if not provided)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Find flights from New York to London on January 15th",
                    "thread_id": "user-123-session"
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str = Field(..., description="Agent's response")
    thread_id: str = Field(..., description="Conversation thread ID")
    data_store: Dict[str, Any] = Field(..., description="Available data for UI")


class HistoryResponse(BaseModel):
    """Response model for conversation history"""
    thread_id: str
    messages: list

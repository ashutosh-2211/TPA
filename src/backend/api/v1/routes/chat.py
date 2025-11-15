"""
Chat API Routes

Handles AI agent chat interactions for travel planning
"""

from fastapi import APIRouter, HTTPException
import logging
import uuid

from services import chat, get_conversation_history, clear_data_store
from models import ChatRequest, ChatResponse, HistoryResponse

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


# ===== ENDPOINTS =====

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Chat with the Travel Planning AI Agent

    The agent can:
    - Search for flights between cities
    - Find hotels at destinations
    - Provide travel news and information

    Returns the agent's response and any data that was fetched.
    """
    try:
        # Generate thread_id if not provided
        thread_id = request.thread_id or f"session-{uuid.uuid4().hex[:12]}"

        logger.info("\n" + "=" * 100)
        logger.info("🚀 NEW CHAT REQUEST")
        logger.info(f"   Thread ID: {thread_id}")
        logger.info(f"   User Message: {request.message}")
        logger.info("=" * 100)

        # Get response from agent (now async)
        result = await chat(
            user_message=request.message,
            thread_id=thread_id
        )

        logger.info("\n" + "=" * 100)
        logger.info("✅ CHAT REQUEST COMPLETED")
        logger.info(f"   Thread ID: {thread_id}")
        logger.info(f"   Agent Response: {result['response'][:200]}...")
        logger.info(f"   Data Store Keys: {list(result.get('data_store', {}).keys())}")
        logger.info("=" * 100 + "\n")

        return ChatResponse(
            response=result["response"],
            thread_id=thread_id,
            data_store=result.get("data_store", {})
        )

    except Exception as e:
        logger.error(f"❌ Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )


@router.get("/history/{thread_id}", response_model=HistoryResponse)
async def get_history(thread_id: str):
    """
    Get conversation history for a specific thread

    Returns all messages in the conversation.
    """
    try:
        messages = get_conversation_history(thread_id)

        # Convert LangChain messages to dict format
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg.type if hasattr(msg, 'type') else "unknown",
                "content": msg.content if hasattr(msg, 'content') else str(msg)
            })

        return HistoryResponse(
            thread_id=thread_id,
            messages=formatted_messages
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving conversation history: {str(e)}"
        )


@router.delete("/clear-data")
async def clear_data():
    """
    Clear the data store

    Useful for resetting between test sessions or clearing cached data.
    """
    try:
        clear_data_store()
        return {"status": "success", "message": "Data store cleared"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing data store: {str(e)}"
        )

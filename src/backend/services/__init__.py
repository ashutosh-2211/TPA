"""
Services package for TPA (Travel Planning Agent)

Contains all business logic for:
- Flight search (flight_service.py)
- Hotel search (hotel_service.py)
- News search (news_service.py)
- AI Agent (ai_service.py)
- Configuration (config.py)
"""

# AI Service exports
from .ai_service import (
    chat,
    get_stored_data,
    clear_data_store,
    get_conversation_history,
    agent
)

# Individual service exports (if needed)
from . import flight_service
from . import hotel_service
from . import news_service
from . import config

__all__ = [
    # AI Agent functions
    'chat',
    'get_stored_data',
    'clear_data_store',
    'get_conversation_history',
    'agent',

    # Service modules
    'flight_service',
    'hotel_service',
    'news_service',
    'config'
]

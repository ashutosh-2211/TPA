"""
Data-related Pydantic models
"""

from pydantic import BaseModel, Field
from typing import Dict, Any


class DataResponse(BaseModel):
    """Response model for data retrieval"""
    data_type: str
    key: str
    data: Dict[str, Any]

"""
Data API Routes

Handles retrieval of full data (flights, hotels, news) for UI display
"""

from fastapi import APIRouter, HTTPException, Path
from typing import Literal

from services import get_stored_data
from models import DataResponse

router = APIRouter(prefix="/data", tags=["Data"])


# ===== ENDPOINTS =====

@router.get("/{data_type}/{key}", response_model=DataResponse)
async def get_data(
    data_type: Literal["flights", "hotels", "news"],
    key: str = Path(..., description="The request key used when storing the data")
):
    """
    Retrieve full data for flights, hotels, or news

    This returns complete data including images, links, and all details
    that were filtered out of the TOON format shown to the agent.

    Examples:
    - GET /data/flights/Mumbai_Delhi_2025-12-15
    - GET /data/hotels/Bali_2025-12-20_2025-12-25
    - GET /data/news/travel%20to%20Japan
    """
    try:
        data = get_stored_data(data_type, key)

        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for {data_type} with key: {key}"
            )

        return DataResponse(
            data_type=data_type,
            key=key,
            data=data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving data: {str(e)}"
        )


@router.get("/keys/{data_type}")
async def list_keys(data_type: Literal["flights", "hotels", "news"]):
    """
    List all available keys for a specific data type

    Useful for discovering what data is currently cached.
    """
    try:
        from services.ai_service import _data_store

        keys = list(_data_store.get(data_type, {}).keys())

        return {
            "data_type": data_type,
            "keys": keys,
            "count": len(keys)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing keys: {str(e)}"
        )

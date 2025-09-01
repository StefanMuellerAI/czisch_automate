"""General management routes."""

from fastapi import APIRouter, HTTPException
from app.database.init_data import initialize_all_test_data
import logging


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/manage", tags=["Management"])


@router.post("/init-test-data")
async def initialize_test_data():
    """Initialize database with test data."""
    try:
        instruction_ids = initialize_all_test_data()
        return {
            "message": "Test data initialized successfully",
            "results": instruction_ids,
        }
    except Exception as e:  # pragma: no cover - simple pass-through
        logger.error("Failed to initialize test data: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to initialize test data: {e}"
        )


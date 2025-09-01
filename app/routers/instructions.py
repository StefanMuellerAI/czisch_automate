"""Instruction management routes."""

from fastapi import APIRouter, HTTPException
from typing import List
from app.database.models import etl_db, URLInstruction
import logging


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/manage/instructions", tags=["Instructions"])


@router.get("")
async def get_all_instructions():
    """Get all URL instructions from database."""
    try:
        instructions = etl_db.get_all_instructions()
        return {
            "instructions": [instruction.to_dict() for instruction in instructions],
            "count": len(instructions),
        }
    except Exception as e:  # pragma: no cover - simple pass-through
        logger.error("Failed to get instructions: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to get instructions: {e}")


@router.get("/{url}")
async def get_instruction_for_url(url: str):
    """Get instruction for a specific URL."""
    try:
        instruction = etl_db.get_instruction_for_url(url)
        if instruction:
            return {"instruction": instruction.to_dict(), "found": True}
        return {
            "instruction": None,
            "found": False,
            "message": f"No instruction found for URL: {url}",
        }
    except Exception as e:  # pragma: no cover - simple pass-through
        logger.error("Failed to get instruction for URL %s: %s", url, e)
        raise HTTPException(status_code=500, detail=f"Failed to get instruction: {e}")


@router.delete("/{instruction_id}")
async def delete_instruction(instruction_id: int):
    """Delete URL instruction by ID."""
    try:
        deleted = etl_db.delete_instruction(instruction_id)
        if deleted:
            return {
                "message": f"Instruction {instruction_id} deleted successfully",
                "deleted": True,
            }
        raise HTTPException(
            status_code=404, detail=f"Instruction {instruction_id} not found"
        )
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - simple pass-through
        logger.error("Failed to delete instruction %s: %s", instruction_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to delete instruction: {e}")


@router.post("")
async def add_instruction(
    url_pattern: str,
    instructions: List[dict],
    return_format: str = "html",
    max_chars: int | None = None,
    description: str = "",
):
    """Add new URL instruction to the database."""
    try:
        instruction = URLInstruction(
            url_pattern=url_pattern,
            instructions=instructions,
            return_format=return_format,
            max_chars=max_chars,
            description=description,
        )
        instruction_id = etl_db.add_instruction(instruction)
        return {
            "message": "Instruction added successfully",
            "instruction_id": instruction_id,
            "instruction": instruction.to_dict(),
        }
    except Exception as e:  # pragma: no cover - simple pass-through
        logger.error("Failed to add instruction: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to add instruction: {e}")


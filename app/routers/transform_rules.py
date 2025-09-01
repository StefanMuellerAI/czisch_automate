"""Transform rule management routes."""

from fastapi import APIRouter, HTTPException
from typing import List
from app.database.models import etl_db, TransformRule
import logging


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/manage/transform-rules", tags=["Transform Rules"])


@router.get("")
async def get_all_transform_rules():
    """Get all transform rules from database."""
    try:
        rules = etl_db.get_all_transform_rules()
        return {
            "transform_rules": [rule.to_dict() for rule in rules],
            "count": len(rules),
        }
    except Exception as e:  # pragma: no cover - simple pass-through
        logger.error("Failed to get transform rules: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to get transform rules: {e}"
        )


@router.get("/{rule_name}")
async def get_transform_rule(rule_name: str):
    """Get transform rule by name."""
    try:
        rule = etl_db.get_transform_rule(rule_name)
        if rule:
            return {"transform_rule": rule.to_dict(), "found": True}
        return {
            "transform_rule": None,
            "found": False,
            "message": f"No transform rule found with name: {rule_name}",
        }
    except Exception as e:  # pragma: no cover - simple pass-through
        logger.error("Failed to get transform rule %s: %s", rule_name, e)
        raise HTTPException(
            status_code=500, detail=f"Failed to get transform rule: {e}"
        )


@router.post("")
async def add_transform_rule(
    rule_name: str,
    rules: List[dict],
    output_format: str = "xml",
    description: str = "",
):
    """Add new transform rule to the database."""
    try:
        transform_rule = TransformRule(
            rule_name=rule_name,
            rules=rules,
            output_format=output_format,
            description=description,
        )
        rule_id = etl_db.add_transform_rule(transform_rule)
        return {
            "message": "Transform rule added successfully",
            "rule_id": rule_id,
            "transform_rule": transform_rule.to_dict(),
        }
    except Exception as e:  # pragma: no cover - simple pass-through
        logger.error("Failed to add transform rule: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to add transform rule: {e}"
        )


@router.delete("/{rule_id}")
async def delete_transform_rule(rule_id: int):
    """Delete transform rule by ID."""
    try:
        deleted = etl_db.delete_transform_rule(rule_id)
        if deleted:
            return {
                "message": f"Transform rule {rule_id} deleted successfully",
                "deleted": True,
            }
        raise HTTPException(
            status_code=404, detail=f"Transform rule {rule_id} not found"
        )
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - simple pass-through
        logger.error("Failed to delete transform rule %s: %s", rule_id, e)
        raise HTTPException(
            status_code=500, detail=f"Failed to delete transform rule: {e}"
        )


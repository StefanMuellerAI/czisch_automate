"""SSH route management routes."""

from fastapi import APIRouter, HTTPException
from app.database.models import etl_db, SSHTransferRoute
from app.services.ssh_transfer_service import SSHTransferService
import logging


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/manage/ssh-routes", tags=["SSH Routes"])


@router.get("")
async def get_all_ssh_routes():
    """Get all SSH transfer routes from database."""
    try:
        routes = etl_db.get_all_ssh_routes()
        return {
            "ssh_routes": [route.to_dict(include_credentials=False) for route in routes],
            "count": len(routes),
        }
    except Exception as e:  # pragma: no cover - simple pass-through
        logger.error("Failed to get SSH routes: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to get SSH routes: {e}")


@router.get("/{route_id}")
async def get_ssh_route(route_id: str):
    """Get SSH route by route_id."""
    try:
        route = etl_db.get_ssh_route(route_id)
        if route:
            return {"ssh_route": route.to_dict(include_credentials=True), "found": True}
        return {
            "ssh_route": None,
            "found": False,
            "message": f"No SSH route found with ID: {route_id}",
        }
    except Exception as e:  # pragma: no cover - simple pass-through
        logger.error("Failed to get SSH route %s: %s", route_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to get SSH route: {e}")


@router.post("")
async def add_ssh_route(
    route_id: str,
    hostname: str,
    username: str,
    target_directory: str,
    port: int = 22,
    password: str = "",
    private_key: str = "",
    description: str = "",
):
    """Add new SSH transfer route with encrypted credentials."""
    try:
        if not password and not private_key:
            raise HTTPException(
                status_code=400,
                detail="Either password or private_key must be provided for authentication",
            )
        ssh_route = SSHTransferRoute(
            route_id=route_id,
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            private_key=private_key,
            target_directory=target_directory,
            description=description,
        )
        route_db_id = etl_db.add_ssh_route(ssh_route)
        return {
            "message": "SSH route added successfully",
            "route_db_id": route_db_id,
            "ssh_route": ssh_route.to_dict(include_credentials=True),
        }
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - simple pass-through
        logger.error("Failed to add SSH route: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to add SSH route: {e}")


@router.delete("/{route_db_id}")
async def delete_ssh_route(route_db_id: int):
    """Delete SSH route by database ID."""
    try:
        deleted = etl_db.delete_ssh_route(route_db_id)
        if deleted:
            return {
                "message": f"SSH route {route_db_id} deleted successfully",
                "deleted": True,
            }
        raise HTTPException(
            status_code=404, detail=f"SSH route {route_db_id} not found"
        )
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - simple pass-through
        logger.error("Failed to delete SSH route %s: %s", route_db_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to delete SSH route: {e}")


@router.post("/{route_id}/test")
async def test_ssh_connection(route_id: str):
    """Test SSH connection for a route."""
    try:
        result = await SSHTransferService.test_ssh_connection(route_id)
        return result
    except Exception as e:  # pragma: no cover - simple pass-through
        logger.error("Failed to test SSH connection: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Connection test failed: {e}"
        )


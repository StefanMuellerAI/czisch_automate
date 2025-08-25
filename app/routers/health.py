from fastapi import APIRouter
from app.models import HealthResponse
from app.services.playwright_service import playwright_service
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    Health Check Endpunkt
    
    Überprüft den Status der API und verfügbarer Services:
    - API-Status
    - Playwright-Browser-Verfügbarkeit
    - Anwendungsversion
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        playwright_available=playwright_service.is_available()
    )


@router.get("/status", response_model=HealthResponse)
async def detailed_status():
    """
    Detaillierter Status-Endpunkt
    
    Alias für den Health Check mit zusätzlichen Informationen
    """
    return await health_check()

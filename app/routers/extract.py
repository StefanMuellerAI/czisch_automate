from fastapi import APIRouter, HTTPException
from app.models import ExtractRequest, ExtractResponse
from app.services.extract_service import ExtractService
from app.services.playwright_service import playwright_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/extract", tags=["Extract"])


@router.post("", response_model=ExtractResponse)
async def extract_data(request: ExtractRequest):
    """
    Extract-Endpunkt für Datenextraktion
    
    Kann Daten aus verschiedenen Quellen extrahieren:
    
    **Web-Scraping (mit source_url):**
    - Automatische Extraktion von Titel und Textinhalt
    - Benutzerdefinierte CSS-Selektoren: `{"selectors": {"name": "css-selector"}}`
    - Meta-Tags extrahieren: `{"extract_meta": true}`
    - Links extrahieren: `{"extract_links": true}`
    
    **Datenextraktion (mit source_data):**
    - Spezifische Keys: `{"extract_keys": ["key1", "key2"]}`
    - Verschachtelte Pfade: `{"extract_paths": {"name": "path.to.value"}}`
    - Listen-Operationen:
      - Indizes: `{"extract_list": {"indices": [0, 1, 2]}}`
      - Erste N: `{"extract_list": {"first": 5}}`
      - Letzte N: `{"extract_list": {"last": 3}}`
      - Filterung: `{"extract_list": {"filter": {"field_equals": {"field": "status", "value": "active"}}}}`
    - JSONPath-Syntax: `{"json_path": "$.data.items[*].name"}`
    - Regex-Muster: `{"regex_patterns": {"email": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b"}}`
    
    **Filter-Optionen:**
    - `field_equals`: Feld muss bestimmten Wert haben
    - `has_field`: Feld muss existieren
    - `value_type`: Wert muss bestimmten Typ haben (string, number, boolean, etc.)
    """
    try:
        if not request.source_url and request.source_data is None:
            raise HTTPException(
                status_code=400,
                detail="Either source_url or source_data must be provided"
            )
        
        if request.source_url and not playwright_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Playwright browser not available for web scraping"
            )
        
        result = await ExtractService.extract_data(
            source_url=request.source_url,
            source_data=request.source_data,
            config=request.extraction_config
        )
        
        return ExtractResponse(
            extracted_data=result["extracted_data"],
            source=result["source"],
            message="Data extraction completed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extract error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Extract operation failed: {str(e)}"
        )

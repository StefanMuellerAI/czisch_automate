from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from app.models import ExtractRequest, ExtractResponse
from app.services.extract_service import ExtractService
from app.services.transform_service import TransformService
from app.services.xml_template_service import XMLTemplateService
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


@router.post("/to-taifun-xml")
async def extract_to_taifun_xml(
    source_url: str = Form(..., description="URL der Auftragsseite"),
    template_file: Optional[UploadFile] = File(None, description="Optional: Leeres Taifun XML-Template"),
    work_order_nr: Optional[str] = Form(None, description="Optional: Spezifische Auftragsnummer"),
    transform_rule: Optional[str] = Form("html_to_taifun_xml", description="Transform-Rule Name"),
    custom_selectors: Optional[str] = Form(None, description="Optional: JSON mit benutzerdefinierten CSS-Selektoren")
):
    """
    Extrahiert Auftragsdaten von einer Website und generiert Taifun XML
    
    **Workflow:**
    1. Daten von der Website extrahieren (Playwright)
    2. Mit Taifun Transform-Rule transformieren
    3. Mit leerem Template kombinieren (falls vorhanden)
    4. Vollständiges Taifun XML zurückgeben
    
    **Parameter:**
    - `source_url`: URL der Website mit Auftragsdaten
    - `template_file`: Optional - Leeres Taifun XML-Template hochladen
    - `work_order_nr`: Optional - Spezifische Auftragsnummer verwenden
    - `transform_rule`: Transform-Rule für die Konvertierung (Standard: html_to_taifun_xml)
    - `custom_selectors`: Optional - JSON mit benutzerdefinierten CSS-Selektoren für bekannte Websites
    
    **Beispiel custom_selectors:**
    ```json
    {
        "problem_description": ".beschreibung-text",
        "order_number": ".auftrag-nr",
        "appointment_date": ".termin-datum",
        "location_name": ".objekt-name"
    }
    ```
    """
    try:
        if not playwright_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Playwright browser not available for web scraping"
            )
        
        # 1. Custom selectors parsen falls vorhanden
        selectors_dict = None
        if custom_selectors:
            try:
                import json
                selectors_dict = json.loads(custom_selectors)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid JSON format in custom_selectors"
                )
        
        # 2. Auftragsdaten von Website extrahieren
        logger.info(f"Extracting work order data from: {source_url}")
        extracted_data = await playwright_service.extract_work_order_data(
            source_url, 
            custom_selectors=selectors_dict
        )
        
        # 3. Mit Taifun Transform-Rule transformieren
        logger.info(f"Transforming data with rule: {transform_rule}")
        xml_data = TransformService.transform_data(
            extracted_data, 
            {"database_rule": transform_rule}
        )
        
        # 4. Template-Verarbeitung falls vorhanden
        final_xml = xml_data
        if template_file:
            logger.info("Processing with uploaded template")
            template_content = await template_file.read()
            template_str = template_content.decode('windows-1252')
            
            # Template mit extrahierten Daten füllen
            final_xml = XMLTemplateService.populate_work_order_template(
                template_str,
                extracted_data,
                work_order_nr
            )
        
        # 5. XML validieren
        validation_result = XMLTemplateService.validate_taifun_xml(final_xml)
        
        return {
            "xml": final_xml,
            "extracted_data": extracted_data,
            "source_url": source_url,
            "validation": validation_result,
            "work_order_nr": work_order_nr,
            "transform_rule_used": transform_rule,
            "template_used": template_file is not None,
            "extraction_method": extracted_data.get("extraction_method", "intelligent"),
            "message": "Taifun XML generated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Taifun XML generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate Taifun XML: {str(e)}"
        )


@router.post("/work-order-data")
async def extract_work_order_data_only(
    source_url: str = Form(..., description="URL der Auftragsseite"),
    custom_selectors: Optional[str] = Form(None, description="Optional: JSON mit benutzerdefinierten CSS-Selektoren")
):
    """
    Extrahiert nur die Auftragsdaten von einer Website (ohne XML-Generierung)
    
    Nützlich zum Testen der Extraktion und zur Entwicklung von custom_selectors
    """
    try:
        if not playwright_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Playwright browser not available for web scraping"
            )
        
        # Custom selectors parsen falls vorhanden
        selectors_dict = None
        if custom_selectors:
            try:
                import json
                selectors_dict = json.loads(custom_selectors)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid JSON format in custom_selectors"
                )
        
        # Auftragsdaten extrahieren
        extracted_data = await playwright_service.extract_work_order_data(
            source_url, 
            custom_selectors=selectors_dict
        )
        
        return {
            "extracted_data": extracted_data,
            "source_url": source_url,
            "extraction_method": extracted_data.get("extraction_method", "intelligent"),
            "fields_found": list(extracted_data.keys()),
            "message": "Work order data extracted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Work order data extraction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract work order data: {str(e)}"
        )


@router.get("/available-transform-rules")
async def get_available_transform_rules():
    """
    Gibt alle verfügbaren Transform-Rules für Taifun XML zurück
    """
    try:
        from app.database.models import etl_db
        
        rules = etl_db.get_all_transform_rules()
        
        # Nur Taifun-relevante Rules filtern
        taifun_rules = [
            {
                "rule_name": rule.rule_name,
                "description": rule.description,
                "output_format": rule.output_format
            }
            for rule in rules 
            if "taifun" in rule.rule_name.lower() or "xml" in rule.output_format.lower()
        ]
        
        return {
            "available_rules": taifun_rules,
            "total_count": len(taifun_rules),
            "message": "Available transform rules retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to get transform rules: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve transform rules: {str(e)}"
        )

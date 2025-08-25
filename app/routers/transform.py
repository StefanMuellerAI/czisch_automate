from fastapi import APIRouter, HTTPException
from app.models import TransformRequest, TransformResponse
from app.services.transform_service import TransformService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transform", tags=["Transform"])


@router.post("", response_model=TransformResponse)
async def transform_data(request: TransformRequest):
    """
    Transform-Endpunkt für Datenmanipulation
    
    Dieser Endpunkt kann verschiedene Transformationen auf die eingehenden Daten anwenden:
    
    **String-Transformationen:**
    - `uppercase`, `lowercase`, `title_case`, `capitalize`: Groß-/Kleinschreibung
    - `strip`: Whitespace entfernen
    - `replace`: {"old": "text", "new": "replacement"}
    - `regex_replace`: {"pattern": "regex", "replacement": "text"}
    - `prefix`, `suffix`: Text hinzufügen
    
    **Numerische Transformationen:**
    - `multiply`: Mit `multiply_by` Wert
    - `add`: Mit `add_value` Wert
    - `subtract`: Mit `subtract_value` Wert
    - `divide`: Mit `divide_by` Wert
    - `round`: Mit `decimal_places`
    - `absolute`: Absoluter Wert
    
    **Dictionary-Transformationen:**
    - `filter_keys`: Mit `allowed_keys` Array
    - `exclude_keys`: Mit `excluded_keys` Array
    - `rename_keys`: Mit `key_mapping` Object
    - `add_timestamp`: Aktuellen Zeitstempel hinzufügen
    - `flatten`: Verschachtelte Dictionaries abflachen
    
    **List-Transformationen:**
    - `sort`: Mit optionalem `sort_reverse`
    - `limit`: Mit `limit_size`
    - `unique`: Duplikate entfernen
    - `filter_values`: Mit `allowed_values` Array
    
    **Allgemeine Transformationen:**
    - `to_json`: In JSON-String konvertieren
    - `from_json`: Von JSON-String parsen
    
    **HTML-zu-XML Transformationen (Database-basiert):**
    - `rule_name`: Name der Transformationsregel aus der Datenbank
    
    **Beispiel für HTML-zu-XML:**
    ```json
    {
        "data": "<html><body><h1>Title</h1><p>Content</p></body></html>",
        "transformation_rules": {
            "rule_name": "html_to_xml_basic"
        }
    }
    ```
    
    **Verfügbare Regel-Namen:**
    - `html_to_xml_basic`: Basis HTML-zu-XML Konvertierung
    - `html_to_xml_structured`: Strukturierte Extraktion mit Hierarchie
    - `html_to_xml_compact`: Kompakte XML-Zusammenfassung mit Metadaten
    """
    try:
        transformed_data = TransformService.transform_data(
            request.data,
            request.transformation_rules
        )
        
        return TransformResponse(
            transformed_data=transformed_data,
            message="Data transformation completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Transform error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Transform operation failed: {str(e)}"
        )

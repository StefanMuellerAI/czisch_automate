from fastapi import APIRouter, HTTPException
from typing import List
from app.database.models import etl_db, URLInstruction, TransformRule, SSHTransferRoute
from app.database.init_data import initialize_all_test_data
from app.services.ssh_transfer_service import SSHTransferService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/manage", tags=["Management"])


@router.post("/init-test-data")
async def initialize_test_data():
    """
    Initialize database with test data
    
    Erstellt Test-Daten in der Datenbank, einschließlich:
    - stefanai.de Beispiel
    - Weitere Beispiel-URLs für Tests
    """
    try:
        instruction_ids = initialize_all_test_data()
        return {
            "message": "Test data initialized successfully",
            "results": instruction_ids
        }
    except Exception as e:
        logger.error(f"Failed to initialize test data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize test data: {str(e)}")


@router.get("/instructions")
async def get_all_instructions():
    """
    Get all URL instructions from database
    
    Zeigt alle gespeicherten URL-Anweisungen
    """
    try:
        instructions = etl_db.get_all_instructions()
        return {
            "instructions": [instruction.to_dict() for instruction in instructions],
            "count": len(instructions)
        }
    except Exception as e:
        logger.error(f"Failed to get instructions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get instructions: {str(e)}")


@router.get("/instructions/{url}")
async def get_instruction_for_url(url: str):
    """
    Get instruction for specific URL
    
    Zeigt die Anweisung für eine bestimmte URL
    """
    try:
        instruction = etl_db.get_instruction_for_url(url)
        if instruction:
            return {
                "instruction": instruction.to_dict(),
                "found": True
            }
        else:
            return {
                "instruction": None,
                "found": False,
                "message": f"No instruction found for URL: {url}"
            }
    except Exception as e:
        logger.error(f"Failed to get instruction for URL {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get instruction: {str(e)}")


@router.delete("/instructions/{instruction_id}")
async def delete_instruction(instruction_id: int):
    """
    Delete URL instruction by ID
    
    Löscht eine URL-Anweisung anhand der ID
    """
    try:
        deleted = etl_db.delete_instruction(instruction_id)
        if deleted:
            return {
                "message": f"Instruction {instruction_id} deleted successfully",
                "deleted": True
            }
        else:
            raise HTTPException(status_code=404, detail=f"Instruction {instruction_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete instruction {instruction_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete instruction: {str(e)}")


@router.post("/instructions")
async def add_instruction(
    url_pattern: str,
    instructions: List[dict],
    return_format: str = "html",
    max_chars: int = None,
    description: str = ""
):
    """
    Add new URL instruction
    
    Fügt eine neue URL-Anweisung zur Datenbank hinzu
    
    **Beispiel-Request:**
    ```json
    {
        "url_pattern": "example.com",
        "instructions": [
            {"action": "click", "text": "Login"},
            {"action": "wait", "duration": 2},
            {"action": "scroll", "direction": "down", "amount": "end"}
        ],
        "return_format": "html",
        "max_chars": 500,
        "description": "Example instruction"
    }
    ```
    
    **Verfügbare Actions:**
    - `click`: Klick auf Element (`selector` oder `text`)
    - `scroll`: Scrollen (`direction`: up/down, `amount`: end/top/number)
    - `wait`: Warten (`duration` in Sekunden)
    - `wait_for_selector`: Auf Element warten (`selector`)
    - `type`: Text eingeben (`selector`, `text`)
    - `press`: Taste drücken (`key`)
    """
    try:
        instruction = URLInstruction(
            url_pattern=url_pattern,
            instructions=instructions,
            return_format=return_format,
            max_chars=max_chars,
            description=description
        )
        
        instruction_id = etl_db.add_instruction(instruction)
        
        return {
            "message": "Instruction added successfully",
            "instruction_id": instruction_id,
            "instruction": instruction.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Failed to add instruction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add instruction: {str(e)}")


# === TRANSFORM RULES MANAGEMENT ===

@router.get("/transform-rules")
async def get_all_transform_rules():
    """
    Get all transform rules from database
    
    Zeigt alle gespeicherten HTML-zu-XML Transformationsregeln
    """
    try:
        rules = etl_db.get_all_transform_rules()
        return {
            "transform_rules": [rule.to_dict() for rule in rules],
            "count": len(rules)
        }
    except Exception as e:
        logger.error(f"Failed to get transform rules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get transform rules: {str(e)}")


@router.get("/transform-rules/{rule_name}")
async def get_transform_rule(rule_name: str):
    """
    Get transform rule by name
    
    Zeigt eine spezifische Transformationsregel
    """
    try:
        rule = etl_db.get_transform_rule(rule_name)
        if rule:
            return {
                "transform_rule": rule.to_dict(),
                "found": True
            }
        else:
            return {
                "transform_rule": None,
                "found": False,
                "message": f"No transform rule found with name: {rule_name}"
            }
    except Exception as e:
        logger.error(f"Failed to get transform rule {rule_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get transform rule: {str(e)}")


@router.post("/transform-rules")
async def add_transform_rule(
    rule_name: str,
    rules: List[dict],
    output_format: str = "xml",
    description: str = ""
):
    """
    Add new transform rule
    
    Fügt eine neue HTML-zu-XML Transformationsregel zur Datenbank hinzu
    
    **Beispiel-Request:**
    ```json
    {
        "rule_name": "custom_html_to_xml",
        "rules": [
            {"action": "extract_text", "target": "body", "output": "content"},
            {"action": "wrap_xml", "root_element": "document"}
        ],
        "output_format": "xml",
        "description": "Custom HTML to XML transformation"
    }
    ```
    
    **Verfügbare Actions:**
    - `extract_text`: Text aus HTML extrahieren
    - `extract_elements`: Spezifische HTML-Elemente extrahieren
    - `clean_whitespace`: Whitespace normalisieren
    - `remove_html_tags`: HTML-Tags entfernen
    - `wrap_xml`: In XML-Struktur einbetten
    - `build_xml_tree`: XML-Baum nach Schema erstellen
    """
    try:
        transform_rule = TransformRule(
            rule_name=rule_name,
            rules=rules,
            output_format=output_format,
            description=description
        )
        
        rule_id = etl_db.add_transform_rule(transform_rule)
        
        return {
            "message": "Transform rule added successfully",
            "rule_id": rule_id,
            "transform_rule": transform_rule.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Failed to add transform rule: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add transform rule: {str(e)}")


@router.delete("/transform-rules/{rule_id}")
async def delete_transform_rule(rule_id: int):
    """
    Delete transform rule by ID
    
    Löscht eine Transformationsregel anhand der ID
    """
    try:
        deleted = etl_db.delete_transform_rule(rule_id)
        if deleted:
            return {
                "message": f"Transform rule {rule_id} deleted successfully",
                "deleted": True
            }
        else:
            raise HTTPException(status_code=404, detail=f"Transform rule {rule_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete transform rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete transform rule: {str(e)}")


# === SSH TRANSFER ROUTES MANAGEMENT ===

@router.get("/ssh-routes")
async def get_all_ssh_routes():
    """
    Get all SSH transfer routes from database
    
    Zeigt alle gespeicherten SSH-Transfer-Routen (ohne Credentials)
    """
    try:
        routes = etl_db.get_all_ssh_routes()
        return {
            "ssh_routes": [route.to_dict(include_credentials=False) for route in routes],
            "count": len(routes)
        }
    except Exception as e:
        logger.error(f"Failed to get SSH routes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get SSH routes: {str(e)}")


@router.get("/ssh-routes/{route_id}")
async def get_ssh_route(route_id: str):
    """
    Get SSH route by route_id
    
    Zeigt eine spezifische SSH-Transfer-Route
    """
    try:
        route = etl_db.get_ssh_route(route_id)
        if route:
            return {
                "ssh_route": route.to_dict(include_credentials=True),
                "found": True
            }
        else:
            return {
                "ssh_route": None,
                "found": False,
                "message": f"No SSH route found with ID: {route_id}"
            }
    except Exception as e:
        logger.error(f"Failed to get SSH route {route_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get SSH route: {str(e)}")


@router.post("/ssh-routes")
async def add_ssh_route(
    route_id: str,
    hostname: str,
    username: str,
    target_directory: str,
    port: int = 22,
    password: str = "",
    private_key: str = "",
    description: str = ""
):
    """
    Add new SSH transfer route with encrypted credentials
    
    Fügt eine neue SSH-Transfer-Route zur Datenbank hinzu
    
    **Beispiel-Request:**
    ```json
    {
        "route_id": "server_prod_01",
        "hostname": "192.168.1.100",
        "username": "transfer_user",
        "target_directory": "/home/transfer_user/uploads",
        "port": 22,
        "password": "secure_password",
        "description": "Production server for XML transfers"
    }
    ```
    
    **Sicherheit:**
    - Passwörter und Private Keys werden verschlüsselt gespeichert
    - Verwenden Sie entweder password ODER private_key für Authentifizierung
    - Private Keys sollten im OpenSSH-Format vorliegen
    """
    try:
        # Validate authentication method
        if not password and not private_key:
            raise HTTPException(
                status_code=400, 
                detail="Either password or private_key must be provided for authentication"
            )
        
        ssh_route = SSHTransferRoute(
            route_id=route_id,
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            private_key=private_key,
            target_directory=target_directory,
            description=description
        )
        
        route_db_id = etl_db.add_ssh_route(ssh_route)
        
        return {
            "message": "SSH route added successfully",
            "route_db_id": route_db_id,
            "ssh_route": ssh_route.to_dict(include_credentials=True)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add SSH route: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add SSH route: {str(e)}")


@router.delete("/ssh-routes/{route_db_id}")
async def delete_ssh_route(route_db_id: int):
    """
    Delete SSH route by database ID
    
    Löscht eine SSH-Transfer-Route anhand der Datenbank-ID
    """
    try:
        deleted = etl_db.delete_ssh_route(route_db_id)
        if deleted:
            return {
                "message": f"SSH route {route_db_id} deleted successfully",
                "deleted": True
            }
        else:
            raise HTTPException(status_code=404, detail=f"SSH route {route_db_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete SSH route {route_db_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete SSH route: {str(e)}")


@router.post("/ssh-routes/{route_id}/test")
async def test_ssh_connection(route_id: str):
    """
    Test SSH connection for a route
    
    Testet die SSH-Verbindung für eine Route ohne Datentransfer
    """
    try:
        result = await SSHTransferService.test_ssh_connection(route_id)
        return result
    except Exception as e:
        logger.error(f"Failed to test SSH connection: {e}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

"""
Initialize database with test data for stefanai.de
"""

from app.database.models import etl_db, URLInstruction, TransformRule, SSHTransferRoute
import logging

logger = logging.getLogger(__name__)


def init_stefanai_test_data():
    """Initialize test data for stefanai.de"""
    
    # Test instruction for stefanai.de
    stefanai_instruction = URLInstruction(
        url_pattern="stefanai.de",
        instructions=[
            {
                "action": "click",
                "text": "Zur KI-Sprechstunde",
                "wait_for_navigation": True
            }
        ],
        return_format="html",
        max_chars=100,
        description="Test for stefanai.de - clicks on 'Zur KI-Sprechstunde' link and returns first 100 chars of HTML"
    )
    
    try:
        instruction_id = etl_db.add_instruction(stefanai_instruction)
        logger.info(f"Added stefanai.de test instruction with ID: {instruction_id}")
        return instruction_id
    except Exception as e:
        logger.error(f"Failed to add stefanai.de test instruction: {e}")
        return None


def init_example_instructions():
    """Initialize additional example instructions"""
    
    examples = [
        URLInstruction(
            url_pattern="example.com",
            instructions=[
                {"action": "wait", "duration": 2},
                {"action": "scroll", "direction": "down", "amount": "end"},
                {"action": "wait", "duration": 1}
            ],
            return_format="text",
            max_chars=500,
            description="Example: Wait, scroll to bottom, extract text"
        ),
        URLInstruction(
            url_pattern="github.com",
            instructions=[
                {"action": "wait_for_selector", "selector": ".repository-content"},
                {"action": "click", "selector": "a[href*='README']"},
                {"action": "wait", "duration": 2}
            ],
            return_format="json",
            description="GitHub example: Click on README link"
        ),
        URLInstruction(
            url_pattern="google.com",
            instructions=[
                {"action": "wait_for_selector", "selector": "input[name='q']"},
                {"action": "type", "selector": "input[name='q']", "text": "playwright automation"},
                {"action": "press", "key": "Enter"},
                {"action": "wait", "duration": 3}
            ],
            return_format="html",
            max_chars=1000,
            description="Google search example"
        )
    ]
    
    added_ids = []
    for instruction in examples:
        try:
            instruction_id = etl_db.add_instruction(instruction)
            added_ids.append(instruction_id)
            logger.info(f"Added example instruction for {instruction.url_pattern} with ID: {instruction_id}")
        except Exception as e:
            logger.error(f"Failed to add example instruction for {instruction.url_pattern}: {e}")
    
    return added_ids


def init_transform_rules():
    """Initialize HTML-to-XML transform rules"""
    
    # Rule 1: Basic HTML cleanup and structure conversion
    basic_transform = TransformRule(
        rule_name="html_to_xml_basic",
        rules=[
            {
                "action": "extract_text",
                "target": "body",
                "output": "content"
            },
            {
                "action": "wrap_xml",
                "root_element": "document",
                "content_element": "content"
            },
            {
                "action": "remove_html_tags",
                "preserve_structure": False
            }
        ],
        output_format="xml",
        description="Basic HTML to XML conversion - extracts text content and wraps in simple XML structure"
    )
    
    # Rule 2: Structured content extraction
    structured_transform = TransformRule(
        rule_name="html_to_xml_structured",
        rules=[
            {
                "action": "extract_elements",
                "selectors": {
                    "title": "title, h1",
                    "headings": "h2, h3, h4",
                    "paragraphs": "p",
                    "links": "a[href]"
                }
            },
            {
                "action": "build_xml_tree",
                "structure": {
                    "document": {
                        "title": "title",
                        "sections": {
                            "headings": "headings",
                            "content": "paragraphs",
                            "references": "links"
                        }
                    }
                }
            }
        ],
        output_format="xml", 
        description="Structured HTML to XML - preserves document hierarchy and extracts semantic elements"
    )
    
    # Rule 3: Compressed content transformation  
    compact_transform = TransformRule(
        rule_name="html_to_xml_compact",
        rules=[
            {
                "action": "extract_text",
                "target": "body",
                "max_length": 500
            },
            {
                "action": "clean_whitespace",
                "normalize": True
            },
            {
                "action": "wrap_xml",
                "root_element": "summary",
                "add_metadata": {
                    "timestamp": "auto",
                    "length": "auto"
                }
            }
        ],
        output_format="xml",
        description="Compact HTML to XML - creates short XML summary with metadata"
    )
    
    # Rule 4: Taifun Work Order XML transformation
    taifun_transform = TransformRule(
        rule_name="html_to_taifun_xml",
        rules=[
            {
                "action": "extract_elements",
                "selectors": {
                    "problem_description": ".problem-info, .description, .meldung, .schadensbeschreibung",
                    "order_number": ".order-nr, .bestellnummer, .auftragsnummer, .referenz",
                    "technician": ".technician, .mitarbeiter, .handwerker, .zuständig",
                    "appointment_date": ".termin-datum, .date, .datum, .termin",
                    "appointment_time": ".termin-zeit, .time, .zeit, .uhrzeit",
                    "location_name": ".objekt-name, .location, .standort, .objekt",
                    "location_address": ".adresse, .address, .anschrift",
                    "contact_person": ".ansprechpartner, .contact, .kontakt, .meldender",
                    "phone": ".telefon, .phone, .tel, .handy"
                }
            },
            {
                "action": "clean_whitespace",
                "normalize": True
            },
            {
                "action": "map_to_taifun_fields",
                "field_mapping": {
                    "problem_description": ["Info", "VortextTxt"],
                    "order_number": "BestellNr",
                    "technician": "MaMatch",
                    "appointment_date": "DateTermin",
                    "appointment_time": ["TimeVon", "TimeBis"],
                    "location_name": "MtName1",
                    "location_address": ["MtAnschriftStr", "MtAnschriftPLZ", "MtAnschriftOrt"],
                    "contact_person": "contact_person",
                    "phone": "contact_phone"
                }
            },
            {
                "action": "build_taifun_xml",
                "template_type": "work_order",
                "preserve_customer_data": True
            }
        ],
        output_format="xml",
        description="Konvertiert HTML-Auftragsdaten in Taifun XML-Format für Arbeitsaufträge"
    )
    
    # Rule 5: Flexible Taifun extraction (für unbekannte Websites)
    flexible_taifun_transform = TransformRule(
        rule_name="html_to_taifun_flexible",
        rules=[
            {
                "action": "extract_text",
                "target": "body",
                "output": "full_content"
            },
            {
                "action": "extract_elements",
                "selectors": {
                    "all_headings": "h1, h2, h3, h4, h5, h6",
                    "all_paragraphs": "p",
                    "all_lists": "ul li, ol li",
                    "all_tables": "table td, table th",
                    "all_forms": "input, textarea, select",
                    "all_links": "a[href]"
                }
            },
            {
                "action": "clean_whitespace",
                "normalize": True
            },
            {
                "action": "build_taifun_xml",
                "template_type": "flexible_extraction",
                "preserve_customer_data": True
            }
        ],
        output_format="xml",
        description="Flexible HTML-Extraktion für unbekannte Websites - extrahiert alle verfügbaren Daten"
    )
    
    rules = [basic_transform, structured_transform, compact_transform, taifun_transform, flexible_taifun_transform]
    added_ids = []
    
    for rule in rules:
        try:
            rule_id = etl_db.add_transform_rule(rule)
            added_ids.append(rule_id)
            logger.info(f"Added transform rule '{rule.rule_name}' with ID: {rule_id}")
        except Exception as e:
            logger.error(f"Failed to add transform rule '{rule.rule_name}': {e}")
    
    return added_ids


def init_ssh_routes():
    """Initialize SSH transfer routes for testing"""
    
    # Test SSH route (localhost example)
    localhost_route = SSHTransferRoute(
        route_id="localhost_test",
        hostname="localhost",
        port=22,
        username="testuser",
        password="testpass123",
        target_directory="/tmp/xml_transfers",
        description="Localhost SSH route for testing XML transfers"
    )
    
    # Example production route (placeholder)
    prod_route = SSHTransferRoute(
        route_id="server_prod_01",
        hostname="192.168.1.100",
        port=22,
        username="transfer_user",
        password="secure_password_change_me",
        target_directory="/home/transfer_user/uploads",
        description="Production server for XML file transfers"
    )
    
    # Example route with private key (placeholder)
    key_route = SSHTransferRoute(
        route_id="server_key_auth",
        hostname="example.com",
        port=2222,
        username="deploy",
        private_key="""-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAEgAAAAdzc2gtcn
EXAMPLE_PRIVATE_KEY_CONTENT_PLACEHOLDER
-----END OPENSSH PRIVATE KEY-----""",
        target_directory="/var/uploads/xml",
        description="Server with private key authentication"
    )
    
    routes = [localhost_route, prod_route, key_route]
    added_ids = []
    
    for route in routes:
        try:
            route_id = etl_db.add_ssh_route(route)
            added_ids.append(route_id)
            logger.info(f"Added SSH route '{route.route_id}' with ID: {route_id}")
        except Exception as e:
            logger.error(f"Failed to add SSH route '{route.route_id}': {e}")
    
    return added_ids


def init_xml_templates():
    """Initialize XML templates with example Taifun templates"""
    from app.database.models import XMLTemplate, etl_db
    import os
    
    # Versuche die echten XML-Dateien zu laden
    templates_to_add = []
    
    # Lade die bereitgestellten XML-Dateien
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    try:
        # Leere XML laden
        empty_xml_path = os.path.join(project_root, "Test Export Aufträge leer.xml")
        if os.path.exists(empty_xml_path):
            with open(empty_xml_path, 'r', encoding='windows-1252') as f:
                real_empty_content = f.read()
            
            real_empty_template = XMLTemplate(
                template_name="taifun_empty_template",
                template_content=real_empty_content,
                template_type="taifun_work_order",
                customer_id="IMD",
                description="Leeres Taifun XML-Template vom Kunden bereitgestellt"
            )
            templates_to_add.append(real_empty_template)
        
        # Gefüllte XML als Referenz laden
        filled_xml_path = os.path.join(project_root, "Test Export Aufträge.xml")
        if os.path.exists(filled_xml_path):
            with open(filled_xml_path, 'r', encoding='windows-1252') as f:
                filled_content = f.read()
            
            filled_template = XMLTemplate(
                template_name="taifun_filled_reference",
                template_content=filled_content,
                template_type="taifun_reference",
                customer_id="IMD",
                description="Gefülltes Taifun XML als Referenz für die Feldstruktur"
            )
            templates_to_add.append(filled_template)
            
    except Exception as e:
        logger.warning(f"Could not load XML files: {e}")
    
    # Templates zur Datenbank hinzufügen
    added_ids = []
    for template in templates_to_add:
        try:
            template_id = etl_db.add_xml_template(template)
            added_ids.append(template_id)
            logger.info(f"Added XML template '{template.template_name}' with ID: {template_id}")
        except Exception as e:
            logger.error(f"Failed to add XML template '{template.template_name}': {e}")
    
    return added_ids


def initialize_all_test_data():
    """Initialize all test data"""
    logger.info("Initializing database with test data...")
    
    stefanai_id = init_stefanai_test_data()
    example_ids = init_example_instructions()
    transform_ids = init_transform_rules()
    ssh_ids = init_ssh_routes()
    xml_template_ids = init_xml_templates()
    
    all_instruction_ids = [stefanai_id] + example_ids
    all_instruction_ids = [id for id in all_instruction_ids if id is not None]
    
    all_transform_ids = [id for id in transform_ids if id is not None]
    all_ssh_ids = [id for id in ssh_ids if id is not None]
    all_xml_template_ids = [id for id in xml_template_ids if id is not None]
    
    logger.info(f"Successfully initialized {len(all_instruction_ids)} URL instructions, {len(all_transform_ids)} transform rules, {len(all_ssh_ids)} SSH routes, and {len(all_xml_template_ids)} XML templates")
    
    return {
        "url_instructions": all_instruction_ids,
        "transform_rules": all_transform_ids,
        "ssh_routes": all_ssh_ids,
        "xml_templates": all_xml_template_ids
    }


if __name__ == "__main__":
    # Run this script to initialize test data
    logging.basicConfig(level=logging.INFO)
    initialize_all_test_data()

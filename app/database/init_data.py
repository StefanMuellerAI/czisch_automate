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
    
    rules = [basic_transform, structured_transform, compact_transform]
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


def initialize_all_test_data():
    """Initialize all test data"""
    logger.info("Initializing database with test data...")
    
    stefanai_id = init_stefanai_test_data()
    example_ids = init_example_instructions()
    transform_ids = init_transform_rules()
    ssh_ids = init_ssh_routes()
    
    all_instruction_ids = [stefanai_id] + example_ids
    all_instruction_ids = [id for id in all_instruction_ids if id is not None]
    
    all_transform_ids = [id for id in transform_ids if id is not None]
    all_ssh_ids = [id for id in ssh_ids if id is not None]
    
    logger.info(f"Successfully initialized {len(all_instruction_ids)} URL instructions, {len(all_transform_ids)} transform rules, and {len(all_ssh_ids)} SSH routes")
    
    return {
        "url_instructions": all_instruction_ids,
        "transform_rules": all_transform_ids,
        "ssh_routes": all_ssh_ids
    }


if __name__ == "__main__":
    # Run this script to initialize test data
    logging.basicConfig(level=logging.INFO)
    initialize_all_test_data()

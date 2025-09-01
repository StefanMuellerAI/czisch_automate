from typing import Dict, Any, List
import xml.etree.ElementTree as ET
try:
    from bs4 import BeautifulSoup
except ImportError:
    # Fallback if BeautifulSoup is not available
    BeautifulSoup = None
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HTMLToXMLTransformService:
    """Service for transforming HTML to XML based on database rules"""
    
    @staticmethod
    def transform_html_to_xml(html_content: str, rules: List[Dict[str, Any]]) -> str:
        """Transform HTML content to XML based on provided rules"""
        
        try:
            # Check if BeautifulSoup is available
            if BeautifulSoup is None:
                raise ImportError("BeautifulSoup4 is not installed. Please install it: pip install beautifulsoup4")
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Initialize result data
            extracted_data = {}
            
            # Process each rule in sequence
            for rule in rules:
                action = rule.get("action")
                
                if action == "extract_text":
                    extracted_data = HTMLToXMLTransformService._extract_text(soup, rule, extracted_data)
                
                elif action == "extract_elements":
                    extracted_data = HTMLToXMLTransformService._extract_elements(soup, rule, extracted_data)
                
                elif action == "clean_whitespace":
                    extracted_data = HTMLToXMLTransformService._clean_whitespace(extracted_data, rule)
                
                elif action == "remove_html_tags":
                    extracted_data = HTMLToXMLTransformService._remove_html_tags(extracted_data, rule)
                
                elif action == "wrap_xml":
                    return HTMLToXMLTransformService._wrap_xml(extracted_data, rule)
                
                elif action == "build_xml_tree":
                    return HTMLToXMLTransformService._build_xml_tree(extracted_data, rule)
                
                elif action == "map_to_taifun_fields":
                    extracted_data = HTMLToXMLTransformService._map_to_taifun_fields(extracted_data, rule)
                
                elif action == "build_taifun_xml":
                    return HTMLToXMLTransformService._build_taifun_xml(extracted_data, rule)
            
            # Default XML wrapping if no explicit wrap action
            return HTMLToXMLTransformService._default_xml_wrap(extracted_data)
            
        except Exception as e:
            logger.error(f"HTML to XML transformation error: {e}")
            # Return error XML
            return f'<error><message>Transformation failed: {str(e)}</message></error>'
    
    @staticmethod
    def _extract_text(soup: Any, rule: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text content from HTML"""
        target = rule.get("target", "body")
        output_key = rule.get("output", "content")
        max_length = rule.get("max_length")
        
        if target == "body":
            text = soup.get_text(strip=True)
        else:
            element = soup.find(target)
            text = element.get_text(strip=True) if element else ""
        
        if max_length and len(text) > max_length:
            text = text[:max_length] + "..."
        
        data[output_key] = text
        return data
    
    @staticmethod
    def _extract_elements(soup: Any, rule: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract specific HTML elements based on selectors"""
        selectors = rule.get("selectors", {})
        
        for key, selector in selectors.items():
            elements = soup.select(selector)
            
            if key == "links":
                # Special handling for links
                data[key] = [
                    {
                        "text": elem.get_text(strip=True),
                        "href": elem.get("href", "")
                    }
                    for elem in elements[:10]  # Limit to first 10
                ]
            else:
                # Extract text content
                data[key] = [elem.get_text(strip=True) for elem in elements[:20]]  # Limit to first 20
        
        return data
    
    @staticmethod
    def _clean_whitespace(data: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Clean whitespace from text content"""
        normalize = rule.get("normalize", True)
        
        def clean_text(text):
            if isinstance(text, str):
                if normalize:
                    # Normalize whitespace
                    return re.sub(r'\s+', ' ', text.strip())
                else:
                    return text.strip()
            return text
        
        def clean_recursive(obj):
            if isinstance(obj, dict):
                return {k: clean_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_recursive(item) for item in obj]
            else:
                return clean_text(obj)
        
        return clean_recursive(data)
    
    @staticmethod
    def _remove_html_tags(data: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Remove HTML tags from content"""
        preserve_structure = rule.get("preserve_structure", False)
        
        def remove_tags(text):
            if isinstance(text, str):
                if preserve_structure:
                    # Replace some tags with newlines
                    text = re.sub(r'</(p|div|br)>', '\n', text)
                # Remove all HTML tags
                return re.sub(r'<[^>]+>', '', text)
            return text
        
        def process_recursive(obj):
            if isinstance(obj, dict):
                return {k: process_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [process_recursive(item) for item in obj]
            else:
                return remove_tags(obj)
        
        return process_recursive(data)
    
    @staticmethod
    def _wrap_xml(data: Dict[str, Any], rule: Dict[str, Any]) -> str:
        """Wrap data in XML structure"""
        root_element = rule.get("root_element", "document")
        content_element = rule.get("content_element", "content")
        add_metadata = rule.get("add_metadata", {})
        
        # Create root element
        root = ET.Element(root_element)
        
        # Add metadata if specified
        if add_metadata:
            metadata_elem = ET.SubElement(root, "metadata")
            for key, value in add_metadata.items():
                if value == "auto":
                    if key == "timestamp":
                        value = datetime.now().isoformat()
                    elif key == "length":
                        content = data.get("content", "")
                        value = str(len(str(content)))
                
                meta_elem = ET.SubElement(metadata_elem, key)
                meta_elem.text = str(value)
        
        # Add content
        if isinstance(data, dict) and len(data) == 1 and content_element in data:
            # Simple content wrapping
            content_elem = ET.SubElement(root, content_element)
            content_elem.text = str(data[content_element])
        else:
            # Add all data elements
            HTMLToXMLTransformService._dict_to_xml(data, root)
        
        # Convert to string
        return HTMLToXMLTransformService._xml_to_string(root)
    
    @staticmethod
    def _build_xml_tree(data: Dict[str, Any], rule: Dict[str, Any]) -> str:
        """Build XML tree based on structure definition"""
        structure = rule.get("structure", {})
        
        def build_recursive(struct, data_source, parent):
            for key, value in struct.items():
                elem = ET.SubElement(parent, key)
                
                if isinstance(value, dict):
                    # Nested structure
                    build_recursive(value, data_source, elem)
                elif isinstance(value, str):
                    # Reference to data
                    if value in data_source:
                        content = data_source[value]
                        if isinstance(content, list):
                            for item in content:
                                item_elem = ET.SubElement(elem, "item")
                                if isinstance(item, dict):
                                    HTMLToXMLTransformService._dict_to_xml(item, item_elem)
                                else:
                                    item_elem.text = str(item)
                        else:
                            elem.text = str(content)
        
        # Find root element
        root_key = list(structure.keys())[0]
        root = ET.Element(root_key)
        
        if isinstance(structure[root_key], dict):
            build_recursive(structure[root_key], data, root)
        
        return HTMLToXMLTransformService._xml_to_string(root)
    
    @staticmethod
    def _default_xml_wrap(data: Dict[str, Any]) -> str:
        """Default XML wrapping for data"""
        root = ET.Element("document")
        HTMLToXMLTransformService._dict_to_xml(data, root)
        return HTMLToXMLTransformService._xml_to_string(root)
    
    @staticmethod
    def _dict_to_xml(data: Dict[str, Any], parent: ET.Element):
        """Convert dictionary to XML elements"""
        for key, value in data.items():
            # Sanitize key name for XML
            safe_key = re.sub(r'[^a-zA-Z0-9_-]', '_', str(key))
            elem = ET.SubElement(parent, safe_key)
            
            if isinstance(value, dict):
                HTMLToXMLTransformService._dict_to_xml(value, elem)
            elif isinstance(value, list):
                for item in value:
                    item_elem = ET.SubElement(elem, "item")
                    if isinstance(item, dict):
                        HTMLToXMLTransformService._dict_to_xml(item, item_elem)
                    else:
                        item_elem.text = str(item)
            else:
                elem.text = str(value)
    
    @staticmethod
    def _xml_to_string(element: ET.Element) -> str:
        """Convert XML element to formatted string"""
        # Create string representation
        rough_string = ET.tostring(element, encoding='unicode')
        
        # Basic formatting (add newlines)
        formatted = rough_string.replace('><', '>\n<')
        
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{formatted}'
    
    @staticmethod
    def _map_to_taifun_fields(data: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Mappt extrahierte HTML-Daten auf Taifun XML-Felder"""
        field_mapping = rule.get("field_mapping", {})
        mapped_data = {}
        
        for source_field, target_fields in field_mapping.items():
            if source_field in data and data[source_field]:
                source_value = data[source_field]
                
                # Behandle verschiedene Target-Field-Typen
                if isinstance(target_fields, str):
                    # Einzelnes Zielfeld
                    mapped_data[target_fields] = source_value
                elif isinstance(target_fields, list):
                    # Mehrere Zielfelder (z.B. für Adressdaten)
                    if source_field in ['location_address', 'address']:
                        # Spezielle Behandlung für Adressen
                        HTMLToXMLTransformService._parse_address_to_fields(
                            source_value, target_fields, mapped_data
                        )
                    elif source_field in ['appointment_time', 'time_range']:
                        # Spezielle Behandlung für Zeitspannen
                        HTMLToXMLTransformService._parse_time_range_to_fields(
                            source_value, target_fields, mapped_data
                        )
                    else:
                        # Standard: Wert in alle Zielfelder kopieren
                        for target_field in target_fields:
                            mapped_data[target_field] = source_value
        
        # Originaldaten beibehalten, die nicht gemappt wurden
        for key, value in data.items():
            if key not in field_mapping:
                mapped_data[key] = value
        
        logger.info(f"Mapped {len(field_mapping)} fields for Taifun XML")
        return mapped_data
    
    @staticmethod
    def _parse_address_to_fields(address: str, target_fields: List[str], mapped_data: Dict[str, Any]):
        """Parst eine Adresszeile in separate Felder"""
        # Einfaches Parsing - kann später verfeinert werden
        address_parts = address.strip().split(',')
        
        if len(address_parts) >= 1 and 'MtAnschriftStr' in target_fields:
            mapped_data['MtAnschriftStr'] = address_parts[0].strip()
        
        if len(address_parts) >= 2:
            # Versuche PLZ und Ort zu extrahieren
            plz_ort = address_parts[-1].strip()
            plz_match = re.match(r'(\d{5})\s+(.+)', plz_ort)
            if plz_match:
                if 'MtAnschriftPLZ' in target_fields:
                    mapped_data['MtAnschriftPLZ'] = plz_match.group(1)
                if 'MtAnschriftOrt' in target_fields:
                    mapped_data['MtAnschriftOrt'] = plz_match.group(2)
    
    @staticmethod
    def _parse_time_range_to_fields(time_range: str, target_fields: List[str], mapped_data: Dict[str, Any]):
        """Parst eine Zeitspanne in Von/Bis-Felder"""
        # Beispiele: "13:00-15:00", "13:00 bis 15:00", "von 13:00 bis 15:00"
        time_pattern = r'(\d{1,2}:\d{2}).*?(\d{1,2}:\d{2})'
        match = re.search(time_pattern, time_range)
        
        if match:
            if 'TimeVon' in target_fields:
                mapped_data['TimeVon'] = f"{match.group(1)}:00"
            if 'TimeBis' in target_fields:
                mapped_data['TimeBis'] = f"{match.group(2)}:00"
        else:
            # Fallback: gesamten String als TimeVon verwenden
            if 'TimeVon' in target_fields:
                mapped_data['TimeVon'] = time_range
    
    @staticmethod
    def _build_taifun_xml(data: Dict[str, Any], rule: Dict[str, Any]) -> str:
        """Erstellt Taifun XML aus gemappten Daten"""
        template_type = rule.get("template_type", "work_order")
        preserve_customer_data = rule.get("preserve_customer_data", True)
        
        # Für jetzt geben wir die Daten als strukturiertes XML zurück
        # Das kann später mit dem XMLTemplateService kombiniert werden
        root = ET.Element("TaifunData")
        root.set("type", template_type)
        
        # Auftragsdaten
        work_order = ET.SubElement(root, "WorkOrder")
        
        # Wichtige Felder für Taifun
        taifun_fields = {
            'Info': data.get('problem_description', ''),
            'VortextTxt': data.get('detailed_description', data.get('problem_description', '')),
            'BestellNr': data.get('order_number', ''),
            'DateTermin': data.get('appointment_date', ''),
            'TimeVon': data.get('appointment_time_from', ''),
            'TimeBis': data.get('appointment_time_to', ''),
            'MtName1': data.get('location_name', ''),
            'MtAnschriftStr': data.get('location_street', ''),
            'MtAnschriftPLZ': data.get('location_zip', ''),
            'MtAnschriftOrt': data.get('location_city', ''),
            'MaMatch': data.get('technician', ''),
        }
        
        for field_name, value in taifun_fields.items():
            if value:  # Nur nicht-leere Werte hinzufügen
                field_elem = ET.SubElement(work_order, field_name)
                field_elem.text = str(value)
        
        # Kontaktdaten falls vorhanden
        if data.get('contact_person') or data.get('contact_phone'):
            contact_info = []
            if data.get('contact_person'):
                contact_info.append(f"Meldender: {data['contact_person']}")
            if data.get('contact_phone'):
                contact_info.append(f"Telefon: {data['contact_phone']}")
            
            # Zu VortextTxt hinzufügen
            current_vortext = taifun_fields.get('VortextTxt', '')
            enhanced_vortext = current_vortext + '\n' + '\n'.join(contact_info)
            
            vortext_elem = work_order.find('VortextTxt')
            if vortext_elem is not None:
                vortext_elem.text = enhanced_vortext
            else:
                vortext_elem = ET.SubElement(work_order, 'VortextTxt')
                vortext_elem.text = enhanced_vortext
        
        # Zusätzliche extrahierte Daten
        if len(data) > len(taifun_fields):
            additional = ET.SubElement(root, "AdditionalData")
            for key, value in data.items():
                if key not in ['problem_description', 'detailed_description', 'order_number', 
                              'appointment_date', 'appointment_time_from', 'appointment_time_to',
                              'location_name', 'location_street', 'location_zip', 'location_city',
                              'technician', 'contact_person', 'contact_phone']:
                    elem = ET.SubElement(additional, key.replace(' ', '_'))
                    elem.text = str(value)
        
        return HTMLToXMLTransformService._xml_to_string(root)

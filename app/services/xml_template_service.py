from typing import Dict, Any, Optional
import xml.etree.ElementTree as ET
from xml.dom import minidom
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class XMLTemplateService:
    """Service für die Verarbeitung von Taifun XML-Templates"""
    
    @staticmethod
    def load_template_from_file(template_path: str) -> str:
        """Lädt XML-Template aus Datei"""
        try:
            with open(template_path, 'r', encoding='windows-1252') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Failed to load template from {template_path}: {e}")
            raise
    
    @staticmethod
    def populate_work_order_template(
        empty_template: str, 
        extracted_data: Dict[str, Any],
        work_order_nr: Optional[str] = None
    ) -> str:
        """
        Füllt das leere Taifun XML-Template mit extrahierten Auftragsdaten
        
        Args:
            empty_template: Das leere XML-Template
            extracted_data: Die extrahierten Daten aus der Website
            work_order_nr: Optional - spezifische Auftragsnummer
        """
        try:
            # XML parsen
            root = ET.fromstring(empty_template)
            
            # Namespace definieren
            namespace = {'taifun': 'urn:taifun-software.de:schema:TAIFUN'}
            
            # Ah Element finden (Auftrag)
            ah_element = root.find('.//taifun:Ah', namespace)
            if ah_element is None:
                ah_element = root.find('.//Ah')  # Fallback ohne namespace
            
            if ah_element is None:
                raise ValueError("Kein Ah (Auftrag) Element im Template gefunden")
            
            # Aktuelle Zeit für Timestamps
            now = datetime.now()
            current_date = now.strftime('%Y-%m-%d')
            current_time = now.strftime('%H:%M:%S.%f')[:-4]
            
            # Basis-Auftragsdaten setzen
            XMLTemplateService._set_element_text(ah_element, 'DateAdd', current_date)
            XMLTemplateService._set_element_text(ah_element, 'TimeAdd', current_time)
            XMLTemplateService._set_element_text(ah_element, 'DatePut', current_date)
            XMLTemplateService._set_element_text(ah_element, 'TimePut', current_time)
            XMLTemplateService._set_element_text(ah_element, 'Date', current_date)
            XMLTemplateService._set_element_text(ah_element, 'DateDesc', current_date)
            XMLTemplateService._set_element_text(ah_element, 'Time', now.strftime('%H:%M:00'))
            
            # Auftragsnummer generieren falls nicht gegeben
            if not work_order_nr:
                work_order_nr = f"A{now.strftime('%y%m%d')}{now.strftime('%H%M')}"
            
            XMLTemplateService._set_element_text(ah_element, 'Nr', work_order_nr)
            XMLTemplateService._set_element_text(ah_element, 'NrDesc', work_order_nr)
            
            # Extrahierte Daten einsetzen
            XMLTemplateService._populate_extracted_data(ah_element, extracted_data)
            
            # XML formatieren und zurückgeben
            return XMLTemplateService._format_xml(root)
            
        except Exception as e:
            logger.error(f"Failed to populate template: {e}")
            raise
    
    @staticmethod
    def _populate_extracted_data(ah_element: ET.Element, data: Dict[str, Any]):
        """Setzt die extrahierten Daten in das XML ein"""
        
        # Problem-Beschreibung
        if 'problem_description' in data:
            XMLTemplateService._set_element_text(ah_element, 'Info', data['problem_description'])
        
        # Detaillierte Beschreibung
        if 'detailed_description' in data:
            XMLTemplateService._set_element_text(ah_element, 'VortextTxt', data['detailed_description'])
        elif 'problem_description' in data:
            # Fallback: verwende Kurzbeschreibung auch für Details
            XMLTemplateService._set_element_text(ah_element, 'VortextTxt', data['problem_description'])
        
        # Bestellnummer
        if 'order_number' in data:
            XMLTemplateService._set_element_text(ah_element, 'BestellNr', str(data['order_number']))
        
        # Terminplanung
        if 'appointment_date' in data:
            XMLTemplateService._set_element_text(ah_element, 'DateTermin', data['appointment_date'])
            XMLTemplateService._set_element_text(ah_element, 'Date2', data['appointment_date'])
        
        if 'appointment_time_from' in data:
            XMLTemplateService._set_element_text(ah_element, 'TimeVon', data['appointment_time_from'])
        
        if 'appointment_time_to' in data:
            XMLTemplateService._set_element_text(ah_element, 'TimeBis', data['appointment_time_to'])
        
        # Objekt/Standort-Informationen
        if 'location_name' in data:
            XMLTemplateService._set_element_text(ah_element, 'MtName1', data['location_name'])
        
        if 'location_street' in data:
            XMLTemplateService._set_element_text(ah_element, 'MtAnschriftStr', data['location_street'])
            XMLTemplateService._set_element_text(ah_element, 'MtStr', data['location_street'])
        
        if 'location_zip' in data:
            XMLTemplateService._set_element_text(ah_element, 'MtAnschriftPLZ', data['location_zip'])
        
        if 'location_city' in data:
            XMLTemplateService._set_element_text(ah_element, 'MtAnschriftOrt', data['location_city'])
            # Kombiniere PLZ und Stadt für MtOrt
            zip_code = data.get('location_zip', '')
            XMLTemplateService._set_element_text(ah_element, 'MtOrt', f"{zip_code} {data['location_city']}".strip())
        
        # Techniker/Mitarbeiter
        if 'technician' in data:
            XMLTemplateService._set_element_text(ah_element, 'MaMatch', data['technician'])
        
        # Kontaktinformationen
        if 'contact_person' in data:
            # Füge Kontaktperson zur VortextTxt hinzu
            current_text = XMLTemplateService._get_element_text(ah_element, 'VortextTxt') or ''
            contact_info = f"\nMeldender: {data['contact_person']}"
            if 'contact_phone' in data:
                contact_info += f"\nTelefon: {data['contact_phone']}"
            XMLTemplateService._set_element_text(ah_element, 'VortextTxt', current_text + contact_info)
        
        # Status-Flags setzen
        XMLTemplateService._set_element_text(ah_element, 'AhOffen', 'true')
        XMLTemplateService._set_element_text(ah_element, 'Erledigt', 'false')
        XMLTemplateService._set_element_text(ah_element, 'AhMobile', 'true')
    
    @staticmethod
    def _set_element_text(parent: ET.Element, tag_name: str, value: str):
        """Setzt den Text eines XML-Elements"""
        element = parent.find(tag_name)
        if element is not None:
            element.text = str(value) if value is not None else ''
        else:
            # Element erstellen falls es nicht existiert
            new_element = ET.SubElement(parent, tag_name)
            new_element.text = str(value) if value is not None else ''
    
    @staticmethod
    def _get_element_text(parent: ET.Element, tag_name: str) -> Optional[str]:
        """Holt den Text eines XML-Elements"""
        element = parent.find(tag_name)
        return element.text if element is not None else None
    
    @staticmethod
    def _format_xml(root: ET.Element) -> str:
        """Formatiert XML für bessere Lesbarkeit"""
        try:
            # XML zu String konvertieren
            rough_string = ET.tostring(root, encoding='unicode')
            
            # Mit minidom formatieren
            reparsed = minidom.parseString(rough_string)
            formatted = reparsed.toprettyxml(indent="  ", encoding=None)
            
            # Erste Zeile (XML-Deklaration) entfernen und durch windows-1252 ersetzen
            lines = formatted.split('\n')[1:]  # Erste Zeile entfernen
            formatted_content = '\n'.join(lines)
            
            # Korrekte XML-Deklaration hinzufügen
            xml_declaration = '<?xml version="1.0" encoding="windows-1252"?>'
            
            return xml_declaration + formatted_content
            
        except Exception as e:
            logger.warning(f"XML formatting failed, returning unformatted: {e}")
            return ET.tostring(root, encoding='unicode')
    
    @staticmethod
    def validate_taifun_xml(xml_content: str) -> Dict[str, Any]:
        """
        Validiert Taifun XML-Struktur
        
        Returns:
            Dict mit validation_result und ggf. Fehlermeldungen
        """
        try:
            root = ET.fromstring(xml_content)
            
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            # Prüfe Root-Element
            if root.tag != 'AhList':
                validation_result['errors'].append("Root-Element sollte 'AhList' sein")
                validation_result['valid'] = False
            
            # Prüfe Namespace
            if 'urn:taifun-software.de:schema:TAIFUN' not in xml_content:
                validation_result['warnings'].append("Taifun-Namespace fehlt")
            
            # Prüfe Ah-Element
            ah_element = root.find('.//Ah')
            if ah_element is None:
                validation_result['errors'].append("Kein Ah (Auftrag) Element gefunden")
                validation_result['valid'] = False
            else:
                # Prüfe wichtige Felder
                required_fields = ['Nr', 'Date', 'Info']
                for field in required_fields:
                    if ah_element.find(field) is None:
                        validation_result['warnings'].append(f"Feld '{field}' fehlt")
            
            return validation_result
            
        except ET.ParseError as e:
            return {
                'valid': False,
                'errors': [f"XML Parse Error: {e}"],
                'warnings': []
            }
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Validation Error: {e}"],
                'warnings': []
            }

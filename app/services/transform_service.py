from typing import Any, Dict, Optional
import json
import re
from datetime import datetime
import logging
from app.database.models import etl_db
from app.services.html_transform_service import HTMLToXMLTransformService

logger = logging.getLogger(__name__)


class TransformService:
    """Service for data transformation operations"""
    
    @staticmethod
    def transform_data(data: Any, rules: Optional[Dict[str, Any]] = None) -> Any:
        """Transform data based on provided rules or database rule sets"""
        
        # Check for HTML-to-XML transformation with rule_name
        if rules and rules.get("rule_name"):
            rule_name = rules["rule_name"]
            return TransformService._transform_with_database_rule(data, rule_name)
        
        # Fallback to legacy transformation rules
        if not rules:
            return data
        
        transformed_data = data
        
        try:
            # String transformations
            if isinstance(transformed_data, str):
                transformed_data = TransformService._apply_string_transformations(
                    transformed_data, rules
                )
            
            # Numeric transformations
            elif isinstance(transformed_data, (int, float)):
                transformed_data = TransformService._apply_numeric_transformations(
                    transformed_data, rules
                )
            
            # Dictionary transformations
            elif isinstance(transformed_data, dict):
                transformed_data = TransformService._apply_dict_transformations(
                    transformed_data, rules
                )
            
            # List transformations
            elif isinstance(transformed_data, list):
                transformed_data = TransformService._apply_list_transformations(
                    transformed_data, rules
                )
            
            # Apply general transformations
            transformed_data = TransformService._apply_general_transformations(
                transformed_data, rules
            )
            
            logger.info("Data transformation completed successfully")
            return transformed_data
            
        except Exception as e:
            logger.error(f"Transform error: {e}")
            raise
    
    @staticmethod
    def _transform_with_database_rule(data: Any, rule_name: str) -> str:
        """Transform data using database-stored transformation rules"""
        try:
            # Get transformation rule from database
            transform_rule = etl_db.get_transform_rule(rule_name)
            
            if not transform_rule:
                raise ValueError(f"Transform rule '{rule_name}' not found in database")
            
            logger.info(f"Applying database rule '{rule_name}': {transform_rule.description}")
            
            # Handle HTML input
            if isinstance(data, str):
                # Assume string input is HTML
                html_content = data
            elif isinstance(data, dict) and "html" in data:
                # Extract HTML from dict
                html_content = data["html"]
            else:
                # Convert other data types to string and treat as HTML
                html_content = str(data)
            
            # Apply HTML-to-XML transformation
            xml_result = HTMLToXMLTransformService.transform_html_to_xml(
                html_content, transform_rule.rules
            )
            
            logger.info(f"Successfully transformed data using rule '{rule_name}'")
            return xml_result
            
        except Exception as e:
            logger.error(f"Database rule transformation error: {e}")
            raise
    
    @staticmethod
    def _apply_string_transformations(data: str, rules: Dict[str, Any]) -> str:
        """Apply string-specific transformations"""
        result = data
        
        # Case transformations
        if rules.get("uppercase"):
            result = result.upper()
        elif rules.get("lowercase"):
            result = result.lower()
        elif rules.get("title_case"):
            result = result.title()
        elif rules.get("capitalize"):
            result = result.capitalize()
        
        # String operations
        if rules.get("strip"):
            result = result.strip()
        
        if rules.get("replace"):
            replace_config = rules["replace"]
            if isinstance(replace_config, dict):
                old = replace_config.get("old", "")
                new = replace_config.get("new", "")
                result = result.replace(old, new)
        
        # Regex operations
        if rules.get("regex_replace"):
            regex_config = rules["regex_replace"]
            if isinstance(regex_config, dict):
                pattern = regex_config.get("pattern", "")
                replacement = regex_config.get("replacement", "")
                result = re.sub(pattern, replacement, result)
        
        # Add prefix/suffix
        if rules.get("prefix"):
            result = rules["prefix"] + result
        if rules.get("suffix"):
            result = result + rules["suffix"]
        
        return result
    
    @staticmethod
    def _apply_numeric_transformations(data: float, rules: Dict[str, Any]) -> float:
        """Apply numeric transformations"""
        result = data
        
        # Arithmetic operations
        if rules.get("multiply"):
            multiplier = rules.get("multiply_by", 1)
            result = result * multiplier
        
        if rules.get("add"):
            addend = rules.get("add_value", 0)
            result = result + addend
        
        if rules.get("subtract"):
            subtrahend = rules.get("subtract_value", 0)
            result = result - subtrahend
        
        if rules.get("divide"):
            divisor = rules.get("divide_by", 1)
            if divisor != 0:
                result = result / divisor
        
        # Rounding
        if rules.get("round"):
            decimal_places = rules.get("decimal_places", 0)
            result = round(result, decimal_places)
        
        # Absolute value
        if rules.get("absolute"):
            result = abs(result)
        
        return result
    
    @staticmethod
    def _apply_dict_transformations(data: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
        """Apply dictionary-specific transformations"""
        result = data.copy()
        
        # Filter keys
        if rules.get("filter_keys"):
            allowed_keys = rules.get("allowed_keys", [])
            if allowed_keys:
                result = {k: v for k, v in result.items() if k in allowed_keys}
        
        # Exclude keys
        if rules.get("exclude_keys"):
            excluded_keys = rules.get("excluded_keys", [])
            if excluded_keys:
                result = {k: v for k, v in result.items() if k not in excluded_keys}
        
        # Rename keys
        if rules.get("rename_keys"):
            rename_mapping = rules.get("key_mapping", {})
            if rename_mapping:
                for old_key, new_key in rename_mapping.items():
                    if old_key in result:
                        result[new_key] = result.pop(old_key)
        
        # Add computed fields
        if rules.get("add_timestamp"):
            result["timestamp"] = datetime.now().isoformat()
        
        # Flatten nested dictionaries
        if rules.get("flatten"):
            result = TransformService._flatten_dict(result)
        
        return result
    
    @staticmethod
    def _apply_list_transformations(data: list, rules: Dict[str, Any]) -> list:
        """Apply list-specific transformations"""
        result = data.copy()
        
        # Sort list
        if rules.get("sort"):
            reverse = rules.get("sort_reverse", False)
            try:
                result = sorted(result, reverse=reverse)
            except TypeError:
                logger.warning("Cannot sort list with mixed types")
        
        # Limit list size
        if rules.get("limit"):
            limit_size = rules.get("limit_size", len(result))
            result = result[:limit_size]
        
        # Remove duplicates
        if rules.get("unique"):
            # Preserve order while removing duplicates
            seen = set()
            result = [x for x in result if not (x in seen or seen.add(x))]
        
        # Filter list items
        if rules.get("filter_values"):
            allowed_values = rules.get("allowed_values", [])
            if allowed_values:
                result = [item for item in result if item in allowed_values]
        
        return result
    
    @staticmethod
    def _apply_general_transformations(data: Any, rules: Dict[str, Any]) -> Any:
        """Apply transformations that work on any data type"""
        result = data
        
        # Convert to JSON string
        if rules.get("to_json"):
            try:
                result = json.dumps(result, default=str)
            except TypeError as e:
                logger.warning(f"Cannot convert to JSON: {e}")
        
        # Parse from JSON string
        if rules.get("from_json") and isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError as e:
                logger.warning(f"Cannot parse JSON: {e}")
        
        return result
    
    @staticmethod
    def _flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:
        """Flatten a nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(TransformService._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

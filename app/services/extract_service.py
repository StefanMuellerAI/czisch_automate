from typing import Any, Dict, Optional
import json
import logging
import asyncio
from urllib.parse import urlparse
from app.services.playwright_service import playwright_service
from app.database.models import etl_db, URLInstruction

logger = logging.getLogger(__name__)


class ExtractService:
    """Service for data extraction operations"""
    
    @staticmethod
    async def extract_data(
        source_url: Optional[str] = None,
        source_data: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extract data from various sources with intelligent URL handling"""
        
        try:
            # Extract from URL using Playwright with database instructions
            if source_url:
                if not playwright_service.is_available():
                    raise RuntimeError("Playwright browser not available")
                
                # Check for URL-specific instructions in database
                url_instruction = etl_db.get_instruction_for_url(source_url)
                
                if url_instruction:
                    logger.info(f"Found database instructions for URL: {source_url}")
                    extracted_data = await ExtractService._execute_url_instructions(
                        source_url, url_instruction
                    )
                else:
                    logger.info(f"No database instructions found, using standard extraction for: {source_url}")
                    extracted_data = await playwright_service.extract_from_url(source_url, config)
                
                source = source_url
                
            # Extract from provided data
            elif source_data is not None:
                extracted_data = ExtractService._extract_from_data(source_data, config)
                source = "provided_data"
                
            else:
                raise ValueError("Either source_url or source_data must be provided")
            
            logger.info(f"Data extracted successfully from {source}")
            
            return {
                "extracted_data": extracted_data,
                "source": source,
                "extraction_config": config,
                "used_database_instructions": url_instruction is not None if source_url else False
            }
            
        except Exception as e:
            logger.error(f"Extract error: {e}")
            raise
    
    @staticmethod
    async def _execute_url_instructions(url: str, instruction: URLInstruction) -> Dict[str, Any]:
        """Execute URL-specific instructions using Playwright"""
        if not playwright_service.is_available():
            raise RuntimeError("Playwright browser not available")
        
        page = await playwright_service.browser.new_page()
        
        try:
            # Navigate to the URL
            logger.info(f"Navigating to: {url}")
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("networkidle")
            
            # Execute each instruction step
            for i, step in enumerate(instruction.instructions):
                action = step.get("action")
                
                logger.info(f"Executing step {i+1}: {action}")
                
                if action == "click":
                    selector = step.get("selector")
                    text = step.get("text")
                    
                    if selector:
                        await page.click(selector)
                    elif text:
                        # Click on element containing specific text
                        await page.click(f"text={text}")
                    
                    # Wait for navigation if specified
                    if step.get("wait_for_navigation", True):
                        await page.wait_for_load_state("networkidle")
                
                elif action == "scroll":
                    direction = step.get("direction", "down")
                    amount = step.get("amount", "end")
                    
                    if direction == "down":
                        if amount == "end":
                            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        else:
                            await page.evaluate(f"window.scrollBy(0, {amount})")
                    elif direction == "up":
                        if amount == "top":
                            await page.evaluate("window.scrollTo(0, 0)")
                        else:
                            await page.evaluate(f"window.scrollBy(0, -{amount})")
                    
                    # Wait a bit for content to load
                    await asyncio.sleep(1)
                
                elif action == "wait":
                    duration = step.get("duration", 1)
                    await asyncio.sleep(duration)
                
                elif action == "wait_for_selector":
                    selector = step.get("selector")
                    timeout = step.get("timeout", 5000)
                    await page.wait_for_selector(selector, timeout=timeout)
                
                elif action == "type":
                    selector = step.get("selector")
                    text = step.get("text", "")
                    await page.fill(selector, text)
                
                elif action == "press":
                    key = step.get("key", "Enter")
                    await page.press("body", key)
            
            # Extract the final result based on return format
            result = {}
            
            if instruction.return_format == "html":
                html_content = await page.content()
                if instruction.max_chars:
                    html_content = html_content[:instruction.max_chars]
                result["html"] = html_content
                result["content_type"] = "html"
            
            elif instruction.return_format == "text":
                text_content = await page.inner_text("body")
                if instruction.max_chars:
                    text_content = text_content[:instruction.max_chars]
                result["text"] = text_content
                result["content_type"] = "text"
            
            elif instruction.return_format == "json":
                # Extract structured data
                title = await page.title()
                text_content = await page.inner_text("body")
                if instruction.max_chars:
                    text_content = text_content[:instruction.max_chars]
                
                result = {
                    "title": title,
                    "text": text_content,
                    "url": page.url,
                    "content_type": "json"
                }
            
            # Add metadata
            result.update({
                "final_url": page.url,
                "instruction_id": instruction.id,
                "instruction_description": instruction.description,
                "steps_executed": len(instruction.instructions)
            })
            
            logger.info(f"Successfully executed {len(instruction.instructions)} instruction steps")
            return result
            
        finally:
            await page.close()
    
    @staticmethod
    def _extract_from_data(data: Any, config: Optional[Dict[str, Any]] = None) -> Any:
        """Extract data from provided data structure"""
        result = data
        
        if not config:
            return result
        
        try:
            # Extract specific keys from dictionary
            if isinstance(data, dict) and config.get("extract_keys"):
                keys_to_extract = config["extract_keys"]
                if isinstance(keys_to_extract, list):
                    result = {k: data.get(k) for k in keys_to_extract if k in data}
            
            # Extract nested values using dot notation
            elif isinstance(data, dict) and config.get("extract_paths"):
                paths = config["extract_paths"]
                result = {}
                for path_name, path in paths.items():
                    value = ExtractService._get_nested_value(data, path)
                    if value is not None:
                        result[path_name] = value
            
            # Extract from list using indices or filters
            elif isinstance(data, list) and config.get("extract_list"):
                list_config = config["extract_list"]
                
                # Extract by indices
                if "indices" in list_config:
                    indices = list_config["indices"]
                    result = [data[i] for i in indices if 0 <= i < len(data)]
                
                # Extract first N items
                elif "first" in list_config:
                    n = list_config["first"]
                    result = data[:n]
                
                # Extract last N items
                elif "last" in list_config:
                    n = list_config["last"]
                    result = data[-n:]
                
                # Filter items by condition
                elif "filter" in list_config:
                    filter_config = list_config["filter"]
                    result = ExtractService._filter_list(data, filter_config)
            
            # Extract using JSONPath-like syntax
            elif config.get("json_path"):
                json_path = config["json_path"]
                result = ExtractService._extract_json_path(data, json_path)
            
            # Extract using regex patterns (for strings)
            elif isinstance(data, str) and config.get("regex_patterns"):
                patterns = config["regex_patterns"]
                result = ExtractService._extract_regex_patterns(data, patterns)
            
            return result
            
        except Exception as e:
            logger.error(f"Data extraction error: {e}")
            return data
    
    @staticmethod
    def _get_nested_value(data: dict, path: str, delimiter: str = ".") -> Any:
        """Get nested value from dictionary using dot notation"""
        keys = path.split(delimiter)
        current = data
        
        try:
            for key in keys:
                if isinstance(current, dict):
                    current = current[key]
                elif isinstance(current, list) and key.isdigit():
                    index = int(key)
                    current = current[index]
                else:
                    return None
            return current
        except (KeyError, IndexError, TypeError):
            return None
    
    @staticmethod
    def _filter_list(data: list, filter_config: Dict[str, Any]) -> list:
        """Filter list items based on configuration"""
        if not isinstance(filter_config, dict):
            return data
        
        result = []
        
        for item in data:
            include_item = True
            
            # Filter by field value
            if "field_equals" in filter_config:
                field_name = filter_config["field_equals"]["field"]
                expected_value = filter_config["field_equals"]["value"]
                
                if isinstance(item, dict):
                    actual_value = item.get(field_name)
                    if actual_value != expected_value:
                        include_item = False
            
            # Filter by field existence
            if "has_field" in filter_config:
                field_name = filter_config["has_field"]
                if isinstance(item, dict) and field_name not in item:
                    include_item = False
            
            # Filter by value type
            if "value_type" in filter_config:
                expected_type = filter_config["value_type"]
                type_mapping = {
                    "string": str,
                    "number": (int, float),
                    "integer": int,
                    "float": float,
                    "boolean": bool,
                    "dict": dict,
                    "list": list
                }
                if expected_type in type_mapping:
                    if not isinstance(item, type_mapping[expected_type]):
                        include_item = False
            
            if include_item:
                result.append(item)
        
        return result
    
    @staticmethod
    def _extract_json_path(data: Any, json_path: str) -> Any:
        """Extract data using simplified JSONPath-like syntax"""
        # This is a simplified implementation
        # For production use, consider using a proper JSONPath library
        
        try:
            if json_path.startswith("$."):
                path = json_path[2:]  # Remove "$."
                return ExtractService._get_nested_value(data, path)
            else:
                return data
        except Exception:
            return None
    
    @staticmethod
    def _extract_regex_patterns(text: str, patterns: Dict[str, str]) -> Dict[str, Any]:
        """Extract data using regex patterns"""
        import re
        
        result = {}
        
        for pattern_name, pattern in patterns.items():
            try:
                matches = re.findall(pattern, text)
                if matches:
                    # If pattern has groups, return the groups
                    if isinstance(matches[0], tuple):
                        result[pattern_name] = matches
                    else:
                        result[pattern_name] = matches
                else:
                    result[pattern_name] = None
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}': {e}")
                result[pattern_name] = None
        
        return result

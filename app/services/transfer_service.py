from typing import Any, Dict, Optional
import json
import aiofiles
import httpx
import logging
from datetime import datetime
from pathlib import Path
from app.services.ssh_transfer_service import SSHTransferService

logger = logging.getLogger(__name__)


class TransferService:
    """Service for data transfer operations"""
    
    @staticmethod
    async def transfer_data(
        data: Any,
        destination: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Transfer data to various destinations"""
        
        transfer_id = f"transfer_{hash(str(data))}_{int(datetime.now().timestamp())}"
        destination = destination.lower()
        
        try:
            if destination == "ssh":
                result = await TransferService._transfer_via_ssh(data, config, transfer_id)
            elif destination == "webhook":
                result = await TransferService._transfer_to_webhook(data, config, transfer_id)
            elif destination == "database":
                result = await TransferService._transfer_to_database(data, config, transfer_id)
            elif destination == "file":
                result = await TransferService._transfer_to_file(data, config, transfer_id)
            elif destination == "api":
                result = await TransferService._transfer_to_api(data, config, transfer_id)
            elif destination == "email":
                result = await TransferService._transfer_to_email(data, config, transfer_id)
            elif destination == "storage":
                result = await TransferService._transfer_to_storage(data, config, transfer_id)
            else:
                raise ValueError(f"Unsupported destination: {destination}")
            
            logger.info(f"Data transfer to {destination} completed successfully")
            
            return {
                "transfer_id": transfer_id,
                "destination": destination,
                "status": "success",
                "details": result
            }
            
        except Exception as e:
            logger.error(f"Transfer error: {e}")
            raise
    
    @staticmethod
    async def _transfer_via_ssh(data: Any, config: Dict[str, Any], transfer_id: str) -> Dict[str, Any]:
        """Transfer data via SSH using route configuration"""
        if not config or "route_id" not in config:
            raise ValueError("route_id required in transfer_config for SSH destination")
        
        route_id = config["route_id"]
        filename = config.get("filename")
        
        # Ensure data is XML string
        if isinstance(data, str):
            xml_content = data
        elif isinstance(data, dict) and "xml" in data:
            xml_content = data["xml"]
        else:
            # Convert to XML if not already
            xml_content = f'<?xml version="1.0" encoding="UTF-8"?>\n<data>{str(data)}</data>'
        
        # Perform SSH transfer
        result = await SSHTransferService.transfer_xml_file(xml_content, route_id, filename)
        
        return result
    
    @staticmethod
    async def _transfer_to_webhook(data: Any, config: Dict[str, Any], transfer_id: str) -> Dict[str, Any]:
        """Transfer data to webhook endpoint"""
        if not config or "webhook_url" not in config:
            raise ValueError("webhook_url required in transfer_config for webhook destination")
        
        webhook_url = config["webhook_url"]
        method = config.get("method", "POST").upper()
        headers = config.get("headers", {"Content-Type": "application/json"})
        timeout = config.get("timeout", 30)
        
        # Prepare payload
        payload = {
            "transfer_id": transfer_id,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        # Add custom fields if specified
        if config.get("custom_fields"):
            payload.update(config["custom_fields"])
        
        async with httpx.AsyncClient() as client:
            if method == "POST":
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=timeout
                )
            elif method == "PUT":
                response = await client.put(
                    webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            return {
                "webhook_url": webhook_url,
                "status_code": response.status_code,
                "response_body": response.text[:500]  # Limit response body
            }
    
    @staticmethod
    async def _transfer_to_database(data: Any, config: Dict[str, Any], transfer_id: str) -> Dict[str, Any]:
        """Transfer data to database (placeholder implementation)"""
        # This is a placeholder - in production, you would implement actual database connections
        
        db_type = config.get("db_type", "postgresql") if config else "postgresql"
        table_name = config.get("table_name", "etl_data") if config else "etl_data"
        
        # Simulate database operation
        logger.info(f"Would insert data into {db_type} table '{table_name}'")
        
        # In a real implementation, you would:
        # 1. Connect to the database using credentials from config
        # 2. Insert/update the data
        # 3. Return operation details
        
        return {
            "db_type": db_type,
            "table_name": table_name,
            "operation": "INSERT",
            "records_affected": 1
        }
    
    @staticmethod
    async def _transfer_to_file(data: Any, config: Dict[str, Any], transfer_id: str) -> Dict[str, Any]:
        """Transfer data to file system"""
        if not config or "file_path" not in config:
            raise ValueError("file_path required in transfer_config for file destination")
        
        file_path = Path(config["file_path"])
        file_format = config.get("format", "json").lower()
        append_mode = config.get("append", False)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare content based on format
        if file_format == "json":
            content = json.dumps({
                "transfer_id": transfer_id,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }, indent=2, default=str)
        elif file_format == "txt":
            content = f"Transfer ID: {transfer_id}\n"
            content += f"Timestamp: {datetime.now().isoformat()}\n"
            content += f"Data: {str(data)}\n"
        elif file_format == "csv":
            # For CSV, data should be a list of dictionaries
            if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                import csv
                import io
                
                output = io.StringIO()
                if data:
                    writer = csv.DictWriter(output, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                content = output.getvalue()
            else:
                raise ValueError("CSV format requires data to be a list of dictionaries")
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
        
        # Write to file
        mode = "a" if append_mode else "w"
        async with aiofiles.open(file_path, mode=mode, encoding="utf-8") as f:
            if append_mode and file_format in ["json", "txt"]:
                await f.write("\n" + content)
            else:
                await f.write(content)
        
        return {
            "file_path": str(file_path),
            "file_format": file_format,
            "file_size": file_path.stat().st_size,
            "append_mode": append_mode
        }
    
    @staticmethod
    async def _transfer_to_api(data: Any, config: Dict[str, Any], transfer_id: str) -> Dict[str, Any]:
        """Transfer data to API endpoint"""
        if not config or "api_endpoint" not in config:
            raise ValueError("api_endpoint required in transfer_config for api destination")
        
        api_endpoint = config["api_endpoint"]
        method = config.get("method", "POST").upper()
        headers = config.get("headers", {"Content-Type": "application/json"})
        auth = config.get("auth")
        timeout = config.get("timeout", 30)
        
        # Prepare payload
        payload = data
        if config.get("wrap_data", True):
            payload = {
                "transfer_id": transfer_id,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
        
        async with httpx.AsyncClient() as client:
            # Prepare auth if provided
            auth_obj = None
            if auth:
                if auth.get("type") == "basic":
                    auth_obj = (auth["username"], auth["password"])
                elif auth.get("type") == "bearer":
                    headers["Authorization"] = f"Bearer {auth['token']}"
            
            if method == "POST":
                response = await client.post(
                    api_endpoint,
                    json=payload,
                    headers=headers,
                    auth=auth_obj,
                    timeout=timeout
                )
            elif method == "PUT":
                response = await client.put(
                    api_endpoint,
                    json=payload,
                    headers=headers,
                    auth=auth_obj,
                    timeout=timeout
                )
            elif method == "PATCH":
                response = await client.patch(
                    api_endpoint,
                    json=payload,
                    headers=headers,
                    auth=auth_obj,
                    timeout=timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            return {
                "api_endpoint": api_endpoint,
                "method": method,
                "status_code": response.status_code,
                "response_body": response.text[:500]
            }
    
    @staticmethod
    async def _transfer_to_email(data: Any, config: Dict[str, Any], transfer_id: str) -> Dict[str, Any]:
        """Transfer data via email (placeholder implementation)"""
        # This is a placeholder - in production, you would implement email sending
        
        if not config:
            raise ValueError("Email configuration required")
        
        recipient = config.get("recipient")
        subject = config.get("subject", f"ETL Data Transfer - {transfer_id}")
        
        if not recipient:
            raise ValueError("recipient required in transfer_config for email destination")
        
        # Simulate email sending
        logger.info(f"Would send email to {recipient} with subject '{subject}'")
        
        return {
            "recipient": recipient,
            "subject": subject,
            "data_size": len(str(data)),
            "status": "sent"
        }
    
    @staticmethod
    async def _transfer_to_storage(data: Any, config: Dict[str, Any], transfer_id: str) -> Dict[str, Any]:
        """Transfer data to cloud storage (placeholder implementation)"""
        # This is a placeholder - in production, you would implement cloud storage uploads
        
        if not config:
            raise ValueError("Storage configuration required")
        
        storage_type = config.get("storage_type", "s3")
        bucket = config.get("bucket")
        key = config.get("key", f"etl-data/{transfer_id}.json")
        
        if not bucket:
            raise ValueError("bucket required in transfer_config for storage destination")
        
        # Simulate storage upload
        logger.info(f"Would upload to {storage_type} bucket '{bucket}' with key '{key}'")
        
        return {
            "storage_type": storage_type,
            "bucket": bucket,
            "key": key,
            "data_size": len(str(data)),
            "status": "uploaded"
        }

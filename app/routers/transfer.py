from fastapi import APIRouter, HTTPException
from app.models import TransferRequest, TransferResponse
from app.services.transfer_service import TransferService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transfer", tags=["Transfer"])


@router.post("", response_model=TransferResponse)
async def transfer_data(request: TransferRequest):
    """
    Transfer-Endpunkt für Datenübertragung
    
    Kann Daten zu verschiedenen Zielsystemen übertragen:
    
    **Webhook:**
    ```json
    {
        "destination": "webhook",
        "transfer_config": {
            "webhook_url": "https://hooks.example.com/webhook",
            "method": "POST",
            "headers": {"Authorization": "Bearer token"},
            "custom_fields": {"source": "etl_api"},
            "timeout": 30
        }
    }
    ```
    
    **API:**
    ```json
    {
        "destination": "api",
        "transfer_config": {
            "api_endpoint": "https://api.example.com/data",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "auth": {
                "type": "bearer",
                "token": "your_token"
            },
            "wrap_data": true,
            "timeout": 30
        }
    }
    ```
    
    **File:**
    ```json
    {
        "destination": "file",
        "transfer_config": {
            "file_path": "/path/to/output.json",
            "format": "json",
            "append": false
        }
    }
    ```
    
    **Database:**
    ```json
    {
        "destination": "database",
        "transfer_config": {
            "db_type": "postgresql",
            "table_name": "etl_data"
        }
    }
    ```
    
    **Email:**
    ```json
    {
        "destination": "email",
        "transfer_config": {
            "recipient": "user@example.com",
            "subject": "ETL Data Transfer"
        }
    }
    ```
    
    **SSH Transfer:**
    ```json
    {
        "destination": "ssh",
        "transfer_config": {
            "route_id": "server_prod_01",
            "filename": "data_export.xml"
        }
    }
    ```
    
    **Cloud Storage:**
    ```json
    {
        "destination": "storage",
        "transfer_config": {
            "storage_type": "s3",
            "bucket": "my-bucket",
            "key": "data/file.json"
        }
    }
    ```
    
    **Unterstützte Formate:** json, txt, csv (für Dateien), xml (für SSH)
    **Unterstützte Auth-Typen:** basic, bearer (für APIs), password/private_key (für SSH)
    """
    try:
        result = await TransferService.transfer_data(
            data=request.data,
            destination=request.destination,
            config=request.transfer_config
        )
        
        return TransferResponse(
            transfer_id=result["transfer_id"],
            destination=request.destination,
            message=f"Data transfer to {request.destination} completed successfully"
        )
        
    except ValueError as e:
        logger.error(f"Transfer validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Transfer error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Transfer operation failed: {str(e)}"
        )

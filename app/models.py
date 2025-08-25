from pydantic import BaseModel
from typing import Any, Dict, Optional


class TransformRequest(BaseModel):
    data: Any
    transformation_rules: Optional[Dict[str, Any]] = None
    
class TransformResponse(BaseModel):
    transformed_data: Any
    status: str = "success"
    message: Optional[str] = None


class ExtractRequest(BaseModel):
    source_url: Optional[str] = None
    source_data: Optional[Any] = None
    extraction_config: Optional[Dict[str, Any]] = None
    
class ExtractResponse(BaseModel):
    extracted_data: Any
    status: str = "success"
    source: Optional[str] = None
    message: Optional[str] = None


class TransferRequest(BaseModel):
    data: Any
    destination: str
    transfer_config: Optional[Dict[str, Any]] = None
    
class TransferResponse(BaseModel):
    transfer_id: Optional[str] = None
    status: str = "success"
    destination: str
    message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    playwright_available: bool

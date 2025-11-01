"""
API request and response schemas
Defines data structures for API communication
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models import ProcessingStatus, ContractData


class UploadResponse(BaseModel):
    """Response for contract upload"""
    contract_id: str
    message: str = "Contract uploaded successfully and processing initiated"
    filename: str
    file_size: int


class StatusResponse(BaseModel):
    """Response for status check"""
    contract_id: str
    status: ProcessingStatus
    progress: int = Field(ge=0, le=100, description="Progress percentage (0-100)")
    error_message: Optional[str] = None
    upload_date: datetime
    processing_time_seconds: Optional[float] = None


class ContractSummary(BaseModel):
    """Summary of contract for list view"""
    contract_id: str
    filename: str
    status: ProcessingStatus
    upload_date: datetime
    completeness_score: float
    total_value: Optional[float] = None
    currency: Optional[str] = None
    customer_name: Optional[str] = None
    vendor_name: Optional[str] = None
    contract_type: Optional[str] = None


class ContractListResponse(BaseModel):
    """Response for contract list"""
    contracts: List[ContractSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class ContractFilter(BaseModel):
    """Query parameters for filtering contracts"""
    status: Optional[ProcessingStatus] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_score: Optional[float] = Field(None, ge=0, le=100)
    max_score: Optional[float] = Field(None, ge=0, le=100)
    search: Optional[str] = None  # Search in filename or customer name
    sort_by: str = "upload_date"  # upload_date, completeness_score, filename
    sort_order: str = "desc"  # asc or desc


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    contract_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    database: str
    redis: str
    timestamp: datetime
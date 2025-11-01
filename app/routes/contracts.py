"""
Contract API routes
Implements all contract-related endpoints
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from pymongo.errors import DuplicateKeyError

from app.database import get_contracts_collection
from app.schemas import (
    UploadResponse, StatusResponse, ContractListResponse,
    ContractSummary, ErrorResponse
)
from app.models import ProcessingStatus, ContractData
from app.services.storage import storage_service
from app.tasks.celery_tasks import process_contract

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_contract(
    file: UploadFile = File(..., description="PDF contract file to upload")
):
    """
    Upload a contract for processing
    
    - Accepts PDF files up to 50MB
    - Returns contract_id immediately
    - Processing happens asynchronously
    """
    try:
        logger.info(f"Received upload request: {file.filename}")
        
        # Generate unique contract ID
        contract_id = str(uuid.uuid4())
        
        # Save file
        file_path, file_size = await storage_service.save_file(file, contract_id)
        
        # Create database entry
        contracts = get_contracts_collection()
        
        contract_doc = {
            "contract_id": contract_id,
            "filename": file.filename,
            "file_path": file_path,
            "file_size": file_size,
            "file_type": file.content_type,
            "status": ProcessingStatus.PENDING.value,
            "progress": 0,
            "upload_date": datetime.utcnow(),
            "completeness_score": 0.0,
            "missing_fields": []
        }
        
        contracts.insert_one(contract_doc)
        
        # Trigger background processing
        process_contract.delay(contract_id, file_path)
        
        logger.info(f"Contract uploaded successfully: {contract_id}")
        
        return UploadResponse(
            contract_id=contract_id,
            filename=file.filename,
            file_size=file_size
        )
        
    except HTTPException:
        raise
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail="Contract with this ID already exists"
        )
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload contract: {str(e)}"
        )


@router.get("/{contract_id}/status", response_model=StatusResponse)
async def get_contract_status(contract_id: str):
    """
    Get processing status of a contract
    
    - Returns current status: pending, processing, completed, or failed
    - Includes progress percentage
    - Shows error message if processing failed
    """
    try:
        contracts = get_contracts_collection()
        
        contract = contracts.find_one(
            {"contract_id": contract_id},
            {
                "contract_id": 1,
                "status": 1,
                "progress": 1,
                "error_message": 1,
                "upload_date": 1,
                "processing_time_seconds": 1
            }
        )
        
        if not contract:
            raise HTTPException(
                status_code=404,
                detail=f"Contract not found: {contract_id}"
            )
        
        return StatusResponse(
            contract_id=contract["contract_id"],
            status=contract["status"],
            progress=contract.get("progress", 0),
            error_message=contract.get("error_message"),
            upload_date=contract["upload_date"],
            processing_time_seconds=contract.get("processing_time_seconds")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get contract status: {str(e)}"
        )


@router.get("/{contract_id}", response_model=ContractData)
async def get_contract(contract_id: str):
    """
    Get complete parsed contract data
    
    - Only available when processing is complete
    - Returns 202 if still processing
    - Returns full contract details with extracted information
    """
    try:
        contracts = get_contracts_collection()
        
        contract = contracts.find_one({"contract_id": contract_id})
        
        if not contract:
            raise HTTPException(
                status_code=404,
                detail=f"Contract not found: {contract_id}"
            )
        
        # Check if processing is complete
        status = contract.get("status")
        
        if status == ProcessingStatus.PENDING.value:
            raise HTTPException(
                status_code=202,
                detail="Contract is queued for processing"
            )
        
        if status == ProcessingStatus.PROCESSING.value:
            raise HTTPException(
                status_code=202,
                detail=f"Contract is being processed ({contract.get('progress', 0)}% complete)"
            )
        
        if status == ProcessingStatus.FAILED.value:
            raise HTTPException(
                status_code=500,
                detail=f"Contract processing failed: {contract.get('error_message', 'Unknown error')}"
            )
        
        # Remove MongoDB _id field
        contract.pop('_id', None)
        
        return ContractData(**contract)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contract: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get contract data: {str(e)}"
        )


@router.get("", response_model=ContractListResponse)
async def list_contracts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[ProcessingStatus] = Query(None, description="Filter by status"),
    date_from: Optional[datetime] = Query(None, description="Filter by upload date from"),
    date_to: Optional[datetime] = Query(None, description="Filter by upload date to"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum score"),
    max_score: Optional[float] = Query(None, ge=0, le=100, description="Maximum score"),
    search: Optional[str] = Query(None, description="Search in filename or customer name"),
    sort_by: str = Query("upload_date", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """
    Get paginated list of contracts with filtering
    
    - Supports pagination
    - Filter by status, date range, score range
    - Search in filename and customer name
    - Sort by various fields
    """
    try:
        contracts = get_contracts_collection()
        
        # Build filter query
        query = {}
        
        if status:
            query["status"] = status.value
        
        if date_from or date_to:
            query["upload_date"] = {}
            if date_from:
                query["upload_date"]["$gte"] = date_from
            if date_to:
                query["upload_date"]["$lte"] = date_to
        
        if min_score is not None or max_score is not None:
            query["completeness_score"] = {}
            if min_score is not None:
                query["completeness_score"]["$gte"] = min_score
            if max_score is not None:
                query["completeness_score"]["$lte"] = max_score
        
        if search:
            query["$or"] = [
                {"filename": {"$regex": search, "$options": "i"}},
                {"customer.name": {"$regex": search, "$options": "i"}},
                {"vendor.name": {"$regex": search, "$options": "i"}}
            ]
        
        # Count total matching documents
        total = contracts.count_documents(query)
        
        # Calculate pagination
        skip = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size
        
        # Build sort
        sort_direction = -1 if sort_order == "desc" else 1
        
        # Query contracts
        cursor = contracts.find(query).sort(sort_by, sort_direction).skip(skip).limit(page_size)
        
        # Build response
        contract_summaries = []
        for contract in cursor:
            summary = ContractSummary(
                contract_id=contract["contract_id"],
                filename=contract["filename"],
                status=contract["status"],
                upload_date=contract["upload_date"],
                completeness_score=contract.get("completeness_score", 0.0),
                total_value=contract.get("financial_details", {}).get("total_value") if contract.get("financial_details") else None,
                currency=contract.get("financial_details", {}).get("currency") if contract.get("financial_details") else None,
                customer_name=contract.get("customer", {}).get("name") if contract.get("customer") else None,
                vendor_name=contract.get("vendor", {}).get("name") if contract.get("vendor") else None,
                contract_type=contract.get("contract_type")
            )
            contract_summaries.append(summary)
        
        return ContractListResponse(
            contracts=contract_summaries,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error listing contracts: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list contracts: {str(e)}"
        )


@router.get("/{contract_id}/download")
async def download_contract(contract_id: str):
    """
    Download original contract file
    
    - Returns the original uploaded PDF
    - Maintains proper file headers
    """
    try:
        contracts = get_contracts_collection()
        
        contract = contracts.find_one(
            {"contract_id": contract_id},
            {"file_path": 1, "filename": 1}
        )
        
        if not contract:
            raise HTTPException(
                status_code=404,
                detail=f"Contract not found: {contract_id}"
            )
        
        file_path = contract.get("file_path")
        
        if not storage_service.file_exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="Contract file not found on server"
            )
        
        return FileResponse(
            path=file_path,
            filename=contract["filename"],
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading contract: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download contract: {str(e)}"
        )
"""
File storage service
Handles file uploads, validation, and retrieval
"""

import os
import uuid
import logging
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing file storage"""
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self._ensure_upload_directory()
    
    def _ensure_upload_directory(self) -> None:
        """Create upload directory if it doesn't exist"""
        try:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Upload directory ready: {self.upload_dir}")
        except Exception as e:
            logger.error(f"Failed to create upload directory: {e}")
            raise
    
    def validate_file(self, file: UploadFile) -> None:
        """
        Validate uploaded file
        
        Args:
            file: Uploaded file
            
        Raises:
            HTTPException: If file is invalid
        """
        # Check file type
        if not file.content_type == "application/pdf":
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Only PDF files are accepted. Got: {file.content_type}"
            )
        
        # Check filename
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is required"
            )
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="File must have .pdf extension"
            )
    
    async def save_file(
        self,
        file: UploadFile,
        contract_id: str
    ) -> Tuple[str, int]:
        """
        Save uploaded file to disk
        
        Args:
            file: Uploaded file
            contract_id: Unique contract identifier
            
        Returns:
            Tuple of (file_path, file_size)
            
        Raises:
            HTTPException: If file operations fail
        """
        try:
            # Validate file
            self.validate_file(file)
            
            # Generate unique filename
            file_extension = Path(file.filename).suffix
            unique_filename = f"{contract_id}{file_extension}"
            file_path = self.upload_dir / unique_filename
            
            # Read and validate file size
            contents = await file.read()
            file_size = len(contents)
            
            if file_size > settings.max_file_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size: {settings.max_file_size / 1024 / 1024:.1f}MB"
                )
            
            if file_size == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Empty file not allowed"
                )
            
            # Write file to disk
            with open(file_path, 'wb') as f:
                f.write(contents)
            
            logger.info(f"File saved: {file_path} ({file_size} bytes)")
            
            return str(file_path), file_size
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )
        finally:
            await file.seek(0)  # Reset file pointer
    
    def get_file_path(self, contract_id: str, filename: str) -> Path:
        """
        Get full file path for a contract
        
        Args:
            contract_id: Contract identifier
            filename: Original filename
            
        Returns:
            Path object for the file
        """
        file_extension = Path(filename).suffix
        unique_filename = f"{contract_id}{file_extension}"
        return self.upload_dir / unique_filename
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file exists, False otherwise
        """
        return Path(file_path).exists()
    
    def get_file_size(self, file_path: str) -> int:
        """
        Get file size in bytes
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in bytes
        """
        try:
            return Path(file_path).stat().st_size
        except Exception as e:
            logger.error(f"Error getting file size: {e}")
            return 0
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from disk
        
        Args:
            file_path: Path to file
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False


# Global storage service instance
storage_service = StorageService()
"""
Database connection and management module
Handles MongoDB connection lifecycle and provides database access
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, OperationFailure
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Global database client
_client: Optional[MongoClient] = None
_database: Optional[Database] = None


def connect_to_mongo() -> None:
    """
    Establish connection to MongoDB and create indexes
    Called during application startup
    """
    global _client, _database
    
    try:
        logger.info(f"Connecting to MongoDB at {settings.mongodb_url}")
        
        # Create MongoDB client
        _client = MongoClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        
        # Test connection
        _client.admin.command('ping')
        
        # Get database
        _database = _client[settings.mongodb_db_name]
        
        # Create indexes
        _create_indexes()
        
        logger.info("Successfully connected to MongoDB")
        
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to MongoDB: {e}")
        raise


def _create_indexes() -> None:
    """
    Create database indexes for optimal query performance
    """
    try:
        contracts_collection = _database.contracts
        
        # Create unique index on contract_id
        contracts_collection.create_index(
            [("contract_id", ASCENDING)],
            unique=True,
            name="contract_id_unique"
        )
        
        # Create index on status for filtering
        contracts_collection.create_index(
            [("status", ASCENDING)],
            name="status_index"
        )
        
        # Create index on upload_date for sorting and filtering
        contracts_collection.create_index(
            [("upload_date", DESCENDING)],
            name="upload_date_index"
        )
        
        # Create compound index for common queries
        contracts_collection.create_index(
            [("status", ASCENDING), ("upload_date", DESCENDING)],
            name="status_date_index"
        )
        
        # Create index on completeness_score for filtering
        contracts_collection.create_index(
            [("completeness_score", DESCENDING)],
            name="score_index"
        )
        
        logger.info("Database indexes created successfully")
        
    except OperationFailure as e:
        logger.warning(f"Index creation warning: {e}")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")


def close_mongo_connection() -> None:
    """
    Close MongoDB connection
    Called during application shutdown
    """
    global _client, _database
    
    if _client:
        logger.info("Closing MongoDB connection")
        _client.close()
        _client = None
        _database = None
        logger.info("MongoDB connection closed")


def get_database() -> Database:
    """
    Get database instance
    
    Returns:
        Database: MongoDB database instance
        
    Raises:
        RuntimeError: If database connection not established
    """
    if _database is None:
        raise RuntimeError(
            "Database connection not established. "
            "Call connect_to_mongo() first."
        )
    return _database


def get_contracts_collection():
    """
    Get contracts collection
    
    Returns:
        Collection: MongoDB contracts collection
    """
    db = get_database()
    return db.contracts
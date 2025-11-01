"""
Celery tasks for asynchronous contract processing
"""

import logging
import time
from datetime import datetime
from celery import Celery

from app.config import settings
from app.database import get_contracts_collection
from app.services.parser import contract_parser
from app.services.scoring import scoring_service
from app.models import ProcessingStatus

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    'contract_parser',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max
    task_soft_time_limit=540,  # 9 minutes soft limit
)


@celery_app.task(bind=True, name='tasks.process_contract', max_retries=2)
def process_contract(self, contract_id: str, file_path: str) -> dict:
    """
    Process contract document asynchronously
    
    Args:
        contract_id: Unique contract identifier
        file_path: Path to uploaded contract file
        
    Returns:
        Processing result dictionary
    """
    start_time = time.time()
    contracts = get_contracts_collection()
    
    try:
        logger.info(f"Starting contract processing: {contract_id}")
        
        # Update status to processing
        contracts.update_one(
            {"contract_id": contract_id},
            {
                "$set": {
                    "status": ProcessingStatus.PROCESSING.value,
                    "progress": 10,
                    "processing_start_date": datetime.utcnow()
                }
            }
        )
        
        # Step 1: Extract and parse contract (60% of progress)
        logger.info(f"Parsing contract: {contract_id}")
        contracts.update_one(
            {"contract_id": contract_id},
            {"$set": {"progress": 20}}
        )
        
        parsed_data = contract_parser.parse_contract(file_path)
        
        contracts.update_one(
            {"contract_id": contract_id},
            {"$set": {"progress": 60}}
        )
        
        # Step 2: Calculate completeness score (20% of progress)
        logger.info(f"Calculating score: {contract_id}")
        contracts.update_one(
            {"contract_id": contract_id},
            {"$set": {"progress": 70}}
        )
        
        total_score, score_breakdown, missing_fields = scoring_service.calculate_score(parsed_data)
        
        contracts.update_one(
            {"contract_id": contract_id},
            {"$set": {"progress": 90}}
        )
        
        # Step 3: Update database with results
        logger.info(f"Saving results: {contract_id}")
        
        processing_time = time.time() - start_time
        
        update_data = {
            "status": ProcessingStatus.COMPLETED.value,
            "progress": 100,
            "processing_end_date": datetime.utcnow(),
            "processing_time_seconds": processing_time,
            
            # Parsed data
            "contract_title": parsed_data.get('contract_title'),
            "contract_type": parsed_data.get('contract_type'),
            "description": parsed_data.get('description'),
            "contract_dates": parsed_data.get('contract_dates'),
            
            # Parties
            "customer": parsed_data.get('customer'),
            "vendor": parsed_data.get('vendor'),
            
            # Detailed information
            "account_info": parsed_data.get('account_info'),
            "financial_details": parsed_data.get('financial_details'),
            "payment_structure": parsed_data.get('payment_structure'),
            "revenue_classification": parsed_data.get('revenue_classification'),
            "sla": parsed_data.get('sla'),
            
            # Scoring
            "completeness_score": total_score,
            "score_breakdown": score_breakdown.dict(),
            "missing_fields": missing_fields,
            
            # Raw data (truncated)
            "extracted_text": parsed_data.get('extracted_text', '')[:5000]
        }
        
        result = contracts.update_one(
            {"contract_id": contract_id},
            {"$set": update_data}
        )
        
        logger.info(
            f"Contract processing completed: {contract_id} "
            f"(Score: {total_score:.2f}, Time: {processing_time:.2f}s)"
        )
        
        return {
            "status": "completed",
            "contract_id": contract_id,
            "score": total_score,
            "processing_time": processing_time
        }
        
    except Exception as e:
        logger.error(f"Contract processing failed: {contract_id} - {str(e)}", exc_info=True)
        
        processing_time = time.time() - start_time
        
        # Update database with error
        contracts.update_one(
            {"contract_id": contract_id},
            {
                "$set": {
                    "status": ProcessingStatus.FAILED.value,
                    "progress": 0,
                    "error_message": str(e),
                    "processing_end_date": datetime.utcnow(),
                    "processing_time_seconds": processing_time
                }
            }
        )
        
        # Retry if not at max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying contract processing: {contract_id}")
            raise self.retry(exc=e, countdown=60)  # Retry after 60 seconds
        
        return {
            "status": "failed",
            "contract_id": contract_id,
            "error": str(e),
            "processing_time": processing_time
        }
"""
Contract parser service
Extracts text from PDFs and uses LLM to parse contract information
"""

import logging
import json
import pdfplumber
from pathlib import Path
from typing import Dict, Any, Optional
from openai import OpenAI

from app.config import settings
from app.models import (
    PartyInfo, AccountInfo, FinancialDetails, PaymentStructure,
    RevenueClassification, SLA, ContractDates
)

logger = logging.getLogger(__name__)


class ContractParser:
    """Service for parsing contract documents"""
    
    def __init__(self):
        # OpenRouter uses OpenAI-compatible API
        self.client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = settings.openrouter_model
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extract text content from PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
            
        Raises:
            Exception: If extraction fails
        """
        try:
            logger.info(f"Extracting text from PDF: {file_path}")
            
            text_content = []
            
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        text_content.append(f"--- Page {page_num} ---\n{text}")
            
            full_text = "\n\n".join(text_content)
            
            if not full_text.strip():
                raise ValueError("No text content extracted from PDF")
            
            logger.info(f"Extracted {len(full_text)} characters from PDF")
            return full_text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
    
    def _create_extraction_prompt(self, text: str) -> str:
        """
        Create prompt for LLM to extract contract information
        
        Args:
            text: Contract text
            
        Returns:
            Formatted prompt
        """
        return f"""You are a contract analysis expert. Extract structured information from the following contract document.

Contract Text:
{text}

Please extract and return a JSON object with the following structure. If information is not found, use null for that field. Include confidence scores (0.0 to 1.0) for major sections.

{{
  "contract_title": "string or null",
  "contract_type": "string or null (e.g., 'Service Agreement', 'Purchase Order', 'SaaS Contract')",
  "description": "brief description or null",
  
  "contract_dates": {{
    "effective_date": "YYYY-MM-DD or null",
    "expiration_date": "YYYY-MM-DD or null",
    "signature_date": "YYYY-MM-DD or null"
  }},
  
  "customer": {{
    "name": "string or null",
    "legal_entity": "string or null",
    "registration_details": "string or null",
    "address": "string or null",
    "signatories": [
      {{"name": "string", "role": "string", "title": "string"}}
    ],
    "confidence_score": 0.0-1.0
  }},
  
  "vendor": {{
    "name": "string or null",
    "legal_entity": "string or null",
    "registration_details": "string or null",
    "address": "string or null",
    "signatories": [
      {{"name": "string", "role": "string", "title": "string"}}
    ],
    "confidence_score": 0.0-1.0
  }},
  
  "account_info": {{
    "billing_details": "string or null",
    "account_numbers": ["string"],
    "contact_info": {{
      "email": "string or null",
      "phone": "string or null",
      "address": "string or null"
    }},
    "billing_contact": {{
      "email": "string or null",
      "phone": "string or null"
    }},
    "technical_contact": {{
      "email": "string or null",
      "phone": "string or null"
    }},
    "confidence_score": 0.0-1.0
  }},
  
  "financial_details": {{
    "line_items": [
      {{
        "description": "string",
        "quantity": number or null,
        "unit_price": number or null,
        "total_price": number or null,
        "unit": "string or null"
      }}
    ],
    "total_value": number or null,
    "currency": "string (e.g., 'USD', 'EUR')",
    "tax_info": "string or null",
    "tax_amount": number or null,
    "subtotal": number or null,
    "confidence_score": 0.0-1.0
  }},
  
  "payment_structure": {{
    "payment_terms": "string (e.g., 'Net 30', 'Net 60', 'Due on receipt')",
    "schedules": [
      {{
        "due_date": "YYYY-MM-DD or string",
        "amount": number,
        "description": "string"
      }}
    ],
    "methods": ["string (e.g., 'Wire Transfer', 'Check', 'Credit Card')"],
    "banking_details": "string or null",
    "late_payment_penalty": "string or null",
    "confidence_score": 0.0-1.0
  }},
  
  "revenue_classification": {{
    "recurring_payment": boolean,
    "one_time_payment": boolean,
    "subscription_model": "string or null (e.g., 'monthly', 'annual')",
    "billing_cycle": "string or null",
    "renewal_terms": "string or null",
    "auto_renewal": boolean,
    "renewal_notice_period": "string or null",
    "confidence_score": 0.0-1.0
  }},
  
  "sla": {{
    "performance_metrics": [
      {{
        "name": "string",
        "target": "string",
        "measurement": "string"
      }}
    ],
    "penalty_clauses": ["string"],
    "support_terms": "string or null",
    "uptime_guarantee": "string or null",
    "response_time": "string or null",
    "resolution_time": "string or null",
    "confidence_score": 0.0-1.0
  }}
}}

Return ONLY the JSON object, no additional text or explanation."""
    
    def _call_llm(self, prompt: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Call LLM API to extract information
        
        Args:
            prompt: Extraction prompt
            max_retries: Maximum number of retry attempts
            
        Returns:
            Parsed JSON response
            
        Raises:
            Exception: If all retries fail
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Calling OpenRouter API (attempt {attempt + 1}/{max_retries})")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a contract analysis expert. Extract information and return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content
                
                # Parse JSON response
                parsed_data = json.loads(content)
                logger.info("Successfully parsed LLM response")
                return parsed_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                if attempt == max_retries - 1:
                    raise
            except Exception as e:
                logger.error(f"LLM API call failed: {e}")
                if attempt == max_retries - 1:
                    raise
        
        raise Exception("Failed to get valid response from LLM after all retries")
    
    def parse_contract(self, file_path: str) -> Dict[str, Any]:
        """
        Parse contract document and extract structured information
        
        Args:
            file_path: Path to contract PDF
            
        Returns:
            Parsed contract data
        """
        try:
            # Extract text from PDF
            text = self.extract_text_from_pdf(file_path)
            
            # Create prompt
            prompt = self._create_extraction_prompt(text)
            
            # Call LLM
            parsed_data = self._call_llm(prompt)
            
            # Add extracted text to result
            parsed_data['extracted_text'] = text[:5000]  # Store first 5000 chars
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Contract parsing failed: {e}")
            raise


# Global parser instance
contract_parser = ContractParser()
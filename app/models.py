"""
Data models for contract intelligence system
Defines all structured data types for contract information
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ProcessingStatus(str, Enum):
    """Contract processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Signatory(BaseModel):
    """Authorized signatory information"""
    name: Optional[str] = None
    role: Optional[str] = None
    title: Optional[str] = None


class PartyInfo(BaseModel):
    """Party identification information"""
    name: Optional[str] = None
    legal_entity: Optional[str] = None
    registration_details: Optional[str] = None
    signatories: List[Signatory] = Field(default_factory=list)
    address: Optional[str] = None
    confidence_score: float = 0.0


class ContactInfo(BaseModel):
    """Contact information"""
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    department: Optional[str] = None


class AccountInfo(BaseModel):
    """Account and billing information"""
    billing_details: Optional[str] = None
    account_numbers: List[str] = Field(default_factory=list)
    contact_info: Optional[ContactInfo] = None
    billing_contact: Optional[ContactInfo] = None
    technical_contact: Optional[ContactInfo] = None
    confidence_score: float = 0.0


class LineItem(BaseModel):
    """Individual line item in contract"""
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    unit: Optional[str] = None


class FinancialDetails(BaseModel):
    """Financial information"""
    line_items: List[LineItem] = Field(default_factory=list)
    total_value: Optional[float] = None
    currency: Optional[str] = None
    tax_info: Optional[str] = None
    tax_amount: Optional[float] = None
    additional_fees: Optional[Dict[str, float]] = None
    subtotal: Optional[float] = None
    confidence_score: float = 0.0


class PaymentSchedule(BaseModel):
    """Payment schedule entry"""
    due_date: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None


class PaymentStructure(BaseModel):
    """Payment terms and structure"""
    payment_terms: Optional[str] = None  # e.g., "Net 30", "Net 60"
    schedules: List[PaymentSchedule] = Field(default_factory=list)
    due_dates: List[str] = Field(default_factory=list)
    methods: List[str] = Field(default_factory=list)
    banking_details: Optional[str] = None
    late_payment_penalty: Optional[str] = None
    confidence_score: float = 0.0


class RevenueClassification(BaseModel):
    """Revenue and billing classification"""
    recurring_payment: bool = False
    one_time_payment: bool = False
    subscription_model: Optional[str] = None
    billing_cycle: Optional[str] = None  # e.g., "monthly", "quarterly", "annual"
    renewal_terms: Optional[str] = None
    auto_renewal: bool = False
    renewal_notice_period: Optional[str] = None
    confidence_score: float = 0.0


class PerformanceMetric(BaseModel):
    """SLA performance metric"""
    name: Optional[str] = None
    target: Optional[str] = None
    measurement: Optional[str] = None


class SLA(BaseModel):
    """Service Level Agreement terms"""
    performance_metrics: List[PerformanceMetric] = Field(default_factory=list)
    penalty_clauses: List[str] = Field(default_factory=list)
    support_terms: Optional[str] = None
    uptime_guarantee: Optional[str] = None
    response_time: Optional[str] = None
    resolution_time: Optional[str] = None
    confidence_score: float = 0.0


class ScoreBreakdown(BaseModel):
    """Detailed scoring breakdown"""
    financial_completeness: float = 0.0  # Max 30 points
    party_identification: float = 0.0    # Max 25 points
    payment_terms: float = 0.0            # Max 20 points
    sla_definition: float = 0.0           # Max 15 points
    contact_information: float = 0.0      # Max 10 points


class ContractDates(BaseModel):
    """Contract date information"""
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    signature_date: Optional[str] = None
    notice_date: Optional[str] = None


class ContractData(BaseModel):
    """Complete contract data model"""
    # Identification
    contract_id: str
    filename: str
    status: ProcessingStatus = ProcessingStatus.PENDING
    
    # Dates
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    processing_start_date: Optional[datetime] = None
    processing_end_date: Optional[datetime] = None
    contract_dates: Optional[ContractDates] = None
    
    # File Information
    file_path: str
    file_size: int
    file_type: str = "application/pdf"
    
    # Extracted Data
    parties: List[PartyInfo] = Field(default_factory=list)
    customer: Optional[PartyInfo] = None
    vendor: Optional[PartyInfo] = None
    account_info: Optional[AccountInfo] = None
    financial_details: Optional[FinancialDetails] = None
    payment_structure: Optional[PaymentStructure] = None
    revenue_classification: Optional[RevenueClassification] = None
    sla: Optional[SLA] = None
    
    # Contract Metadata
    contract_title: Optional[str] = None
    contract_type: Optional[str] = None
    description: Optional[str] = None
    
    # Scoring
    completeness_score: float = 0.0
    score_breakdown: Optional[ScoreBreakdown] = None
    missing_fields: List[str] = Field(default_factory=list)
    
    # Processing Information
    progress: int = 0  # 0-100
    error_message: Optional[str] = None
    processing_time_seconds: Optional[float] = None
    
    # Raw Data
    extracted_text: Optional[str] = None  # Store for reference
    
    class Config:
        use_enum_values = True
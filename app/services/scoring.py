"""
Contract scoring service
Calculates completeness scores and identifies missing fields
"""

import logging
from typing import Dict, List, Tuple, Any
from app.models import (
    ScoreBreakdown, PartyInfo, AccountInfo, FinancialDetails,
    PaymentStructure, RevenueClassification, SLA
)

logger = logging.getLogger(__name__)


class ScoringService:
    """Service for scoring contract completeness"""
    
    # Maximum points for each category
    MAX_FINANCIAL = 30
    MAX_PARTY = 25
    MAX_PAYMENT = 20
    MAX_SLA = 15
    MAX_CONTACT = 10
    
    def calculate_score(self, contract_data: Dict[str, Any]) -> Tuple[float, ScoreBreakdown, List[str]]:
        """
        Calculate completeness score for contract
        
        Args:
            contract_data: Parsed contract data
            
        Returns:
            Tuple of (total_score, score_breakdown, missing_fields)
        """
        try:
            # Calculate individual scores
            financial_score = self._score_financial(contract_data.get('financial_details'))
            party_score = self._score_parties(
                contract_data.get('customer'),
                contract_data.get('vendor')
            )
            payment_score = self._score_payment(contract_data.get('payment_structure'))
            sla_score = self._score_sla(contract_data.get('sla'))
            contact_score = self._score_contact(contract_data.get('account_info'))
            
            # Create score breakdown
            breakdown = ScoreBreakdown(
                financial_completeness=financial_score,
                party_identification=party_score,
                payment_terms=payment_score,
                sla_definition=sla_score,
                contact_information=contact_score
            )
            
            # Calculate total score
            total_score = (
                financial_score +
                party_score +
                payment_score +
                sla_score +
                contact_score
            )
            
            # Identify missing fields
            missing_fields = self._identify_missing_fields(contract_data)
            
            logger.info(f"Contract score calculated: {total_score:.2f}/100")
            
            return total_score, breakdown, missing_fields
            
        except Exception as e:
            logger.error(f"Error calculating score: {e}")
            return 0.0, ScoreBreakdown(), ["Error calculating score"]
    
    def _score_financial(self, financial: Optional[Dict]) -> float:
        """
        Score financial completeness (max 30 points)
        
        Criteria:
        - Line items present and detailed: 15 points
        - Total value specified: 10 points
        - Currency specified: 3 points
        - Tax information: 2 points
        """
        if not financial:
            return 0.0
        
        score = 0.0
        
        # Line items (15 points)
        line_items = financial.get('line_items', [])
        if line_items:
            item_score = 0
            for item in line_items:
                if item.get('description'):
                    item_score += 5
                if item.get('quantity') is not None and item.get('unit_price') is not None:
                    item_score += 5
                if item.get('total_price') is not None:
                    item_score += 5
            score += min(item_score / len(line_items), 15)
        
        # Total value (10 points)
        if financial.get('total_value') is not None:
            score += 10
        
        # Currency (3 points)
        if financial.get('currency'):
            score += 3
        
        # Tax information (2 points)
        if financial.get('tax_info') or financial.get('tax_amount') is not None:
            score += 2
        
        return min(score, self.MAX_FINANCIAL)
    
    def _score_parties(
        self,
        customer: Optional[Dict],
        vendor: Optional[Dict]
    ) -> float:
        """
        Score party identification (max 25 points)
        
        Criteria:
        - Customer identified: 12.5 points (name, legal entity, address, signatories)
        - Vendor identified: 12.5 points (name, legal entity, address, signatories)
        """
        score = 0.0
        
        # Score customer (12.5 points)
        if customer:
            customer_score = 0
            if customer.get('name'):
                customer_score += 4
            if customer.get('legal_entity'):
                customer_score += 3
            if customer.get('address'):
                customer_score += 2.5
            if customer.get('signatories'):
                customer_score += 3
            score += customer_score
        
        # Score vendor (12.5 points)
        if vendor:
            vendor_score = 0
            if vendor.get('name'):
                vendor_score += 4
            if vendor.get('legal_entity'):
                vendor_score += 3
            if vendor.get('address'):
                vendor_score += 2.5
            if vendor.get('signatories'):
                vendor_score += 3
            score += vendor_score
        
        return min(score, self.MAX_PARTY)
    
    def _score_payment(self, payment: Optional[Dict]) -> float:
        """
        Score payment terms (max 20 points)
        
        Criteria:
        - Payment terms specified: 8 points
        - Payment schedule/due dates: 7 points
        - Payment methods: 3 points
        - Banking details: 2 points
        """
        if not payment:
            return 0.0
        
        score = 0.0
        
        # Payment terms (8 points)
        if payment.get('payment_terms'):
            score += 8
        
        # Payment schedule/due dates (7 points)
        schedules = payment.get('schedules', [])
        if schedules:
            schedule_score = min(len(schedules) * 2, 7)
            score += schedule_score
        elif payment.get('due_dates'):
            score += 5
        
        # Payment methods (3 points)
        if payment.get('methods'):
            score += 3
        
        # Banking details (2 points)
        if payment.get('banking_details'):
            score += 2
        
        return min(score, self.MAX_PAYMENT)
    
    def _score_sla(self, sla: Optional[Dict]) -> float:
        """
        Score SLA definition (max 15 points)
        
        Criteria:
        - Performance metrics: 6 points
        - Support terms: 4 points
        - Penalty clauses: 3 points
        - Response/resolution times: 2 points
        """
        if not sla:
            return 0.0
        
        score = 0.0
        
        # Performance metrics (6 points)
        metrics = sla.get('performance_metrics', [])
        if metrics:
            score += min(len(metrics) * 2, 6)
        
        # Support terms (4 points)
        if sla.get('support_terms'):
            score += 4
        
        # Penalty clauses (3 points)
        penalties = sla.get('penalty_clauses', [])
        if penalties:
            score += 3
        
        # Response/resolution times (2 points)
        if sla.get('response_time') or sla.get('resolution_time'):
            score += 2
        
        return min(score, self.MAX_SLA)
    
    def _score_contact(self, account_info: Optional[Dict]) -> float:
        """
        Score contact information (max 10 points)
        
        Criteria:
        - Billing contact: 4 points
        - Technical contact: 3 points
        - General contact info: 3 points
        """
        if not account_info:
            return 0.0
        
        score = 0.0
        
        # Billing contact (4 points)
        billing = account_info.get('billing_contact', {})
        if billing:
            if billing.get('email'):
                score += 2
            if billing.get('phone'):
                score += 2
        
        # Technical contact (3 points)
        technical = account_info.get('technical_contact', {})
        if technical:
            if technical.get('email'):
                score += 1.5
            if technical.get('phone'):
                score += 1.5
        
        # General contact (3 points)
        contact = account_info.get('contact_info', {})
        if contact:
            if contact.get('email'):
                score += 1.5
            if contact.get('phone'):
                score += 1.5
        
        return min(score, self.MAX_CONTACT)
    
    def _identify_missing_fields(self, contract_data: Dict[str, Any]) -> List[str]:
        """
        Identify critical missing fields
        
        Args:
            contract_data: Parsed contract data
            
        Returns:
            List of missing field descriptions
        """
        missing = []
        
        # Check financial details
        financial = contract_data.get('financial_details')
        if not financial:
            missing.append("Financial details section")
        else:
            if not financial.get('total_value'):
                missing.append("Total contract value")
            if not financial.get('currency'):
                missing.append("Currency")
            if not financial.get('line_items'):
                missing.append("Line items/services description")
        
        # Check parties
        customer = contract_data.get('customer')
        if not customer or not customer.get('name'):
            missing.append("Customer name")
        
        vendor = contract_data.get('vendor')
        if not vendor or not vendor.get('name'):
            missing.append("Vendor name")
        
        # Check payment terms
        payment = contract_data.get('payment_structure')
        if not payment:
            missing.append("Payment structure section")
        else:
            if not payment.get('payment_terms'):
                missing.append("Payment terms (e.g., Net 30)")
            if not payment.get('schedules') and not payment.get('due_dates'):
                missing.append("Payment schedule or due dates")
        
        # Check contact information
        account_info = contract_data.get('account_info')
        if not account_info:
            missing.append("Account/contact information")
        else:
            if not account_info.get('billing_contact'):
                missing.append("Billing contact information")
        
        # Check SLA (optional but valuable)
        if not contract_data.get('sla'):
            missing.append("Service Level Agreement (SLA)")
        
        return missing


# Global scoring service instance
scoring_service = ScoringService()
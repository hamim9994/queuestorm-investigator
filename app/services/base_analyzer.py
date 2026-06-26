from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from app.models.request import AnalyzeTicketRequest, TransactionHistoryEntry
from app.models.response import AnalyzeTicketResponse, EvidenceVerdict, CaseType, Department, Severity

class BaseAnalyzer(ABC):
    """Abstract base class for ticket analyzers"""
    
    @abstractmethod
    def analyze(self, request: AnalyzeTicketRequest) -> AnalyzeTicketResponse:
        """Analyze a ticket and return structured response"""
        pass
    
    def find_matching_transaction(self, complaint: str, history: List[TransactionHistoryEntry]) -> Optional[str]:
        """
        Find which transaction the complaint refers to
        Override this with ML-based matching
        """
        # Basic implementation - override with better logic
        for tx in history:
            if tx.transaction_id in complaint:
                return tx.transaction_id
            if str(tx.amount) in complaint:
                return tx.transaction_id
        return None
    
    def check_evidence_consistency(self, complaint: str, history: List[TransactionHistoryEntry], 
                                   selected_tx_id: Optional[str]) -> EvidenceVerdict:
        """
        Check if evidence supports the complaint
        Override with ML-based verification
        """
        if not selected_tx_id or not history:
            return EvidenceVerdict.INSUFFICIENT_DATA
        
        # Find the transaction
        selected_tx = None
        for tx in history:
            if tx.transaction_id == selected_tx_id:
                selected_tx = tx
                break
        
        if not selected_tx:
            return EvidenceVerdict.INSUFFICIENT_DATA
        
        # Basic consistency check - override with better logic
        # Check if complaint mentions amount that matches transaction
        amount_str = str(selected_tx.amount)
        if amount_str in complaint or str(int(selected_tx.amount)) in complaint:
            return EvidenceVerdict.CONSISTENT
        else:
            return EvidenceVerdict.INSUFFICIENT_DATA
    
    def classify_case_type(self, complaint: str, history: List[TransactionHistoryEntry],
                          selected_tx_id: Optional[str]) -> CaseType:
        """Classify the case type"""
        # Override with ML classification
        complaint_lower = complaint.lower()
        
        # Pattern matching - replace with ML
        if "wrong number" in complaint_lower or "wrong recipient" in complaint_lower:
            return CaseType.WRONG_TRANSFER
        elif "failed" in complaint_lower and "deduct" in complaint_lower:
            return CaseType.PAYMENT_FAILED
        elif "refund" in complaint_lower:
            return CaseType.REFUND_REQUEST
        elif "duplicate" in complaint_lower or "twice" in complaint_lower:
            return CaseType.DUPLICATE_PAYMENT
        elif "pin" in complaint_lower or "otp" in complaint_lower or "call" in complaint_lower:
            return CaseType.PHISHING_SOCIAL_ENGINEERING
        else:
            return CaseType.OTHER
    
    def determine_department(self, case_type: CaseType, severity: Severity) -> Department:
        """Determine which department handles this case"""
        mapping = {
            CaseType.WRONG_TRANSFER: Department.DISPUTE_RESOLUTION,
            CaseType.PAYMENT_FAILED: Department.PAYMENTS_OPS,
            CaseType.REFUND_REQUEST: Department.DISPUTE_RESOLUTION,
            CaseType.DUPLICATE_PAYMENT: Department.PAYMENTS_OPS,
            CaseType.MERCHANT_SETTLEMENT_DELAY: Department.MERCHANT_OPERATIONS,
            CaseType.AGENT_CASH_IN_ISSUE: Department.AGENT_OPERATIONS,
            CaseType.PHISHING_SOCIAL_ENGINEERING: Department.FRAUD_RISK,
            CaseType.OTHER: Department.CUSTOMER_SUPPORT
        }
        return mapping.get(case_type, Department.CUSTOMER_SUPPORT)
    
    def determine_severity(self, case_type: CaseType, amount: float) -> Severity:
        """Determine severity based on case type and amount"""
        HIGH_VALUE = 10000
        
        # Phishing is ALWAYS critical
        if case_type == CaseType.PHISHING_SOCIAL_ENGINEERING:
            return Severity.CRITICAL
        
        if amount >= HIGH_VALUE:
            return Severity.CRITICAL
        
        if case_type in [CaseType.DUPLICATE_PAYMENT]:
            return Severity.HIGH
        
        if case_type in [CaseType.WRONG_TRANSFER, CaseType.PAYMENT_FAILED]:
            if amount > 5000:
                return Severity.HIGH
            return Severity.MEDIUM
        
        return Severity.LOW
    
    def check_safety_rules(self, customer_reply: str) -> bool:
        """Check if customer reply violates safety rules"""
        forbidden = ["pin", "otp", "password", "mpin", "verification code"]
        lower_reply = customer_reply.lower()
        
        for word in forbidden:
            if word in lower_reply:
                return False
        
        # Check for unauthorized refund confirmation
        if "will refund" in lower_reply or "confirm refund" in lower_reply:
            return False
        
        return True
    
    def create_safe_customer_reply(self, case_type: CaseType, amount: float, 
                                   transaction_id: Optional[str]) -> str:
        """Create a safe customer reply that doesn't violate safety rules"""
        # Templates - override with LLM generation
        templates = {
            CaseType.WRONG_TRANSFER: f"We have noted your concern regarding transaction {transaction_id}. Our dispute resolution team will investigate this matter thoroughly. Any eligible amount will be returned through official channels once verification is complete. Please refrain from sharing any sensitive information.",
            
            CaseType.PAYMENT_FAILED: f"We understand you experienced an issue with your transaction. Our payments team will investigate the status of transaction {transaction_id}. If the amount was deducted incorrectly, it will be reversed through official channels. Please do not share your PIN or OTP with anyone.",
            
            CaseType.REFUND_REQUEST: f"We have received your refund request. Our team will review the transaction {transaction_id} and process any eligible refund through official channels. You will be notified once the review is complete.",
            
            CaseType.PHISHING_SOCIAL_ENGINEERING: "We have detected a potential security concern. Please do not share your PIN, OTP, or password with anyone. Our fraud prevention team will contact you through official channels. If you have already shared sensitive information, please report it immediately.",
            
            CaseType.OTHER: "We have received your query and our support team is investigating. Please note that we will never ask for your PIN, OTP, or password. Any resolution will be communicated through official channels."
        }
        
        return templates.get(case_type, templates[CaseType.OTHER])
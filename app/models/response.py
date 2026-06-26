from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class EvidenceVerdict(str, Enum):
    CONSISTENT = "consistent"
    INCONSISTENT = "inconsistent"
    INSUFFICIENT_DATA = "insufficient_data"

class CaseType(str, Enum):
    WRONG_TRANSFER = "wrong_transfer"
    PAYMENT_FAILED = "payment_failed"
    REFUND_REQUEST = "refund_request"
    DUPLICATE_PAYMENT = "duplicate_payment"
    MERCHANT_SETTLEMENT_DELAY = "merchant_settlement_delay"
    AGENT_CASH_IN_ISSUE = "agent_cash_in_issue"
    PHISHING_SOCIAL_ENGINEERING = "phishing_or_social_engineering"
    OTHER = "other"

class Department(str, Enum):
    CUSTOMER_SUPPORT = "customer_support"
    DISPUTE_RESOLUTION = "dispute_resolution"
    PAYMENTS_OPS = "payments_ops"
    MERCHANT_OPERATIONS = "merchant_operations"
    AGENT_OPERATIONS = "agent_operations"
    FRAUD_RISK = "fraud_risk"

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AnalyzeTicketResponse(BaseModel):
    ticket_id: str
    relevant_transaction_id: Optional[str] = None
    evidence_verdict: EvidenceVerdict
    case_type: CaseType
    severity: Severity
    department: Department
    agent_summary: str
    recommended_next_action: str
    customer_reply: str
    human_review_required: bool
    confidence: Optional[float] = Field(None, ge=0, le=1)
    reason_codes: Optional[List[str]] = Field(default=[])
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class TransactionHistoryEntry(BaseModel):
    transaction_id: str
    timestamp: str  # ISO 8601
    type: str  # transfer, payment, cash_in, cash_out, settlement, refund
    amount: float
    counterparty: str
    status: str  # completed, failed, pending, reversed

class AnalyzeTicketRequest(BaseModel):
    ticket_id: str = Field(..., description="Unique ticket identifier")
    complaint: str = Field(..., description="Customer complaint text")
    language: Optional[str] = Field(None, description="en, bn, or mixed")
    channel: Optional[str] = Field(None, description="in_app_chat, call_center, email, merchant_portal, field_agent")
    user_type: Optional[str] = Field(None, description="customer, merchant, agent, unknown")
    campaign_context: Optional[str] = Field(None, description="Campaign identifier")
    transaction_history: Optional[List[TransactionHistoryEntry]] = Field(default=[], description="Recent transactions")
    metadata: Optional[dict] = Field(default={}, description="Additional context")
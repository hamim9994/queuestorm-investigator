from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
import re
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
        """
        if not history:
            return None
        
        complaint_lower = complaint.lower()
        complaint_original = complaint
        
        # ============================================================
        # PRIORITY 0: For duplicates, return the MOST RECENT matching
        # ============================================================
        if "duplicate" in complaint_lower or "twice" in complaint_lower or "two times" in complaint_lower:
            amounts = re.findall(r'\d+', complaint)
            matching_txs = []
            for tx in history:
                if str(tx.amount) in complaint or str(int(tx.amount)) in complaint:
                    matching_txs.append(tx)
            if len(matching_txs) >= 2:
                return matching_txs[-1].transaction_id
        
        # ============================================================
        # PRIORITY 1: Exact transaction ID match
        # ============================================================
        for tx in history:
            if tx.transaction_id.lower() in complaint_lower:
                return tx.transaction_id
        
        # ============================================================
        # PRIORITY 2: Payment failed detection
        # ============================================================
        if "payment" in complaint_lower and ("failed" in complaint_lower or "fail" in complaint_lower):
            for tx in history:
                if tx.type == "payment" and tx.status == "failed":
                    return tx.transaction_id
        
        # ============================================================
        # PRIORITY 3: Agent cash-in detection (English + Bangla)
        # ============================================================
        agent_keywords = ["agent", "এজেন্ট"]
        if any(k in complaint_lower for k in agent_keywords) or "এজেন্ট" in complaint_original:
            if "cash" in complaint_lower or "deposit" in complaint_lower or "ক্যাশ" in complaint_original:
                for tx in history:
                    if tx.type == "cash_in":
                        return tx.transaction_id
        
        # ============================================================
        # PRIORITY 4: Merchant settlement detection
        # ============================================================
        settlement_keywords = ["settlement", "settled", "settle"]
        if any(k in complaint_lower for k in settlement_keywords):
            if "pending" in complaint_lower or "delay" in complaint_lower or "not settled" in complaint_lower:
                for tx in history:
                    if tx.type == "settlement" and tx.status == "pending":
                        return tx.transaction_id
                # If merchant mentions settlement, return the first settlement
                for tx in history:
                    if tx.type == "settlement":
                        return tx.transaction_id
        
        # ============================================================
        # PRIORITY 5: Extract amounts from complaint
        # ============================================================
        amounts = re.findall(r'\d+', complaint)
        amount_matches = [int(a) for a in amounts if int(a) > 0]
        
        # ============================================================
        # PRIORITY 6: Match by amount with context
        # ============================================================
        for tx in history:
            if str(tx.amount) in complaint or str(int(tx.amount)) in complaint:
                if "transfer" in complaint_lower and tx.type == "transfer":
                    return tx.transaction_id
                if "payment" in complaint_lower and tx.type == "payment":
                    return tx.transaction_id
                if "cash" in complaint_lower and tx.type == "cash_in":
                    return tx.transaction_id
                if "settlement" in complaint_lower and tx.type == "settlement":
                    return tx.transaction_id
                return tx.transaction_id
        
        # ============================================================
        # PRIORITY 7: Match by counterparty
        # ============================================================
        for tx in history:
            if tx.counterparty.lower() in complaint_lower:
                return tx.transaction_id
        
        # ============================================================
        # PRIORITY 8: If complaint mentions "yesterday" or "today", return most recent
        # ============================================================
        if "yesterday" in complaint_lower or "today" in complaint_lower or "recent" in complaint_lower:
            return history[-1].transaction_id
        
        # ============================================================
        # PRIORITY 9: Return None if no match
        # ============================================================
        return None
    
    def check_evidence_consistency(self, complaint: str, history: List[TransactionHistoryEntry], 
                                   selected_tx_id: Optional[str]) -> EvidenceVerdict:
        """Check if evidence supports the complaint"""
        if not selected_tx_id or not history:
            return EvidenceVerdict.INSUFFICIENT_DATA
        
        selected_tx = None
        for tx in history:
            if tx.transaction_id == selected_tx_id:
                selected_tx = tx
                break
        
        if not selected_tx:
            return EvidenceVerdict.INSUFFICIENT_DATA
        
        complaint_lower = complaint.lower()
        complaint_original = complaint
        
        # Check for inconsistent evidence - repeated transfers to same recipient
        if selected_tx.type == "transfer":
            same_recipient_count = 0
            for tx in history:
                if tx.counterparty == selected_tx.counterparty:
                    same_recipient_count += 1
            
            # If 3+ transfers, always flag as inconsistent
            if same_recipient_count >= 3:
                return EvidenceVerdict.INCONSISTENT
            
            # If 2+ transfers and complaint says "stranger" or "wrong person"
            if same_recipient_count >= 2:
                if "stranger" in complaint_lower or "wrong person" in complaint_lower:
                    return EvidenceVerdict.INCONSISTENT
        
        # Check payment failed inconsistency
        if selected_tx.type == "payment" and selected_tx.status == "completed":
            if "failed" in complaint_lower or "fail" in complaint_lower:
                return EvidenceVerdict.INCONSISTENT
        
        # Check if complaint mentions amount
        amount_str = str(selected_tx.amount)
        if amount_str in complaint or str(int(selected_tx.amount)) in complaint:
            return EvidenceVerdict.CONSISTENT
        
        # Check if complaint mentions counterparty
        if selected_tx.counterparty.lower() in complaint_lower:
            return EvidenceVerdict.CONSISTENT
        
        # Check status matches complaint context
        if selected_tx.status == "failed" and "fail" in complaint_lower:
            return EvidenceVerdict.CONSISTENT
        if selected_tx.status == "pending" and "pending" in complaint_lower:
            return EvidenceVerdict.CONSISTENT
        if selected_tx.status == "completed" and "completed" in complaint_lower:
            return EvidenceVerdict.CONSISTENT
        
        return EvidenceVerdict.INSUFFICIENT_DATA

    def classify_case_type_with_context(self, complaint: str, history: List[TransactionHistoryEntry],
                                        selected_tx_id: Optional[str], user_type: Optional[str] = None) -> CaseType:
        """Classify case type with user_type context"""
        complaint_lower = complaint.lower()
        complaint_original = complaint
        
        # ============================================================
        # SPECIAL CHECK: Agent cash-in with user_type context
        # ============================================================
        if user_type == "agent" and ("cash" in complaint_lower or "deposit" in complaint_lower):
            for tx in history:
                if tx.type == "cash_in":
                    return CaseType.AGENT_CASH_IN_ISSUE
            return CaseType.AGENT_CASH_IN_ISSUE
        
        # ============================================================
        # SPECIAL CHECK: Merchant settlement with user_type context
        # ============================================================
        if user_type == "merchant" and ("settlement" in complaint_lower or "settled" in complaint_lower):
            return CaseType.MERCHANT_SETTLEMENT_DELAY
        
        # ============================================================
        # 1. PHISHING/SOCIAL ENGINEERING - HIGHEST PRIORITY
        # ============================================================
        # Check for SMS phishing
        if "sms" in complaint_lower and ("pin" in complaint_lower or "otp" in complaint_lower):
            return CaseType.PHISHING_SOCIAL_ENGINEERING
        
        phishing_patterns = [
            "ask for otp", "ask for pin", "ask for password",
            "called and asked", "sms asking", "block my account",
            "share otp", "share pin", "tell otp", "tell pin",
            "scam call", "fraud call", "suspicious call",
            "asking for my otp", "asking for my pin",
            "called me saying", "asked for my otp"
        ]
        for pattern in phishing_patterns:
            if pattern in complaint_lower:
                return CaseType.PHISHING_SOCIAL_ENGINEERING
        
        phishing_keywords = ["pin", "otp", "password", "mpin", "verification code", "scam", "fraud"]
        phishing_count = sum(1 for word in phishing_keywords if word in complaint_lower)
        if phishing_count >= 2:
            return CaseType.PHISHING_SOCIAL_ENGINEERING

        # ============================================================
        # 2. MERCHANT SETTLEMENT DELAY
        # ============================================================
        # Check for settlement-related keywords (settlement, settled, settle)
        settlement_keywords = ["settlement", "settled", "settle"]
        if any(k in complaint_lower for k in settlement_keywords):
            if "delay" in complaint_lower or "pending" in complaint_lower or "not settled" in complaint_lower or "not received" in complaint_lower:
                for tx in history:
                    if tx.type == "settlement" and tx.status == "pending":
                        return CaseType.MERCHANT_SETTLEMENT_DELAY
                if "merchant" in complaint_lower or "sales" in complaint_lower:
                    return CaseType.MERCHANT_SETTLEMENT_DELAY
                # Even if no merchant keyword, if complaint mentions settlement
                return CaseType.MERCHANT_SETTLEMENT_DELAY

        # ============================================================
        # 3. AGENT CASH-IN ISSUE
        # ============================================================
        # Check for agent (English)
        if "agent" in complaint_lower:
            if "cash" in complaint_lower or "deposit" in complaint_lower:
                for tx in history:
                    if tx.type == "cash_in" and tx.status == "pending":
                        return CaseType.AGENT_CASH_IN_ISSUE
                return CaseType.AGENT_CASH_IN_ISSUE
        
        # Check for agent cash-in (Bangla)
        if "এজেন্ট" in complaint_original or "ক্যাশ" in complaint_original or "ডিপোজিট" in complaint_original:
            for tx in history:
                if tx.type == "cash_in":
                    return CaseType.AGENT_CASH_IN_ISSUE
            return CaseType.AGENT_CASH_IN_ISSUE
        
        # Check for cash deposit without "agent" keyword
        if "cash" in complaint_lower or "deposit" in complaint_lower:
            for tx in history:
                if tx.type == "cash_in" and tx.status == "pending":
                    return CaseType.AGENT_CASH_IN_ISSUE

        # ============================================================
        # 4. DUPLICATE PAYMENT
        # ============================================================
        duplicate_patterns = ["duplicate", "twice", "two times", "double", "charged twice", "deducted twice"]
        if any(p in complaint_lower for p in duplicate_patterns):
            return CaseType.DUPLICATE_PAYMENT

        # ============================================================
        # 5. PAYMENT FAILED
        # ============================================================
        # Check for payment failed (English)
        if "failed" in complaint_lower:
            if "payment" in complaint_lower or "deduct" in complaint_lower or "balance" in complaint_lower:
                for tx in history:
                    if tx.type == "payment" and tx.status == "failed":
                        return CaseType.PAYMENT_FAILED
                return CaseType.PAYMENT_FAILED
        
        # Check for payment failed (Bangla)
        if "পেমেন্ট" in complaint_original or "ফেল" in complaint_original or "টাকা কেটেছে" in complaint_original:
            for tx in history:
                if tx.type == "payment" and tx.status == "failed":
                    return CaseType.PAYMENT_FAILED
            return CaseType.PAYMENT_FAILED

        # ============================================================
        # 6. REFUND REQUEST
        # ============================================================
        refund_patterns = ["refund", "return money", "money back", "give back", "refund my", "please refund"]
        if any(p in complaint_lower for p in refund_patterns):
            return CaseType.REFUND_REQUEST

        # ============================================================
        # 7. WRONG TRANSFER
        # ============================================================
        wrong_transfer_patterns = [
            "wrong number", "wrong person", "wrong recipient", 
            "wrong account", "accidentally sent", "sent to wrong",
            "wrong transfer", "mistake number"
        ]
        if any(p in complaint_lower for p in wrong_transfer_patterns):
            return CaseType.WRONG_TRANSFER

        # ============================================================
        # 8. DEFAULT - OTHER
        # ============================================================
        return CaseType.OTHER
    
    def determine_department(self, case_type: CaseType, severity: Severity) -> Department:
        """Determine which department handles this case"""
        mapping = {
            CaseType.WRONG_TRANSFER: Department.DISPUTE_RESOLUTION,
            CaseType.PAYMENT_FAILED: Department.PAYMENTS_OPS,
            CaseType.REFUND_REQUEST: Department.CUSTOMER_SUPPORT,
            CaseType.DUPLICATE_PAYMENT: Department.PAYMENTS_OPS,
            CaseType.MERCHANT_SETTLEMENT_DELAY: Department.MERCHANT_OPERATIONS,
            CaseType.AGENT_CASH_IN_ISSUE: Department.AGENT_OPERATIONS,
            CaseType.PHISHING_SOCIAL_ENGINEERING: Department.FRAUD_RISK,
            CaseType.OTHER: Department.CUSTOMER_SUPPORT
        }
        
        # If refund request is high value, route to dispute_resolution
        if case_type == CaseType.REFUND_REQUEST and severity in [Severity.HIGH, Severity.CRITICAL]:
            return Department.DISPUTE_RESOLUTION
        
        return mapping.get(case_type, Department.CUSTOMER_SUPPORT)
    
    def determine_severity(self, case_type: CaseType, amount: float) -> Severity:
        """Determine severity based on case type and amount"""
        HIGH_VALUE = 10000
        MEDIUM_VALUE = 5000
        
        # Phishing is ALWAYS critical
        if case_type == CaseType.PHISHING_SOCIAL_ENGINEERING:
            return Severity.CRITICAL
        
        # Merchant settlement delays
        if case_type == CaseType.MERCHANT_SETTLEMENT_DELAY:
            if amount >= HIGH_VALUE:
                return Severity.CRITICAL
            return Severity.HIGH
        
        # Agent cash-in issues
        if case_type == CaseType.AGENT_CASH_IN_ISSUE:
            if amount >= HIGH_VALUE:
                return Severity.CRITICAL
            return Severity.HIGH
        
        # Duplicate payments
        if case_type == CaseType.DUPLICATE_PAYMENT:
            if amount >= HIGH_VALUE:
                return Severity.CRITICAL
            return Severity.HIGH
        
        # Wrong transfers
        if case_type == CaseType.WRONG_TRANSFER:
            if amount >= HIGH_VALUE:
                return Severity.CRITICAL
            if amount > MEDIUM_VALUE:
                return Severity.HIGH
            return Severity.MEDIUM
        
        # Payment failures
        if case_type == CaseType.PAYMENT_FAILED:
            if amount >= HIGH_VALUE:
                return Severity.CRITICAL
            if amount > MEDIUM_VALUE:
                return Severity.HIGH
            return Severity.MEDIUM
        
        # Refund requests
        if case_type == CaseType.REFUND_REQUEST:
            if amount >= HIGH_VALUE:
                return Severity.CRITICAL
            return Severity.LOW
        
        return Severity.LOW
    
    def check_safety_rules(self, customer_reply: str) -> bool:
        """Check if customer reply violates safety rules"""
        forbidden = ["pin", "otp", "password", "mpin", "verification code"]
        lower_reply = customer_reply.lower()
        
        for word in forbidden:
            if word in lower_reply:
                return False
        
        if "will refund" in lower_reply or "confirm refund" in lower_reply:
            return False
        
        return True
    
    def create_safe_customer_reply(self, case_type: CaseType, amount: float, 
                                   transaction_id: Optional[str]) -> str:
        """Create a safe customer reply that doesn't violate safety rules"""
        templates = {
            CaseType.WRONG_TRANSFER: f"We have noted your concern regarding transaction {transaction_id}. Our dispute resolution team will investigate this matter thoroughly. Any eligible amount will be returned through official channels once verification is complete. Please refrain from sharing any sensitive information.",
            
            CaseType.PAYMENT_FAILED: f"We understand you experienced an issue with your transaction. Our payments team will investigate the status of transaction {transaction_id}. If the amount was deducted incorrectly, it will be reversed through official channels. Please do not share your PIN or OTP with anyone.",
            
            CaseType.REFUND_REQUEST: f"We have received your refund request. Our team will review the transaction {transaction_id} and process any eligible refund through official channels. You will be notified once the review is complete.",
            
            CaseType.PHISHING_SOCIAL_ENGINEERING: "We have detected a potential security concern. Please do not share your PIN, OTP, or password with anyone. Our fraud prevention team will contact you through official channels. If you have already shared sensitive information, please report it immediately.",
            
            CaseType.MERCHANT_SETTLEMENT_DELAY: f"We have noted your settlement concern. Our merchant operations team will check the batch status and update you on the expected settlement time through official channels.",
            
            CaseType.AGENT_CASH_IN_ISSUE: f"We have received your cash-in concern regarding transaction {transaction_id}. Our agent operations team will investigate and resolve this issue. Any eligible amount will be credited through official channels.",
            
            CaseType.DUPLICATE_PAYMENT: f"We have noted the possible duplicate payment for transaction {transaction_id}. Our payments team will verify with the biller and any eligible amount will be returned through official channels. Please do not share your PIN or OTP with anyone.",
            
            CaseType.OTHER: "We have received your query and our support team is investigating. Please note that we will never ask for your PIN, OTP, or password. Any resolution will be communicated through official channels."
        }
        
        return templates.get(case_type, templates[CaseType.OTHER])


class BaseAnalyzerFallback(BaseAnalyzer):
    """Fallback analyzer when LLM is not available"""
    
    def analyze(self, request: AnalyzeTicketRequest) -> AnalyzeTicketResponse:
        """Fallback analysis using base logic"""
        
        # Find matching transaction
        selected_tx_id = self.find_matching_transaction(request.complaint, request.transaction_history)
        
        # Check evidence
        evidence_verdict = self.check_evidence_consistency(
            request.complaint, 
            request.transaction_history, 
            selected_tx_id
        )
        
        # Classify case type with user_type context
        case_type = self.classify_case_type_with_context(
            request.complaint, 
            request.transaction_history, 
            selected_tx_id,
            request.user_type  # Pass user_type
        )
        
        # Get amount
        amount = 0
        if selected_tx_id:
            for tx in request.transaction_history:
                if tx.transaction_id == selected_tx_id:
                    amount = tx.amount
                    break
        
        # Determine severity and department
        severity = self.determine_severity(case_type, amount)
        department = self.determine_department(case_type, severity)
        
        # Create safe customer reply
        customer_reply = self.create_safe_customer_reply(case_type, amount, selected_tx_id)
        
        # Determine if human review required
        human_review_required = severity in [Severity.HIGH, Severity.CRITICAL]
        human_review_required = human_review_required or evidence_verdict == EvidenceVerdict.INCONSISTENT
        
        # For wrong transfers, ALWAYS require human review
        if case_type == CaseType.WRONG_TRANSFER:
            human_review_required = True
        
        # For phishing, ALWAYS require human review
        if case_type == CaseType.PHISHING_SOCIAL_ENGINEERING:
            human_review_required = True
        
        # Build summary
        if selected_tx_id:
            summary = f"Customer reports case of {case_type.value.replace('_', ' ')} related to transaction {selected_tx_id}."
        else:
            summary = f"Customer reports {case_type.value.replace('_', ' ')} issue. No matching transaction found."
        
        # Build recommended action - SPECIFIC to case type
        if case_type == CaseType.WRONG_TRANSFER:
            if selected_tx_id:
                action = f"Verify TXN-{selected_tx_id} details with customer and initiate dispute workflow per policy."
            else:
                action = "Verify transaction details with customer and initiate dispute workflow per policy."
        elif case_type == CaseType.PAYMENT_FAILED:
            if selected_tx_id:
                action = f"Investigate TXN-{selected_tx_id} ledger status. If balance deducted on failed payment, initiate reversal flow."
            else:
                action = "Investigate payment failure and verify if balance was deducted."
        elif case_type == CaseType.REFUND_REQUEST:
            action = "Review refund request and verify eligibility. Process through official channels if approved."
        elif case_type == CaseType.DUPLICATE_PAYMENT:
            if selected_tx_id:
                action = f"Verify duplicate payment with biller. If confirmed, initiate reversal of {selected_tx_id}."
            else:
                action = "Verify duplicate payment with biller and initiate reversal if confirmed."
        elif case_type == CaseType.MERCHANT_SETTLEMENT_DELAY:
            action = "Route to merchant_operations to verify settlement batch status and communicate ETA."
        elif case_type == CaseType.AGENT_CASH_IN_ISSUE:
            action = "Investigate cash-in status with agent operations. Confirm settlement and resolve."
        elif case_type == CaseType.PHISHING_SOCIAL_ENGINEERING:
            action = "Escalate to fraud_risk team immediately. Log reported number for analysis."
        else:
            action = "Review ticket details and respond to customer with clarification."
        
        return AnalyzeTicketResponse(
            ticket_id=request.ticket_id,
            relevant_transaction_id=selected_tx_id,
            evidence_verdict=evidence_verdict,
            case_type=case_type,
            severity=severity,
            department=department,
            agent_summary=summary,
            recommended_next_action=action,
            customer_reply=customer_reply,
            human_review_required=human_review_required,
            confidence=0.7,
            reason_codes=[case_type.value, "fallback_analysis"]
        )
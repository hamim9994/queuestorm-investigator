# tests/test_cases_100.py
"""
100+ Test Cases for QueueStorm Investigator
Covers: Normal cases, Edge cases, Safety rules, 
Bangla/English/Mixed language, Different user types,
Various case types, and Stress tests.
"""

import unittest
import json
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.main import app

class TestQueueStorm100(unittest.TestCase):
    """100+ Test Cases for QueueStorm Investigator"""
    
    def setUp(self):
        self.client = TestClient(app)
        
        # Common test data
        self.base_request = {
            "ticket_id": "TKT-000",
            "complaint": "Test complaint",
            "language": "en",
            "channel": "in_app_chat",
            "user_type": "customer",
            "campaign_context": "test_campaign",
            "transaction_history": []
        }
    
    # ============================================================
    # SECTION 1: WRONG TRANSFER CASES (1-15)
    # ============================================================
    
    def test_01_wrong_transfer_simple(self):
        """Simple wrong transfer with matching transaction"""
        request = {
            "ticket_id": "TKT-001",
            "complaint": "I sent 5000 taka to the wrong number. Please help.",
            "transaction_history": [
                {"transaction_id": "TXN-001", "timestamp": "2026-04-14T10:00:00Z", 
                 "type": "transfer", "amount": 5000, "counterparty": "+8801712345678", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["case_type"], "wrong_transfer")
        self.assertEqual(data["relevant_transaction_id"], "TXN-001")
    
    def test_02_wrong_transfer_large_amount(self):
        """Wrong transfer with large amount (>10000)"""
        request = {
            "ticket_id": "TKT-002",
            "complaint": "I accidentally sent 50000 to the wrong person!",
            "transaction_history": [
                {"transaction_id": "TXN-002", "timestamp": "2026-04-14T11:00:00Z", 
                 "type": "transfer", "amount": 50000, "counterparty": "+8801712345679", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["severity"], "critical")
        self.assertTrue(data["human_review_required"])
    
    def test_03_wrong_transfer_multiple_transactions(self):
        """Wrong transfer with multiple transactions"""
        request = {
            "ticket_id": "TKT-003",
            "complaint": "I sent 2000 to the wrong person today morning",
            "transaction_history": [
                {"transaction_id": "TXN-003", "timestamp": "2026-04-14T08:00:00Z", 
                 "type": "transfer", "amount": 2000, "counterparty": "+8801712345680", "status": "completed"},
                {"transaction_id": "TXN-004", "timestamp": "2026-04-14T09:00:00Z", 
                 "type": "transfer", "amount": 500, "counterparty": "+8801712345681", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["case_type"], "wrong_transfer")
    
    def test_04_wrong_transfer_inconsistent_evidence(self):
        """Wrong transfer claim with inconsistent evidence"""
        request = {
            "ticket_id": "TKT-004",
            "complaint": "I sent 3000 to a stranger by mistake",
            "transaction_history": [
                {"transaction_id": "TXN-005", "timestamp": "2026-04-10T10:00:00Z", 
                 "type": "transfer", "amount": 3000, "counterparty": "+8801712345682", "status": "completed"},
                {"transaction_id": "TXN-006", "timestamp": "2026-04-08T10:00:00Z", 
                 "type": "transfer", "amount": 3000, "counterparty": "+8801712345682", "status": "completed"},
                {"transaction_id": "TXN-007", "timestamp": "2026-04-05T10:00:00Z", 
                 "type": "transfer", "amount": 3000, "counterparty": "+8801712345682", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should flag as inconsistent due to repeated transfers to same number
        self.assertIn(data["evidence_verdict"], ["inconsistent", "insufficient_data"])
    
    def test_05_wrong_transfer_no_transaction(self):
        """Wrong transfer claim with no matching transaction"""
        request = {
            "ticket_id": "TKT-005",
            "complaint": "I sent money to the wrong person",
            "transaction_history": []
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["evidence_verdict"], "insufficient_data")
        self.assertIsNone(data["relevant_transaction_id"])
    
    def test_06_wrong_transfer_bangla(self):
        """Wrong transfer in Bangla"""
        request = {
            "ticket_id": "TKT-006",
            "complaint": "আমি ভুল নম্বরে ১০০০ টাকা পাঠিয়ে দিয়েছি",
            "language": "bn",
            "transaction_history": [
                {"transaction_id": "TXN-008", "timestamp": "2026-04-14T12:00:00Z", 
                 "type": "transfer", "amount": 1000, "counterparty": "+8801712345683", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["case_type"], "wrong_transfer")
    
    def test_07_wrong_transfer_merchant_recipient(self):
        """Wrong transfer to merchant"""
        request = {
            "ticket_id": "TKT-007",
            "complaint": "I paid the wrong merchant by mistake",
            "transaction_history": [
                {"transaction_id": "TXN-009", "timestamp": "2026-04-14T13:00:00Z", 
                 "type": "payment", "amount": 1500, "counterparty": "MERCHANT-123", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["case_type"], "wrong_transfer")
    
    def test_08_wrong_transfer_agent(self):
        """Wrong transfer involving agent"""
        request = {
            "ticket_id": "TKT-008",
            "complaint": "Agent sent money to wrong account",
            "user_type": "agent",
            "transaction_history": [
                {"transaction_id": "TXN-010", "timestamp": "2026-04-14T14:00:00Z", 
                 "type": "transfer", "amount": 2500, "counterparty": "AGENT-456", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user_type"], "agent")
    
    def test_09_wrong_transfer_different_amounts(self):
        """Wrong transfer with different amounts in history"""
        request = {
            "ticket_id": "TKT-009",
            "complaint": "I sent 750 to wrong number",
            "transaction_history": [
                {"transaction_id": "TXN-011", "timestamp": "2026-04-14T15:00:00Z", 
                 "type": "transfer", "amount": 1000, "counterparty": "+8801712345684", "status": "completed"},
                {"transaction_id": "TXN-012", "timestamp": "2026-04-14T16:00:00Z", 
                 "type": "transfer", "amount": 750, "counterparty": "+8801712345685", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["relevant_transaction_id"], "TXN-012")
    
    def test_10_wrong_transfer_failed_status(self):
        """Wrong transfer with failed status"""
        request = {
            "ticket_id": "TKT-010",
            "complaint": "I think I sent money to wrong person",
            "transaction_history": [
                {"transaction_id": "TXN-013", "timestamp": "2026-04-14T17:00:00Z", 
                 "type": "transfer", "amount": 500, "counterparty": "+8801712345686", "status": "failed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should still handle wrong transfer even if failed
        self.assertIn(data["case_type"], ["wrong_transfer", "other"])
    
    def test_11_wrong_transfer_pending_status(self):
        """Wrong transfer with pending status"""
        request = {
            "ticket_id": "TKT-011",
            "complaint": "I sent money to wrong number, please stop it",
            "transaction_history": [
                {"transaction_id": "TXN-014", "timestamp": "2026-04-14T18:00:00Z", 
                 "type": "transfer", "amount": 2000, "counterparty": "+8801712345687", "status": "pending"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Pending status should be noted
        self.assertIn(data["evidence_verdict"], ["consistent", "insufficient_data"])
    
    def test_12_wrong_transfer_call_center(self):
        """Wrong transfer via call center channel"""
        request = {
            "ticket_id": "TKT-012",
            "complaint": "I called earlier about wrong transfer",
            "channel": "call_center",
            "transaction_history": [
                {"transaction_id": "TXN-015", "timestamp": "2026-04-14T19:00:00Z", 
                 "type": "transfer", "amount": 3000, "counterparty": "+8801712345688", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["channel"], "call_center")
    
    def test_13_wrong_transfer_email_channel(self):
        """Wrong transfer via email"""
        request = {
            "ticket_id": "TKT-013",
            "complaint": "I emailed about wrong transfer",
            "channel": "email",
            "transaction_history": [
                {"transaction_id": "TXN-016", "timestamp": "2026-04-14T20:00:00Z", 
                 "type": "transfer", "amount": 4000, "counterparty": "+8801712345689", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["channel"], "email")
    
    def test_14_wrong_transfer_mixed_language(self):
        """Wrong transfer with mixed Bangla/English"""
        request = {
            "ticket_id": "TKT-014",
            "complaint": "I sent 500 taka to wrong number yesterday ami vule pathaisi",
            "language": "mixed",
            "transaction_history": [
                {"transaction_id": "TXN-017", "timestamp": "2026-04-13T21:00:00Z", 
                 "type": "transfer", "amount": 500, "counterparty": "+8801712345690", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["case_type"], "wrong_transfer")
    
    def test_15_wrong_transfer_with_campaign_context(self):
        """Wrong transfer with campaign context"""
        request = {
            "ticket_id": "TKT-015",
            "complaint": "I sent money to wrong person during the campaign",
            "campaign_context": "boishakh_bonanza",
            "transaction_history": [
                {"transaction_id": "TXN-018", "timestamp": "2026-04-14T22:00:00Z", 
                 "type": "transfer", "amount": 1000, "counterparty": "+8801712345691", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["campaign_context"], "boishakh_bonanza")

    # ============================================================
    # SECTION 2: PAYMENT FAILED CASES (16-30)
    # ============================================================
    
    def test_16_payment_failed_simple(self):
        """Simple payment failed with balance deduction"""
        request = {
            "ticket_id": "TKT-016",
            "complaint": "My payment failed but money deducted from balance",
            "transaction_history": [
                {"transaction_id": "TXN-019", "timestamp": "2026-04-14T10:00:00Z", 
                 "type": "payment", "amount": 500, "counterparty": "MERCHANT-001", "status": "failed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["case_type"], "payment_failed")
        self.assertEqual(data["department"], "payments_ops")
    
    def test_17_payment_failed_large_amount(self):
        """Payment failed with large amount"""
        request = {
            "ticket_id": "TKT-017",
            "complaint": "Failed payment of 25000, balance deducted",
            "transaction_history": [
                {"transaction_id": "TXN-020", "timestamp": "2026-04-14T11:00:00Z", 
                 "type": "payment", "amount": 25000, "counterparty": "MERCHANT-002", "status": "failed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["severity"], "critical")
    
    def test_18_payment_failed_merchant_portal(self):
        """Payment failed via merchant portal"""
        request = {
            "ticket_id": "TKT-018",
            "complaint": "Payment failed for our store",
            "channel": "merchant_portal",
            "user_type": "merchant",
            "transaction_history": [
                {"transaction_id": "TXN-021", "timestamp": "2026-04-14T12:00:00Z", 
                 "type": "payment", "amount": 1000, "counterparty": "MERCHANT-003", "status": "failed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user_type"], "merchant")
    
    def test_19_payment_failed_multiple(self):
        """Multiple payment failures"""
        request = {
            "ticket_id": "TKT-019",
            "complaint": "Multiple payments failed today",
            "transaction_history": [
                {"transaction_id": "TXN-022", "timestamp": "2026-04-14T13:00:00Z", 
                 "type": "payment", "amount": 200, "counterparty": "MERCHANT-004", "status": "failed"},
                {"transaction_id": "TXN-023", "timestamp": "2026-04-14T13:05:00Z", 
                 "type": "payment", "amount": 200, "counterparty": "MERCHANT-004", "status": "failed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["case_type"], "payment_failed")
    
    def test_20_payment_failed_bangla(self):
        """Payment failed complaint in Bangla"""
        request = {
            "ticket_id": "TKT-020",
            "complaint": "পেমেন্ট ফেল হয়েছে কিন্তু টাকা কেটেছে",
            "language": "bn",
            "transaction_history": [
                {"transaction_id": "TXN-024", "timestamp": "2026-04-14T14:00:00Z", 
                 "type": "payment", "amount": 300, "counterparty": "MERCHANT-005", "status": "failed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["case_type"], "payment_failed")
    
    def test_21_payment_failed_no_transaction(self):
        """Payment failed complaint with no matching transaction"""
        request = {
            "ticket_id": "TKT-021",
            "complaint": "My payment failed and balance is wrong",
            "transaction_history": []
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["evidence_verdict"], "insufficient_data")
    
    def test_22_payment_failed_inconsistent(self):
        """Payment failed with inconsistent evidence"""
        request = {
            "ticket_id": "TKT-022",
            "complaint": "Payment failed yesterday",
            "transaction_history": [
                {"transaction_id": "TXN-025", "timestamp": "2026-04-13T15:00:00Z", 
                 "type": "payment", "amount": 100, "counterparty": "MERCHANT-006", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should flag as inconsistent since transaction is completed
        self.assertIn(data["evidence_verdict"], ["inconsistent", "insufficient_data"])
    
    def test_23_payment_failed_pending_status(self):
        """Payment failed with pending status"""
        request = {
            "ticket_id": "TKT-023",
            "complaint": "Payment is stuck, money gone",
            "transaction_history": [
                {"transaction_id": "TXN-026", "timestamp": "2026-04-14T16:00:00Z", 
                 "type": "payment", "amount": 450, "counterparty": "MERCHANT-007", "status": "pending"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["case_type"], ["payment_failed", "other"])
    
    def test_24_payment_failed_agent_cash_in(self):
        """Payment failed for agent cash-in"""
        request = {
            "ticket_id": "TKT-024",
            "complaint": "Agent cash-in failed but money deducted",
            "user_type": "agent",
            "transaction_history": [
                {"transaction_id": "TXN-027", "timestamp": "2026-04-14T17:00:00Z", 
                 "type": "cash_in", "amount": 5000, "counterparty": "AGENT-001", "status": "failed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["case_type"], "agent_cash_in_issue")
    
    def test_25_payment_failed_unknown_user(self):
        """Payment failed with unknown user type"""
        request = {
            "ticket_id": "TKT-025",
            "complaint": "Payment failed for my account",
            "user_type": "unknown",
            "transaction_history": [
                {"transaction_id": "TXN-028", "timestamp": "2026-04-14T18:00:00Z", 
                 "type": "payment", "amount": 600, "counterparty": "MERCHANT-008", "status": "failed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user_type"], "unknown")
    
    def test_26_payment_failed_mixed_banglish(self):
        """Payment failed in mixed Banglish"""
        request = {
            "ticket_id": "TKT-026",
            "complaint": "Payment failed but balance komse",
            "language": "mixed",
            "transaction_history": [
                {"transaction_id": "TXN-029", "timestamp": "2026-04-14T19:00:00Z", 
                 "type": "payment", "amount": 800, "counterparty": "MERCHANT-009", "status": "failed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["case_type"], "payment_failed")
    
    def test_27_payment_failed_merchant_operations(self):
        """Payment failed should route to payments_ops"""
        request = {
            "ticket_id": "TKT-027",
            "complaint": "Payment failed, need help",
            "transaction_history": [
                {"transaction_id": "TXN-030", "timestamp": "2026-04-14T20:00:00Z", 
                 "type": "payment", "amount": 1200, "counterparty": "MERCHANT-010", "status": "failed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["department"], "payments_ops")
    
    def test_28_payment_failed_high_value(self):
        """Payment failed with high value triggers critical"""
        request = {
            "ticket_id": "TKT-028",
            "complaint": "Failed payment of 15000 for business",
            "transaction_history": [
                {"transaction_id": "TXN-031", "timestamp": "2026-04-14T21:00:00Z", 
                 "type": "payment", "amount": 15000, "counterparty": "MERCHANT-011", "status": "failed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["severity"], "critical")
        self.assertTrue(data["human_review_required"])
    
    def test_29_payment_failed_duplicate(self):
        """Payment failed with duplicate entries"""
        request = {
            "ticket_id": "TKT-029",
            "complaint": "Same payment failed twice",
            "transaction_history": [
                {"transaction_id": "TXN-032", "timestamp": "2026-04-14T22:00:00Z", 
                 "type": "payment", "amount": 500, "counterparty": "MERCHANT-012", "status": "failed"},
                {"transaction_id": "TXN-033", "timestamp": "2026-04-14T22:01:00Z", 
                 "type": "payment", "amount": 500, "counterparty": "MERCHANT-012", "status": "failed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["case_type"], "duplicate_payment")
    
    def test_30_payment_failed_in_app_chat(self):
        """Payment failed via in-app chat"""
        request = {
            "ticket_id": "TKT-030",
            "complaint": "Payment failed in app",
            "channel": "in_app_chat",
            "transaction_history": [
                {"transaction_id": "TXN-034", "timestamp": "2026-04-14T23:00:00Z", 
                 "type": "payment", "amount": 350, "counterparty": "MERCHANT-013", "status": "failed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["channel"], "in_app_chat")

    # ============================================================
    # SECTION 3: REFUND REQUEST CASES (31-45)
    # ============================================================
    
    def test_31_refund_request_simple(self):
        """Simple refund request"""
        request = {
            "ticket_id": "TKT-031",
            "complaint": "Please refund my 1000 taka payment",
            "transaction_history": [
                {"transaction_id": "TXN-035", "timestamp": "2026-04-14T10:00:00Z", 
                 "type": "payment", "amount": 1000, "counterparty": "MERCHANT-014", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["case_type"], "refund_request")
        self.assertEqual(data["department"], "customer_support")
    
    def test_32_refund_request_safety_no_refund_promise(self):
        """Refund request - should NOT promise refund"""
        request = {
            "ticket_id": "TKT-032",
            "complaint": "Refund my money please",
            "transaction_history": [
                {"transaction_id": "TXN-036", "timestamp": "2026-04-14T11:00:00Z", 
                 "type": "payment", "amount": 500, "counterparty": "MERCHANT-015", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        reply = data["customer_reply"].lower()
        self.assertNotIn("will refund", reply)
        self.assertNotIn("confirm refund", reply)
    
    def test_33_refund_request_bangla(self):
        """Refund request in Bangla"""
        request = {
            "ticket_id": "TKT-033",
            "complaint": "আমার ২০০০ টাকা রিফান্ড করুন",
            "language": "bn",
            "transaction_history": [
                {"transaction_id": "TXN-037", "timestamp": "2026-04-14T12:00:00Z", 
                 "type": "payment", "amount": 2000, "counterparty": "MERCHANT-016", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["case_type"], "refund_request")
    
    def test_34_refund_request_merchant(self):
        """Refund request from merchant"""
        request = {
            "ticket_id": "TKT-034",
            "complaint": "Need refund for customer payment",
            "user_type": "merchant",
            "transaction_history": [
                {"transaction_id": "TXN-038", "timestamp": "2026-04-14T13:00:00Z", 
                 "type": "payment", "amount": 3000, "counterparty": "MERCHANT-017", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user_type"], "merchant")
    
    def test_35_refund_request_multiple(self):
        """Multiple refund requests"""
        request = {
            "ticket_id": "TKT-035",
            "complaint": "I want refund for all failed payments",
            "transaction_history": [
                {"transaction_id": "TXN-039", "timestamp": "2026-04-14T14:00:00Z", 
                 "type": "payment", "amount": 100, "counterparty": "MERCHANT-018", "status": "failed"},
                {"transaction_id": "TXN-040", "timestamp": "2026-04-14T14:05:00Z", 
                 "type": "payment", "amount": 150, "counterparty": "MERCHANT-018", "status": "failed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["case_type"], ["refund_request", "payment_failed"])
    
    def test_36_refund_request_no_transaction(self):
        """Refund request with no transaction history"""
        request = {
            "ticket_id": "TKT-036",
            "complaint": "Please refund my money",
            "transaction_history": []
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["evidence_verdict"], "insufficient_data")
    
    def test_37_refund_request_high_value(self):
        """High value refund request"""
        request = {
            "ticket_id": "TKT-037",
            "complaint": "Refund 100000 taka from my account",
            "transaction_history": [
                {"transaction_id": "TXN-041", "timestamp": "2026-04-14T15:00:00Z", 
                 "type": "payment", "amount": 100000, "counterparty": "MERCHANT-019", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["severity"], "critical")
        self.assertTrue(data["human_review_required"])
    
    def test_38_refund_request_phone_channel(self):
        """Refund request via phone"""
        request = {
            "ticket_id": "TKT-038",
            "complaint": "Refund for my transaction",
            "channel": "call_center",
            "transaction_history": [
                {"transaction_id": "TXN-042", "timestamp": "2026-04-14T16:00:00Z", 
                 "type": "payment", "amount": 750, "counterparty": "MERCHANT-020", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["channel"], "call_center")
    
    def test_39_refund_request_field_agent(self):
        """Refund request from field agent"""
        request = {
            "ticket_id": "TKT-039",
            "complaint": "Need refund for customer",
            "channel": "field_agent",
            "user_type": "agent",
            "transaction_history": [
                {"transaction_id": "TXN-043", "timestamp": "2026-04-14T17:00:00Z", 
                 "type": "payment", "amount": 2000, "counterparty": "MERCHANT-021", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["channel"], "field_agent")
    
    def test_40_refund_request_agent_cash(self):
        """Refund for agent cash-in"""
        request = {
            "ticket_id": "TKT-040",
            "complaint": "Refund my agent cash-in",
            "transaction_history": [
                {"transaction_id": "TXN-044", "timestamp": "2026-04-14T18:00:00Z", 
                 "type": "cash_in", "amount": 5000, "counterparty": "AGENT-002", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["case_type"], "refund_request")
    
    def test_41_refund_request_inconsistent(self):
        """Refund request with inconsistent evidence"""
        request = {
            "ticket_id": "TKT-041",
            "complaint": "Refund 5000 for wrong transfer",
            "transaction_history": [
                {"transaction_id": "TXN-045", "timestamp": "2026-04-14T19:00:00Z", 
                 "type": "transfer", "amount": 5000, "counterparty": "+8801712345692", "status": "completed"},
                {"transaction_id": "TXN-046", "timestamp": "2026-04-14T19:01:00Z", 
                 "type": "transfer", "amount": 5000, "counterparty": "+8801712345692", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["case_type"], ["refund_request", "duplicate_payment"])
    
    def test_42_refund_request_business(self):
        """Refund request with business context"""
        request = {
            "ticket_id": "TKT-042",
            "complaint": "Business payment needs refund",
            "campaign_context": "business_promo",
            "transaction_history": [
                {"transaction_id": "TXN-047", "timestamp": "2026-04-14T20:00:00Z", 
                 "type": "payment", "amount": 10000, "counterparty": "MERCHANT-022", "status": "completed"}
            ]
        }
        response = self.client.post("/analyze-ticket", json=request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["campaign_context"], "business_promo")
    
    def test_43_refund_request_fraud_concern(self):
        """Refund request with fraud concern"""
        request = {
            "ticket_id": "TKT-043",
            "complaint": "Unauthorized payment, need refund",
            "transaction_history": [
                {"transaction_id": "
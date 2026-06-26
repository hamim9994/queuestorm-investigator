# app/services/analyzer.py
import os
from app.services.base_analyzer import BaseAnalyzerFallback

try:
    from app.services.llm_analyzer import LLMAnalyzer
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

class TicketAnalyzer:
    """Factory class for ticket analysis"""
    
    def __init__(self):
        # Check if OpenAI API key is available
        use_llm = os.getenv("OPENAI_API_KEY") is not None and LLM_AVAILABLE
        
        if use_llm:
            try:
                from app.services.llm_analyzer import LLMAnalyzer
                self.analyzer = LLMAnalyzer()
                print("Using LLM-based analyzer")
            except Exception as e:
                print(f"LLM initialization failed: {e}")
                self.analyzer = BaseAnalyzerFallback()
                print("Using Base analyzer (fallback)")
        else:
            self.analyzer = BaseAnalyzerFallback()
            print("Using Base analyzer (no LLM)")
    
    def analyze(self, request):
        """Analyze a ticket using the configured analyzer"""
        return self.analyzer.analyze(request)
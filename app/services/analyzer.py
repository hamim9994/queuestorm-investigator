from app.services.base_analyzer import BaseAnalyzer
from app.services.llm_analyzer import LLMAnalyzer

class TicketAnalyzer:
    """Factory class for ticket analysis"""
    
    def __init__(self):
        self.analyzer: BaseAnalyzer = LLMAnalyzer()
    
    def analyze(self, request):
        """Analyze a ticket using the configured analyzer"""
        return self.analyzer.analyze(request)
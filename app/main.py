from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import time
import logging
from app.models.request import AnalyzeTicketRequest
from app.models.response import AnalyzeTicketResponse
from app.services.analyzer import TicketAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="QueueStorm Investigator", version="1.0.0")

# Initialize analyzer
analyzer = TicketAnalyzer()

@app.get("/health")
async def health_check():
    """Health check endpoint - must respond within 60 seconds of startup"""
    return {"status": "ok"}

@app.post("/analyze-ticket")
async def analyze_ticket(request: AnalyzeTicketRequest):
    """
    Analyze a customer complaint with transaction history
    """
    try:
        # Validate input
        if not request.complaint or len(request.complaint.strip()) < 3:
            raise HTTPException(
                status_code=422,
                detail="Complaint text must be at least 3 characters long"
            )
        
        # Process the ticket
        response = analyzer.analyze(request)
        
        return response.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing ticket: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error processing request"
        )
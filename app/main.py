# app/main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
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

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid input"}
    )

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
        
        # FIX: Use model_dump() instead of dict() (Pydantic v2)
        return response.model_dump()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing ticket: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error processing request"
        )
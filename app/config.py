import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    # Model settings
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    
    # Fallback settings - use local model if no API key
    USE_LOCAL_FALLBACK = os.getenv("USE_LOCAL_FALLBACK", "true").lower() == "true"
    
    # Safety thresholds
    HIGH_VALUE_THRESHOLD = float(os.getenv("HIGH_VALUE_THRESHOLD", "10000"))
    PHISHING_KEYWORDS = ["pin", "otp", "password", "mpin", "verification code"]
    
    # Response timeouts
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "10"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "25"))
import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    PORT: int           = int(os.getenv("PORT", "3001"))
    CLIENT_ORIGIN: str  = os.getenv("CLIENT_ORIGIN", "http://localhost:5173")
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024

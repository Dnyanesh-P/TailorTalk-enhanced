from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from datetime import datetime
import os
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Testing minimal FastAPI setup...")

app = FastAPI(title="Test AI Booking Agent API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get timezone
TIMEZONE = pytz.timezone(os.getenv('TIMEZONE', 'Asia/Kolkata'))

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "default_user"

@app.get("/")
async def root():
    current_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')
    return {
        "message": "🤖 Test AI Booking Agent API is running!",
        "status": "healthy",
        "version": "1.0.0",
        "current_time": current_time,
        "timezone": str(TIMEZONE)
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    current_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')
    return {
        "status": "healthy",
        "current_time": current_time,
        "timezone": str(TIMEZONE),
        "openai": "configured" if os.getenv("OPENAI_API_KEY") else "not configured",
        "credentials_path": os.getenv('GOOGLE_CREDENTIALS_PATH', 'not set')
    }

@app.post("/chat")
async def chat_endpoint(message: ChatMessage):
    """Simple chat endpoint without AI agent"""
    return {
        "response": f"Echo: {message.message} (This is a test response)", 
        "status": "success",
        "timestamp": datetime.now(TIMEZONE).isoformat()
    }

if __name__ == "__main__":
    print("🚀 Starting Test AI Booking Agent API...")
    print(f"🔑 OpenAI API key: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not set'}")
    print(f"🌍 Timezone: {TIMEZONE}")
    print("🌐 API will be available at: http://localhost:8000")
    
    try:
        uvicorn.run(
    app,
    host="127.0.0.1",  # Changed from 0.0.0.0
    port=8001,         # Changed from 8000
    reload=False,      # Changed from True
    log_level="info"
)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()

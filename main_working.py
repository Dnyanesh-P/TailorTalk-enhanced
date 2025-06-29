from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime, timedelta
import os
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="AI Booking Agent API", version="1.0.0")

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

class BookingRequest(BaseModel):
    date: str
    time: str
    duration: int = 60  # minutes
    title: str = "Meeting"
    description: Optional[str] = ""

class AvailabilityResponse(BaseModel):
    available_slots: List[str]
    date: str
    timezone: str

@app.get("/")
async def root():
    current_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')
    return {
        "message": "🤖 AI Booking Agent API is running!",
        "status": "healthy",
        "version": "1.0.0",
        "current_time": current_time,
        "timezone": str(TIMEZONE)
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        openai_configured = bool(os.getenv("OPENAI_API_KEY"))
        credentials_exist = os.path.exists(os.getenv('GOOGLE_CREDENTIALS_PATH', ''))
        
        current_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')
        
        return {
            "status": "healthy",
            "current_time": current_time,
            "timezone": str(TIMEZONE),
            "openai": "configured" if openai_configured else "not configured",
            "credentials_file": "found" if credentials_exist else "missing",
            "credentials_path": os.getenv('GOOGLE_CREDENTIALS_PATH', ''),
            "google_calendar": "not tested yet",
            "agent": "not initialized yet"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "current_time": datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')
        }

@app.post("/chat")
async def chat_endpoint(message: ChatMessage):
    """Simple chat endpoint without AI agent for now"""
    try:
        print(f"📨 Received message from {message.user_id}: {message.message}")
        
        # Simple response without AI for now
        current_time = datetime.now(TIMEZONE).strftime('%I:%M %p IST on %A, %B %d, %Y')
        
        if "hello" in message.message.lower() or "hi" in message.message.lower():
            response = f"Hello! I'm your AI booking assistant. Current time: {current_time}. I can help you schedule appointments. What would you like to book?"
        elif "book" in message.message.lower() or "schedule" in message.message.lower():
            response = "I'd be happy to help you book an appointment! Could you tell me what date and time you prefer? (Note: AI agent is not fully connected yet, but the API is working!)"
        else:
            response = f"I received your message: '{message.message}'. I'm a booking assistant and can help you schedule appointments. Current time: {current_time}"
        
        print(f"🤖 Sending response: {response}")
        return {
            "response": response, 
            "status": "success",
            "timestamp": datetime.now(TIMEZONE).isoformat()
        }
    except Exception as e:
        print(f"❌ Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/availability/{date}")
async def get_availability(date: str):
    """Mock availability endpoint (without Google Calendar for now)"""
    try:
        # Mock available slots for testing
        mock_slots = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
        return AvailabilityResponse(
            available_slots=mock_slots, 
            date=date,
            timezone=str(TIMEZONE)
        )
    except Exception as e:
        print(f"❌ Error getting availability: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/book")
async def book_appointment(booking: BookingRequest):
    """Mock booking endpoint (without Google Calendar for now)"""
    try:
        # Mock booking for testing
        datetime_str = f"{booking.date} {booking.time}"
        booking_datetime_naive = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        booking_datetime = TIMEZONE.localize(booking_datetime_naive)
        
        # Mock event ID
        mock_event_id = f"mock_event_{int(datetime.now().timestamp())}"
        
        return {
            "event_id": mock_event_id,
            "status": "booked (mock)",
            "message": "Mock appointment booked successfully! (Google Calendar not connected yet)",
            "datetime": booking_datetime.isoformat(),
            "timezone": str(TIMEZONE)
        }
    except Exception as e:
        print(f"❌ Error booking appointment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting AI Booking Agent API (Working Version)...")
    print(f"📁 Credentials path: {os.getenv('GOOGLE_CREDENTIALS_PATH', 'Not set')}")
    print(f"🔑 OpenAI API key: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not set'}")
    print(f"🌍 Timezone: {TIMEZONE}")
    print("🌐 API will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    print("⚠️  Note: This version works without Google Calendar and AI agent for testing")
    
    uvicorn.run(
        app,
        host="127.0.0.1",  # Changed from 0.0.0.0
        port=8001,         # Changed from 8000
        reload=False,      # Changed from True
        log_level="info"
    )

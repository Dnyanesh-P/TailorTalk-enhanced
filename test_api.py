from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime, timedelta
import os
import pytz
from dotenv import load_dotenv
from google_calendar import get_calendar_manager
from langgraph_agent import BookingAgent

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

# Initialize the booking agent
try:
    booking_agent = BookingAgent()
    print("✅ Booking agent initialized successfully!")
except Exception as e:
    print(f"❌ Error initializing booking agent: {e}")
    import traceback
    traceback.print_exc()
    booking_agent = None

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
        # Test Google Calendar connection
        calendar_manager = get_calendar_manager()
        openai_configured = bool(os.getenv("OPENAI_API_KEY"))
        credentials_exist = os.path.exists(os.getenv('GOOGLE_CREDENTIALS_PATH', ''))
        
        current_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')
        
        return {
            "status": "healthy",
            "current_time": current_time,
            "timezone": str(TIMEZONE),
            "google_calendar": "connected" if calendar_manager else "failed",
            "openai": "configured" if openai_configured else "not configured",
            "credentials_file": "found" if credentials_exist else "missing",
            "credentials_path": os.getenv('GOOGLE_CREDENTIALS_PATH', ''),
            "agent": "initialized" if booking_agent else "failed"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "current_time": datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')
        }

@app.post("/chat")
async def chat_endpoint(message: ChatMessage):
    """Main chat endpoint for the AI agent"""
    if not booking_agent:
        raise HTTPException(status_code=500, detail="Booking agent not initialized")
    
    try:
        print(f"📨 Received message from {message.user_id}: {message.message}")
        response = await booking_agent.process_message(message.message, message.user_id)
        print(f"🤖 Agent response: {response}")
        return {
            "response": response, 
            "status": "success",
            "timestamp": datetime.now(TIMEZONE).isoformat()
        }
    except Exception as e:
        print(f"❌ Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/availability/{date}")
async def get_availability(date: str):
    """Get available time slots for a specific date"""
    try:
        calendar_manager = get_calendar_manager()
        available_slots = calendar_manager.get_availability(date)
        return AvailabilityResponse(
            available_slots=available_slots, 
            date=date,
            timezone=str(TIMEZONE)
        )
    except Exception as e:
        print(f"❌ Error getting availability: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/book")
async def book_appointment(booking: BookingRequest):
    """Book an appointment"""
    try:
        calendar_manager = get_calendar_manager()
        
        # Create datetime object in IST
        datetime_str = f"{booking.date} {booking.time}"
        booking_datetime_naive = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        booking_datetime = TIMEZONE.localize(booking_datetime_naive)
        
        # Create calendar event
        event_id = calendar_manager.create_event(
            title=booking.title,
            start_datetime=booking_datetime,
            duration_minutes=booking.duration,
            description=booking.description
        )
        
        return {
            "event_id": event_id,
            "status": "booked",
            "message": "Appointment booked successfully!",
            "datetime": booking_datetime.isoformat(),
            "timezone": str(TIMEZONE)
        }
    except Exception as e:
        print(f"❌ Error booking appointment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting AI Booking Agent API...")
    print(f"📁 Credentials path: {os.getenv('GOOGLE_CREDENTIALS_PATH', 'Not set')}")
    print(f"🔑 OpenAI API key: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not set'}")
    print(f"🌍 Timezone: {TIMEZONE}")
    print("🌐 API will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

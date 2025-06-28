import os
import sys
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import pytz
import asyncio

import uvicorn

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('tailortalk.log', encoding='utf-8')]
)
logger = logging.getLogger("tailortalk")

# Import enhanced modules
try:
    from backend.enhanced_langgraph_agent import EnhancedBookingAgent
    from backend.date_time_parser import DateTimeParser
    from backend.enhanced_calendar import EnhancedCalendarManager
    logger.info("✅ Enhanced modules loaded")
except ImportError as e:
    logger.error(f"❌ Enhanced modules missing: {e}")
    sys.exit(1)

# Timezone setup
TIMEZONE = pytz.timezone(os.getenv('TIMEZONE', 'Asia/Kolkata'))

def get_datetime_parser():
    """Singleton for DateTimeParser."""
    if not hasattr(get_datetime_parser, "parser"):
        get_datetime_parser.parser = DateTimeParser(str(TIMEZONE))
        logger.info("✅ DateTimeParser initialized")
    return get_datetime_parser.parser

async def get_booking_agent():
    """Singleton for EnhancedBookingAgent."""
    if not hasattr(get_booking_agent, "agent"):
        try:
            get_booking_agent.agent = EnhancedBookingAgent()
            logger.info("✅ EnhancedBookingAgent initialized")
        except Exception as e:
            logger.error(f"❌ Failed to init EnhancedBookingAgent: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Booking agent unavailable")
    return get_booking_agent.agent

# FastAPI app
tailor_app = FastAPI(
    title="TailorTalk AI Booking API",
    description="AI-powered appointment booking with advanced NLP and Google Calendar integration.",
    version="2.0.0"
)

# CORS
tailor_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    message: str = Field(..., description="User message")
    user_id: Optional[str] = Field("default_user", description="User identifier")

class ChatResponse(BaseModel):
    response: str
    status: str
    timestamp: datetime
    user_id: str

class DateTimeParseResponse(BaseModel):
    date: Optional[str]
    time: Optional[str]
    confidence: float
    original_text: str
    parsed_components: List[str]

class AvailabilityResponse(BaseModel):
    available_slots: List[str]
    date: str
    timezone: str
    total_slots: int

class BookingRequest(BaseModel):
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    duration: int = Field(60, ge=1, description="Duration in minutes")
    title: Optional[str] = Field("Meeting", description="Event title")
    description: Optional[str] = Field("", description="Event description")
    attendee_email: Optional[str] = Field(None, description="Attendee email")
    location: Optional[str] = Field(None, description="Event location")
    reminders: Optional[List[int]] = Field(default_factory=lambda: [15], description="Reminder times in minutes")

    @validator('date')
    def valid_date(cls, v):
        d = date.fromisoformat(v)
        today = date.today()
        if d < today:
            raise ValueError('Date cannot be in the past')
        if d > today.replace(year=today.year + 1):
            raise ValueError('Date too far in the future')
        return v

class BookingResponse(BaseModel):
    event_id: str
    status: str

class EventDetail(BaseModel):
    id: str
    summary: str
    start_time: str
    end_time: str

class EventsResponse(BaseModel):
    date: str
    timezone: str
    events: List[EventDetail]

# Routes
tailor_app.get("/", tags=["System"])(
    lambda: {"message": "TailorTalk API running.", "version": "2.0.0", "timezone": str(TIMEZONE)}
)

@tailor_app.get("/health", tags=["System"])
async def health_check():
    try:
        cal_mgr = EnhancedCalendarManager()
        today = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
        slots = cal_mgr.get_availability(today)
        agent = await get_booking_agent()
        return {"status": "healthy", "slots_today": len(slots), "agent": "ready"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@tailor_app.post("/chat", response_model=ChatResponse, tags=["AI Assistant"])
async def chat_endpoint(msg: ChatMessage):
    agent = await get_booking_agent()
    reply = await agent.process_message(msg.message, msg.user_id)
    return ChatResponse(response=reply, status="success", timestamp=datetime.now(TIMEZONE), user_id=msg.user_id)

@tailor_app.get("/parse-datetime", response_model=DateTimeParseResponse, tags=["Tools"])
async def parse_datetime(text: str):
    parser = get_datetime_parser()
    res = parser.parse_datetime(text)
    return DateTimeParseResponse(
        date=res.get('date'), time=res.get('time'), confidence=res.get('confidence', 0),
        original_text=res.get('original_text'), parsed_components=res.get('parsed_components', [])
    )

@tailor_app.get("/availability/{date}", response_model=AvailabilityResponse, tags=["Calendar"])
async def availability(date: str):
    cal_mgr = EnhancedCalendarManager()
    slots = cal_mgr.get_availability(date)
    return AvailabilityResponse(
        available_slots=slots, date=date, timezone=str(TIMEZONE), total_slots=len(slots)
    )

@tailor_app.post("/book", response_model=BookingResponse, tags=["Calendar"])
async def book(request: BookingRequest):
    cal_mgr = EnhancedCalendarManager()
    details = {"title": request.title, "description": request.description,
               "attendees": [request.attendee_email] if request.attendee_email else [],
               "location": request.location, "duration": request.duration}
    event_id = cal_mgr.create_event_with_details(request.date, request.time, details)
    return BookingResponse(event_id=event_id, status="booked")

@tailor_app.get("/events/{date}", response_model=EventsResponse, tags=["Calendar"])
async def list_events(date: str):
    cal_mgr = EnhancedCalendarManager()
    raw = cal_mgr.get_events(date)
    events = []
    for e in raw:
        start = e.get('start', {}).get('dateTime') or e.get('start', {}).get('date')
        end = e.get('end', {}).get('dateTime') or e.get('end', {}).get('date')
        events.append(EventDetail(id=e.get('id'), summary=e.get('summary', ''), start_time=start, end_time=end))
    return EventsResponse(date=date, timezone=str(TIMEZONE), events=events)
if __name__ == "__main__":
    print("Starting TailorTalk AI Booking Agent API...")
    print(f"Credentials path: {os.getenv('GOOGLE_CREDENTIALS_PATH', 'Not set')}")
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key and openai_key != "your_openai_api_key_here":
        print(f"OpenAI API key: Set")
    else:
        print(f"OpenAI API key: Not set (using fallback agent)")
    print(f"Timezone: {TIMEZONE}")
    print("API will be available at: http://127.0.0.1:8001")
    print("API docs will be available at: http://127.0.0.1:8001/docs")
    print("AI agent with Google Calendar integration enabled!")
    
    uvicorn.run(
        "main_with_ai:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    )

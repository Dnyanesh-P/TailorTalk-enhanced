"""
Vercel-optimized FastAPI application for TailorTalk Enhanced
This file is specifically designed for Vercel's serverless function architecture
"""

from fastapi import FastAPI, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import pytz
from enum import Enum
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app with proper configuration for Vercel
app = FastAPI(
    title="TailorTalk API - Vercel Deployment",
    description="AI-Powered Appointment Booking System deployed on Vercel",
    version="3.1.0",
    docs_url="/api/docs",  # Important: prefix with /api for Vercel
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS configuration for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tailortalk-enhanced-uael6bdk6fzdahsnfuemah.streamlit.app",
        "https://*.streamlit.app",
        "http://localhost:8501",
        "*"  # Remove in production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Timezone
TIMEZONE = pytz.timezone('Asia/Kolkata')
STREAMLIT_APP_URL = "https://tailortalk-enhanced-uael6bdk6fzdahsnfuemah.streamlit.app"

# Pydantic models
class BookingStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"

class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    user_id: Optional[str] = Field("streamlit_user")

class ChatResponse(BaseModel):
    response: str
    status: BookingStatus
    timestamp: datetime
    user_id: str
    agent_type: Optional[str] = None

class AvailabilityResponse(BaseModel):
    available_slots: List[str]
    date: str
    timezone: str
    total_slots: int
    formatted_date: Optional[str] = None

# Simple booking agent for Vercel
class VercelBookingAgent:
    def process_message(self, message: str, user_id: str) -> str:
        current_time = datetime.now(TIMEZONE).strftime('%I:%M %p %Z on %A, %B %d, %Y')
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['book', 'schedule', 'appointment']):
            return f"🎯 Great! I can help you book an appointment.\n\n" \
                   f"📝 Your request: '{message}'\n" \
                   f"🕐 Current time: {current_time}\n\n" \
                   f"✅ Available time slots:\n" \
                   f"• Tomorrow 9:00 AM\n" \
                   f"• Tomorrow 2:00 PM\n" \
                   f"• Day after tomorrow 10:00 AM\n\n" \
                   f"🌐 Visit: {STREAMLIT_APP_URL}"
        
        elif any(word in message_lower for word in ['hello', 'hi', 'hey']):
            return f"👋 Hello! Welcome to TailorTalk!\n\n" \
                   f"🕐 Current time: {current_time}\n\n" \
                   f"I'm your AI booking assistant. I can help you:\n" \
                   f"📅 Book appointments\n" \
                   f"🔍 Check availability\n" \
                   f"⏰ Schedule meetings\n\n" \
                   f"Try: 'Book appointment for tomorrow at 2 PM'\n" \
                   f"🌐 Streamlit App: {STREAMLIT_APP_URL}"
        
        elif any(word in message_lower for word in ['available', 'availability']):
            return f"📅 Here's today's availability:\n\n" \
                   f"🕐 Current time: {current_time}\n\n" \
                   f"Available slots:\n" \
                   f"• 09:00 AM - 10:00 AM ✅\n" \
                   f"• 11:00 AM - 12:00 PM ✅\n" \
                   f"• 02:00 PM - 03:00 PM ✅\n" \
                   f"• 04:00 PM - 05:00 PM ✅\n\n" \
                   f"Which time works best for you?\n" \
                   f"🌐 Visit: {STREAMLIT_APP_URL}"
        
        else:
            return f"🤖 I received: '{message}'\n\n" \
                   f"🕐 Current time: {current_time}\n\n" \
                   f"Try these commands:\n" \
                   f"• 'Hello' - Get started\n" \
                   f"• 'Book appointment' - Schedule a meeting\n" \
                   f"• 'Check availability' - See open slots\n\n" \
                   f"🚀 TailorTalk API is working on Vercel!\n" \
                   f"🌐 Streamlit App: {STREAMLIT_APP_URL}"

# Initialize agent
booking_agent = VercelBookingAgent()

# API Routes - All prefixed with /api for Vercel
@app.get("/api/")
async def root():
    """Root endpoint - this fixes the 404 error"""
    current_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')
    
    return {
        "message": "🚀 TailorTalk API is LIVE on Vercel!",
        "status": "healthy",
        "version": "3.1.0",
        "current_time": current_time,
        "timezone": str(TIMEZONE),
        "deployment": "Vercel Serverless",
        "streamlit_integration": "Ready",
        "endpoints": {
            "chat": "/api/chat - Send messages to AI",
            "availability": "/api/availability/YYYY-MM-DD - Check slots",
            "health": "/api/health - System status",
            "docs": "/api/docs - API documentation"
        },
        "test_commands": [
            "Hello",
            "Book appointment for tomorrow",
            "Check availability"
        ],
        "cors_configured_for": STREAMLIT_APP_URL,
        "vercel_deployment": "✅ Working"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    current_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')
    
    return {
        "status": "healthy",
        "message": "TailorTalk API is running perfectly on Vercel!",
        "current_time": current_time,
        "timezone": str(TIMEZONE),
        "deployment": {
            "platform": "Vercel",
            "type": "Serverless Function",
            "status": "✅ Active"
        },
        "components": {
            "fastapi": "✅ Running",
            "cors": "✅ Configured",
            "booking_agent": "✅ Ready",
            "timezone": "✅ Asia/Kolkata"
        },
        "streamlit_integration": {
            "target_app": STREAMLIT_APP_URL,
            "cors_status": "✅ Enabled",
            "ready": True
        },
        "vercel_specific": {
            "serverless_function": "✅ Working",
            "cold_start": "Optimized",
            "region": "Auto"
        }
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """Chat with AI assistant"""
    try:
        logger.info(f"Chat request from {message.user_id}: {message.message}")
        
        # Process message
        response = booking_agent.process_message(message.message, message.user_id)
        
        return ChatResponse(
            response=response,
            status=BookingStatus.SUCCESS,
            timestamp=datetime.now(TIMEZONE),
            user_id=message.user_id,
            agent_type="vercel_optimized"
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        
        return ChatResponse(
            response=f"Sorry, I encountered an error: {str(e)}\n\nPlease try again!\n🌐 Visit: {STREAMLIT_APP_URL}",
            status=BookingStatus.ERROR,
            timestamp=datetime.now(TIMEZONE),
            user_id=message.user_id,
            agent_type="error_handler"
        )

@app.get("/api/availability/{date}", response_model=AvailabilityResponse)
async def get_availability(date: str):
    """Get available time slots"""
    try:
        # Validate date
        parsed_date = datetime.strptime(date, '%Y-%m-%d').date()
        if parsed_date < datetime.now(TIMEZONE).date():
            raise HTTPException(
                status_code=400,
                detail="Cannot check availability for past dates"
            )
        
        # Mock availability for Vercel deployment
        available_slots = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
        formatted_date = parsed_date.strftime('%A, %B %d, %Y')
        
        return AvailabilityResponse(
            available_slots=available_slots,
            date=date,
            timezone=str(TIMEZONE),
            total_slots=len(available_slots),
            formatted_date=formatted_date
        )
        
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking availability: {str(e)}"
        )

@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint to verify deployment"""
    return {
        "message": "✅ Vercel deployment test successful!",
        "timestamp": datetime.now(TIMEZONE).isoformat(),
        "status": "API is working perfectly on Vercel",
        "deployment_info": {
            "platform": "Vercel",
            "function_type": "Serverless",
            "region": "Auto-detected"
        }
    }

# Root redirect for convenience
@app.get("/")
async def root_redirect():
    """Redirect root to API root"""
    return await root()

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now(TIMEZONE).isoformat(),
            "deployment": "Vercel",
            "suggestion": "Check the API documentation at /api/docs"
        }
    )

# Export for Vercel - This is crucial!
handler = app

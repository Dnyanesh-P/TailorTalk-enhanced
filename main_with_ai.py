"""
Enhanced TailorTalk server with integrated precise scheduling
"""

import uvicorn
import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
import pytz
import asyncio
from enum import Enum

# Set up logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tailortalk.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables first
load_dotenv()

# Import enhanced modules with comprehensive error handling
ENHANCED_MODULES_STATUS = {
    'advanced_parser': False,
    'enhanced_calendar': False,
    'precise_scheduler': False,
    'enhanced_agent': False,
    'fallback_agent': False,
    'openai_agent': False
}

# Try to import enhanced modules
try:
    from backend.advanced_date_parser import advanced_parser, AdvancedDateTimeParser
    ENHANCED_MODULES_STATUS['advanced_parser'] = True
    logger.info("✅ Advanced date parser imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Advanced date parser not available: {e}")
except Exception as e:
    logger.error(f"❌ Advanced date parser import error: {e}")

try:
    from backend.enhanced_calendar import get_enhanced_calendar_manager, EnhancedCalendarManager
    ENHANCED_MODULES_STATUS['enhanced_calendar'] = True
    logger.info("✅ Enhanced calendar manager imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Enhanced calendar manager not available: {e}")
except Exception as e:
    logger.error(f"❌ Enhanced calendar manager import error: {e}")

try:
    from backend.precise_appointment_scheduler import precise_scheduler, PreciseAppointmentScheduler
    ENHANCED_MODULES_STATUS['precise_scheduler'] = True
    logger.info("✅ Precise appointment scheduler imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Precise appointment scheduler not available: {e}")
except Exception as e:
    logger.error(f"❌ Precise appointment scheduler import error: {e}")

try:
    from backend.enhanced_booking_agent import enhanced_booking_agent, EnhancedBookingAgent
    ENHANCED_MODULES_STATUS['enhanced_agent'] = True
    logger.info("✅ Enhanced booking agent imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Enhanced booking agent not available: {e}")
except Exception as e:
    logger.error(f"❌ Enhanced booking agent import error: {e}")

# Try to import fallback modules
try:
    from backend.langgraph_agent_fallback import FallbackBookingAgent
    ENHANCED_MODULES_STATUS['fallback_agent'] = True
    logger.info("✅ Fallback booking agent imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Fallback booking agent not available: {e}")
except Exception as e:
    logger.error(f"❌ Fallback booking agent import error: {e}")

# Try to import OpenAI agent
try:
    from backend.langgraph_agent import BookingAgent as OpenAIBookingAgent
    ENHANCED_MODULES_STATUS['openai_agent'] = True
    logger.info("✅ OpenAI booking agent imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ OpenAI booking agent not available: {e}")
except Exception as e:
    logger.error(f"❌ OpenAI booking agent import error: {e}")

# Try to import basic calendar manager as fallback
try:
    from backend.google_calendar import get_calendar_manager
    logger.info("✅ Basic calendar manager available as fallback")
except ImportError as e:
    logger.error(f"❌ No calendar manager available: {e}")

# Check if we have at least one working agent
if not any([ENHANCED_MODULES_STATUS['enhanced_agent'], 
           ENHANCED_MODULES_STATUS['fallback_agent'], 
           ENHANCED_MODULES_STATUS['openai_agent']]):
    logger.error("CRITICAL: No booking agents available!")
    import sys
    sys.exit(1)

# Get timezone
TIMEZONE = pytz.timezone(os.getenv('TIMEZONE', 'Asia/Kolkata'))

# Create FastAPI app with enhanced metadata
app = FastAPI(
    title="TailorTalk AI Booking Assistant API - Enhanced",
    description="""
    **TailorTalk Enhanced** is an intelligent appointment booking system with advanced features:
    
    ## 🚀 Enhanced Features
    
    * **Precise Date/Time Parsing** - Handles "5th July", "4th August 3:30pm", etc.
    * **Advanced Calendar Integration** - Real-time Google Calendar sync with timezone handling
    * **Smart Conversation Flow** - Context-aware multi-turn conversations
    * **Robust Error Handling** - Comprehensive error recovery and user guidance
    * **Multiple Agent Support** - Enhanced AI, OpenAI, and rule-based fallback agents
    
    ## 🎯 Supported Formats
    
    * **Dates**: "5th July", "July 5th", "tomorrow", "next Monday", "2025-07-05"
    * **Times**: "3:30pm", "15:00", "afternoon", "morning", "3 PM"
    * **Combined**: "Book appointment on 5th July at 3:30pm"
    
    ## 🔧 System Status
    
    Check `/health` endpoint for detailed system status and component availability.
    """,
    version="3.0.0",
    contact={
        "name": "TailorTalk Support",
        "email": "dnyaneshpurohit@gmail.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the AI agent globally
booking_agent = None

async def get_booking_agent():
    """Get or initialize the best available booking agent"""
    global booking_agent
    if booking_agent is None:
        
        # Priority 1: Enhanced Booking Agent (best option)
        if ENHANCED_MODULES_STATUS['enhanced_agent']:
            try:
                booking_agent = enhanced_booking_agent
                logger.info("🎯 Enhanced Booking Agent initialized (with precise scheduling)")
                return booking_agent
            except Exception as e:
                logger.warning(f"Enhanced booking agent failed: {e}")
        
        # Priority 2: OpenAI Agent (if API key available)
        if ENHANCED_MODULES_STATUS['openai_agent']:
            try:
                openai_key = os.getenv("OPENAI_API_KEY")
                if openai_key and openai_key != "your_openai_api_key_here":
                    logger.info("Testing OpenAI API connection...")
                    
                    # Test OpenAI connection
                    from openai import OpenAI
                    test_client = OpenAI(api_key=openai_key)
                    test_response = test_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=1
                    )
                    
                    booking_agent = OpenAIBookingAgent()
                    logger.info("🤖 OpenAI Booking Agent initialized")
                    return booking_agent
                else:
                    logger.info("OpenAI API key not configured, skipping OpenAI agent")
            except Exception as e:
                logger.warning(f"OpenAI agent failed: {e}")
        
        # Priority 3: Fallback Agent (rule-based)
        if ENHANCED_MODULES_STATUS['fallback_agent']:
            try:
                booking_agent = FallbackBookingAgent()
                logger.info("🔄 Fallback Booking Agent initialized (rule-based)")
                return booking_agent
            except Exception as e:
                logger.error(f"Fallback agent failed: {e}")
        
        # If all agents fail
        logger.error("No booking agent could be initialized!")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No AI agent available - all agents failed to initialize"
        )
    
    return booking_agent

# Enums for better API documentation
class BookingStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"

class MeetingType(str, Enum):
    MEETING = "meeting"
    CALL = "call"
    CONSULTATION = "consultation"
    INTERVIEW = "interview"
    DEMO = "demo"
    OTHER = "other"

# Enhanced Pydantic models
class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="User message for the AI assistant")
    user_id: Optional[str] = Field("default_user", description="Unique identifier for the user")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Book appointment on 5th July at 3:30pm",
                "user_id": "user123"
            }
        }
    }

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI assistant's response")
    status: BookingStatus = Field(..., description="Response status")
    timestamp: datetime = Field(..., description="Response timestamp")
    user_id: str = Field(..., description="User identifier")
    agent_type: Optional[str] = Field(None, description="Type of agent that processed the request")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "response": "✅ Appointment confirmed for Saturday, July 05, 2025 at 03:30 PM",
                "status": "success",
                "timestamp": "2025-06-27T15:30:00+05:30",
                "user_id": "user123",
                "agent_type": "enhanced"
            }
        }
    }

class AvailabilityResponse(BaseModel):
    available_slots: List[str] = Field(..., description="List of available time slots")
    date: str = Field(..., description="Date for availability check")
    timezone: str = Field(..., description="Timezone")
    total_slots: int = Field(..., description="Total number of available slots")
    formatted_date: Optional[str] = Field(None, description="Human-readable date format")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "available_slots": ["09:00", "10:00", "11:00", "14:00", "15:00"],
                "date": "2025-07-05",
                "timezone": "Asia/Kolkata",
                "total_slots": 5,
                "formatted_date": "Saturday, July 05, 2025"
            }
        }
    }

class DateTimeParseRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500, description="Natural language text to parse")
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty')
        return v.strip()

class DateTimeParseResponse(BaseModel):
    date: Optional[str] = Field(None, description="Extracted date in YYYY-MM-DD format")
    time: Optional[str] = Field(None, description="Extracted time in HH:MM format")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")
    original_text: str = Field(..., description="Original input text")
    parsed_components: List[str] = Field(..., description="List of parsed components")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    parser_type: str = Field(..., description="Type of parser used")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall system status")
    current_time: str = Field(..., description="Current server time")
    timezone: str = Field(..., description="Server timezone")
    components: Dict[str, str] = Field(..., description="Status of individual components")
    config: Dict[str, Any] = Field(..., description="System configuration")
    enhanced_features: Dict[str, bool] = Field(..., description="Enhanced features availability")

# API Routes

@app.get(
    "/",
    tags=["System"],
    summary="API Root - Enhanced",
    description="Get enhanced API information and status",
    response_model=Dict[str, Any]
)
async def root():
    """
    Welcome endpoint for TailorTalk Enhanced API.
    
    Returns system status, version, and available enhanced features.
    """
    current_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')
    
    # Determine active agent type
    agent_type = "none"
    if ENHANCED_MODULES_STATUS['enhanced_agent']:
        agent_type = "enhanced"
    elif ENHANCED_MODULES_STATUS['openai_agent']:
        agent_type = "openai"
    elif ENHANCED_MODULES_STATUS['fallback_agent']:
        agent_type = "fallback"
    
    return {
        "message": "🚀 TailorTalk Enhanced AI Booking Agent API",
        "status": "healthy",
        "version": "3.0.0",
        "current_time": current_time,
        "timezone": str(TIMEZONE),
        "active_agent": agent_type,
        "enhanced_features": {
            "precise_date_parsing": ENHANCED_MODULES_STATUS['advanced_parser'],
            "enhanced_calendar": ENHANCED_MODULES_STATUS['enhanced_calendar'],
            "precise_scheduling": ENHANCED_MODULES_STATUS['precise_scheduler'],
            "enhanced_conversations": ENHANCED_MODULES_STATUS['enhanced_agent'],
            "timezone_handling": True,
            "error_recovery": True
        },
        "supported_formats": {
            "dates": ["5th July", "July 5th", "tomorrow", "next Monday", "2025-07-05"],
            "times": ["3:30pm", "15:00", "afternoon", "morning", "3 PM"],
            "combined": ["Book appointment on 5th July at 3:30pm"]
        },
        "endpoints": {
            "chat": "/chat - Enhanced conversational booking interface",
            "availability": "/availability/{date} - Check available slots",
            "parse-datetime": "/parse-datetime - Test enhanced parsing",
            "health": "/health - Comprehensive system health check",
            "docs": "/docs - API documentation"
        }
    }

@app.get(
    "/health",
    tags=["System"],
    summary="Enhanced Health Check",
    description="Comprehensive system health check with enhanced components",
    response_model=HealthResponse
)
async def health_check():
    """
    Comprehensive health check for all enhanced components.
    
    Verifies:
    - Enhanced modules availability
    - Calendar integration
    - AI agent initialization
    - Parsing capabilities
    - System configuration
    """
    try:
        # Check OpenAI configuration
        openai_key = os.getenv("OPENAI_API_KEY")
        openai_configured = bool(openai_key and openai_key != "your_openai_api_key_here")
        
        # Check Google credentials
        credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', '')
        credentials_exist = os.path.exists(credentials_path)
        
        # Test calendar connection
        calendar_status = "not tested"
        try:
            if ENHANCED_MODULES_STATUS['enhanced_calendar']:
                calendar_manager = get_enhanced_calendar_manager()
                connection_result = calendar_manager.test_connection()
                if connection_result['status'] == 'success':
                    calendar_status = f"enhanced calendar connected ({connection_result['calendar_name']})"
                else:
                    calendar_status = f"enhanced calendar error: {connection_result['error']}"
            else:
                # Fallback to basic calendar
                calendar_manager = get_calendar_manager()
                today = datetime.now(TIMEZONE).date().strftime('%Y-%m-%d')
                test_slots = calendar_manager.get_availability(today)
                calendar_status = f"basic calendar connected ({len(test_slots)} slots available today)"
        except Exception as e:
            calendar_status = f"calendar error: {str(e)}"
        
        # Test AI agent
        agent_status = "not tested"
        agent_type = "none"
        try:
            agent = await get_booking_agent()
            if hasattr(agent, '__class__'):
                class_name = agent.__class__.__name__
                if 'Enhanced' in class_name:
                    agent_status = "enhanced agent ready (with precise scheduling)"
                    agent_type = "enhanced"
                elif 'Fallback' in class_name:
                    agent_status = "fallback agent ready (rule-based)"
                    agent_type = "fallback"
                elif 'OpenAI' in class_name or 'BookingAgent' in class_name:
                    agent_status = "OpenAI agent ready"
                    agent_type = "openai"
                else:
                    agent_status = f"agent ready ({class_name})"
                    agent_type = "unknown"
            else:
                agent_status = "agent ready (unknown type)"
        except Exception as e:
            agent_status = f"agent error: {str(e)}"
        
        # Test parsing capabilities
        parsing_status = "not available"
        if ENHANCED_MODULES_STATUS['advanced_parser']:
            try:
                test_result = advanced_parser.parse_appointment_request("5th July at 3pm")
                if test_result['date'] and test_result['time']:
                    parsing_status = f"enhanced parsing ready (confidence: {test_result['confidence']:.2f})"
                else:
                    parsing_status = "enhanced parsing partial"
            except Exception as e:
                parsing_status = f"enhanced parsing error: {str(e)}"
        
        current_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')
        
        # Determine overall status
        critical_components = [credentials_exist, agent_status != "agent error"]
        overall_status = "healthy" if all(critical_components) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            current_time=current_time,
            timezone=str(TIMEZONE),
            components={
                "openai_api": "configured" if openai_configured else "not configured (using fallback)",
                "google_credentials": "found" if credentials_exist else "missing",
                "calendar_integration": calendar_status,
                "ai_agent": agent_status,
                "date_time_parsing": parsing_status,
                "enhanced_scheduler": "available" if ENHANCED_MODULES_STATUS['precise_scheduler'] else "not available"
            },
            config={
                "credentials_path": credentials_path,
                "calendar_id": os.getenv('CALENDAR_ID', 'primary'),
                "timezone": str(TIMEZONE),
                "active_agent_type": agent_type,
                "openai_available": openai_configured,
                "enhanced_mode": ENHANCED_MODULES_STATUS['enhanced_agent']
            },
            enhanced_features=ENHANCED_MODULES_STATUS
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )

@app.post(
    "/chat",
    tags=["AI Assistant"],
    summary="Enhanced Chat Interface",
    description="Chat with enhanced AI assistant for precise appointment scheduling",
    response_model=ChatResponse
)
async def chat_endpoint(message: ChatMessage):
    """
    Enhanced conversational interface with precise date/time understanding.
    
    The enhanced AI can accurately understand:
    - "Book appointment on 5th July at 3:30pm"
    - "Schedule meeting for August 4th at 15:00"
    - "Book for tomorrow at 2 PM"
    - "Show me availability for next Monday"
    
    Features context-aware conversations and precise scheduling.
    """
    try:
        logger.info(f"Enhanced chat request from {message.user_id}: {message.message}")
        
        # Get the best available AI agent
        agent = await get_booking_agent()
        
        # Determine agent type for response
        agent_type = "unknown"
        if hasattr(agent, '__class__'):
            class_name = agent.__class__.__name__
            if 'Enhanced' in class_name:
                agent_type = "enhanced"
            elif 'Fallback' in class_name:
                agent_type = "fallback"
            elif 'OpenAI' in class_name or 'BookingAgent' in class_name:
                agent_type = "openai"
        
        # Process the message through the AI agent
        response = await agent.process_message(message.message, message.user_id)
        
        logger.info(f"Enhanced AI response ({agent_type}): {response[:100]}...")
        
        return ChatResponse(
            response=response,
            status=BookingStatus.SUCCESS,
            timestamp=datetime.now(TIMEZONE),
            user_id=message.user_id,
            agent_type=agent_type
        )
        
    except Exception as e:
        logger.error(f"Error in enhanced chat endpoint: {e}")
        current_time = datetime.now(TIMEZONE).strftime('%I:%M %p %Z on %A, %B %d, %Y')
        
        # Enhanced error response
        fallback_response = f"I'm experiencing technical difficulties right now.\n\n" \
                          f"🕐 Current time: {current_time}\n" \
                          f"🔧 System status: Temporary issue\n\n" \
                          f"Please try again in a moment, or use a simple format like:\n" \
                          f"'Book appointment on [date] at [time]'"
        
        return ChatResponse(
            response=fallback_response,
            status=BookingStatus.ERROR,
            timestamp=datetime.now(TIMEZONE),
            user_id=message.user_id,
            agent_type="error_handler"
        )

@app.get(
    "/availability/{date}",
    tags=["Calendar"],
    summary="Enhanced Availability Check",
    description="Get available time slots with enhanced calendar integration",
    response_model=AvailabilityResponse
)
async def get_availability(date: str):
    """
    Check available time slots using enhanced calendar integration.
    
    Features:
    - Real-time Google Calendar sync
    - Timezone-aware scheduling
    - Business hours filtering
    - Conflict detection
    """
    try:
        # Validate date format
        try:
            parsed_date = datetime.strptime(date, '%Y-%m-%d').date()
            if parsed_date < datetime.now(TIMEZONE).date():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot check availability for past dates"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        logger.info(f"Enhanced availability check for {date}")
        
        # Use enhanced calendar manager if available
        if ENHANCED_MODULES_STATUS['enhanced_calendar']:
            calendar_manager = get_enhanced_calendar_manager()
        else:
            calendar_manager = get_calendar_manager()
        
        # Get available slots
        available_slots = calendar_manager.get_availability(date)
        
        # Format date nicely
        formatted_date = parsed_date.strftime('%A, %B %d, %Y')
        
        return AvailabilityResponse(
            available_slots=available_slots,
            date=date,
            timezone=str(TIMEZONE),
            total_slots=len(available_slots),
            formatted_date=formatted_date
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in enhanced availability check: {e}")
        # Enhanced fallback with better mock data
        mock_slots = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
        formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%A, %B %d, %Y')
        
        return AvailabilityResponse(
            available_slots=mock_slots,
            date=date,
            timezone=str(TIMEZONE),
            total_slots=len(mock_slots),
            formatted_date=formatted_date
        )

@app.get(
    "/parse-datetime",
    tags=["Enhanced Features"],
    summary="Enhanced Date/Time Parsing",
    description="Test the enhanced natural language date and time parsing",
    response_model=DateTimeParseResponse
)
async def parse_datetime_endpoint(text: str = Query(..., description="Natural language text to parse")):
    """
    Test enhanced natural language parsing capabilities.
    
    Supports formats like:
    - "5th July at 3:30pm"
    - "tomorrow at 2 PM"
    - "next Monday morning"
    - "August 4th at 15:00"
    - "4th Augus 3:30pm" (handles typos)
    """
    try:
        if ENHANCED_MODULES_STATUS['advanced_parser']:
            # Use enhanced parser
            result = advanced_parser.parse_appointment_request(text)
            
            return DateTimeParseResponse(
                date=result.get('date'),
                time=result.get('time'),
                confidence=result.get('confidence', 0.0),
                original_text=result.get('original_text', text),
                parsed_components=result.get('parsing_details', []),
                suggestions=result.get('suggestions', []),
                parser_type="enhanced"
            )
        else:
            # Basic fallback parsing
            return DateTimeParseResponse(
                date=None,
                time=None,
                confidence=0.0,
                original_text=text,
                parsed_components=[],
                suggestions=["Enhanced parsing not available. Install enhanced modules for advanced parsing."],
                parser_type="basic"
            )
            
    except Exception as e:
        logger.error(f"Error in enhanced datetime parsing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enhanced parsing error: {str(e)}"
        )

@app.post(
    "/test-booking",
    tags=["Enhanced Features"],
    summary="Test Enhanced Booking Flow",
    description="Test the complete enhanced booking flow"
)
async def test_booking_endpoint(request: ChatMessage):
    """
    Test endpoint for the enhanced booking flow.
    
    This endpoint demonstrates the complete enhanced booking process
    without actually creating calendar events.
    """
    try:
        if ENHANCED_MODULES_STATUS['precise_scheduler']:
            result = await precise_scheduler.schedule_appointment(request.message, request.user_id)
            
            return {
                "test_mode": True,
                "parsing_result": result.get('parsing_result', {}),
                "booking_result": {
                    "success": result.get('success', False),
                    "message": result.get('message', ''),
                    "next_action": result.get('next_action', ''),
                    "appointment_details": result.get('appointment_details', {})
                },
                "available_slots": result.get('available_slots', []),
                "errors": result.get('errors', []),
                "suggestions": result.get('suggestions', [])
            }
        else:
            return {
                "test_mode": True,
                "error": "Enhanced scheduler not available",
                "message": "Please install enhanced modules for testing"
            }
            
    except Exception as e:
        logger.error(f"Error in test booking: {e}")
        return {
            "test_mode": True,
            "error": str(e),
            "message": "Test booking failed"
        }

# Enhanced error handlers
@app.exception_handler(HTTPException)
async def enhanced_http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now(TIMEZONE).isoformat(),
            "enhanced_features": ENHANCED_MODULES_STATUS,
            "suggestion": "Check /health endpoint for system status"
        }
    )

@app.exception_handler(Exception)
async def enhanced_general_exception_handler(request, exc):
    logger.error(f"Unhandled exception in enhanced API: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now(TIMEZONE).isoformat(),
            "enhanced_features": ENHANCED_MODULES_STATUS,
            "suggestion": "Please check logs and system configuration"
        }
    )

if __name__ == "__main__":
    print("🚀 Starting TailorTalk Enhanced AI Booking Agent API...")
    print("=" * 60)
    
    # System information
    print(f"📍 Timezone: {TIMEZONE}")
    print(f"📁 Credentials: {os.getenv('GOOGLE_CREDENTIALS_PATH', 'Not set')}")
    
    # OpenAI status
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key and openai_key != "your_openai_api_key_here":
        print(f"🤖 OpenAI API: Configured")
    else:
        print(f"🤖 OpenAI API: Not configured (using fallback)")
    
    # Enhanced features status
    print("\n🎯 Enhanced Features Status:")
    for feature, status in ENHANCED_MODULES_STATUS.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {feature.replace('_', ' ').title()}")
    
    # Determine active mode
    if ENHANCED_MODULES_STATUS['enhanced_agent']:
        print("\n🎉 Running in ENHANCED MODE with precise scheduling!")
    elif ENHANCED_MODULES_STATUS['openai_agent']:
        print("\n🤖 Running in OPENAI MODE")
    elif ENHANCED_MODULES_STATUS['fallback_agent']:
        print("\n🔄 Running in FALLBACK MODE")
    else:
        print("\n⚠️ Running in BASIC MODE")
    
    print("\n📡 Server Information:")
    print(f"   🌐 API: http://127.0.0.1:8001")
    print(f"   📚 Docs: http://127.0.0.1:8001/docs")
    print(f"   🔍 Health: http://127.0.0.1:8001/health")
    print(f"   🧪 Test Parsing: http://127.0.0.1:8001/parse-datetime")
    
    print("\n🎯 Ready for enhanced appointment booking!")
    print("=" * 60)
    
    uvicorn.run(
        "main_with_ai:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    )

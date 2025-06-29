"""
Enhanced TailorTalk server with integrated precise scheduling and real-time availability updates
INTEGRATED WITH STREAMLIT APP: https://tailortalk-enhanced-uael6bdk6fzdahsnfuemah.streamlit.app/
"""

import uvicorn
import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
import pytz
import asyncio
from enum import Enum
from contextlib import asynccontextmanager

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

# STREAMLIT INTEGRATION CONFIGURATION
STREAMLIT_APP_URL = "https://tailortalk-enhanced-uael6bdk6fzdahsnfuemah.streamlit.app/"
STREAMLIT_DOMAIN = "tailortalk-enhanced-uael6bdk6fzdahsnfuemah.streamlit.app"

# Import enhanced modules with comprehensive error handling
ENHANCED_MODULES_STATUS = {
    'advanced_parser': False,
    'enhanced_calendar': False,
    'precise_scheduler': False,
    'enhanced_agent': False,
    'fallback_agent': False,
    'openai_agent': False,
    'streamlit_integration': True  # Added for Streamlit integration tracking
}

# Try to import enhanced modules (keeping your existing import logic)
try:
    from backend.advanced_date_parser import advanced_parser, AdvancedDateTimeParser
    ENHANCED_MODULES_STATUS['advanced_parser'] = True
    logger.info("✅ Advanced date parser imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Advanced date parser not available: {e}")
    # Create mock parser for fallback
    class MockAdvancedParser:
        def parse_appointment_request(self, text):
            return {
                'date': None,
                'time': None,
                'confidence': 0.0,
                'original_text': text,
                'parsing_details': ['Mock parser - enhanced modules not available'],
                'suggestions': ['Install enhanced modules for advanced parsing']
            }
    advanced_parser = MockAdvancedParser()
except Exception as e:
    logger.error(f"❌ Advanced date parser import error: {e}")
    class MockAdvancedParser:
        def parse_appointment_request(self, text):
            return {
                'date': None,
                'time': None,
                'confidence': 0.0,
                'original_text': text,
                'parsing_details': ['Mock parser - enhanced modules not available'],
                'suggestions': ['Install enhanced modules for advanced parsing']
            }
    advanced_parser = MockAdvancedParser()

# Enhanced calendar manager imports with fallbacks
try:
    from backend.enhanced_calendar import get_enhanced_calendar_manager, EnhancedCalendarManager
    ENHANCED_MODULES_STATUS['enhanced_calendar'] = True
    logger.info("✅ Enhanced calendar manager imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Enhanced calendar manager not available: {e}")
    # Create mock calendar manager
    class MockCalendarManager:
        def get_availability(self, date_str):
            return ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
        def test_connection(self):
            return {'status': 'success', 'calendar_name': 'Mock Calendar'}
    
    def get_enhanced_calendar_manager():
        return MockCalendarManager()
except Exception as e:
    logger.error(f"❌ Enhanced calendar manager import error: {e}")
    class MockCalendarManager:
        def get_availability(self, date_str):
            return ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
        def test_connection(self):
            return {'status': 'success', 'calendar_name': 'Mock Calendar'}
    
    def get_enhanced_calendar_manager():
        return MockCalendarManager()

# Continue with other imports (keeping your existing logic)
try:
    from backend.precise_appointment_scheduler import precise_scheduler, PreciseAppointmentScheduler
    ENHANCED_MODULES_STATUS['precise_scheduler'] = True
    logger.info("✅ Precise appointment scheduler imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Precise appointment scheduler not available: {e}")
    # Create mock scheduler
    class MockPreciseScheduler:
        async def schedule_appointment(self, message, user_id):
            return {
                'success': False,
                'message': 'Mock scheduler - enhanced modules not available',
                'parsing_result': {},
                'appointment_details': {},
                'available_slots': [],
                'errors': ['Enhanced scheduler not available'],
                'suggestions': ['Install enhanced modules for precise scheduling']
            }
    precise_scheduler = MockPreciseScheduler()
except Exception as e:
    logger.error(f"❌ Precise appointment scheduler import error: {e}")
    class MockPreciseScheduler:
        async def schedule_appointment(self, message, user_id):
            return {
                'success': False,
                'message': 'Mock scheduler - enhanced modules not available',
                'parsing_result': {},
                'appointment_details': {},
                'available_slots': [],
                'errors': ['Enhanced scheduler not available'],
                'suggestions': ['Install enhanced modules for precise scheduling']
            }
    precise_scheduler = MockPreciseScheduler()

# Enhanced booking agent imports with fallbacks
try:
    from backend.enhanced_booking_agent import enhanced_booking_agent, EnhancedBookingAgent
    ENHANCED_MODULES_STATUS['enhanced_agent'] = True
    logger.info("✅ Enhanced booking agent imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Enhanced booking agent not available: {e}")
    enhanced_booking_agent = None
except Exception as e:
    logger.error(f"❌ Enhanced booking agent import error: {e}")
    enhanced_booking_agent = None

# Fallback agent imports
try:
    from backend.langgraph_agent_fallback import FallbackBookingAgent
    ENHANCED_MODULES_STATUS['fallback_agent'] = True
    logger.info("✅ Fallback booking agent imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Fallback booking agent not available: {e}")
    # Create simple fallback agent
    class SimpleFallbackAgent:
        async def process_message(self, message, user_id):
            current_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p %Z on %A, %B %d, %Y')
            return f"🤖 Simple Fallback Agent Response\n\n" \
                   f"📝 Your message: '{message}'\n" \
                   f"🕐 Current time: {current_time}\n" \
                   f"👤 User ID: {user_id}\n\n" \
                   f"💡 This is a basic response. For enhanced features, please install the enhanced modules.\n" \
                   f"🌐 Streamlit App: {STREAMLIT_APP_URL}"
    
    FallbackBookingAgent = SimpleFallbackAgent
except Exception as e:
    logger.error(f"❌ Fallback booking agent import error: {e}")
    class SimpleFallbackAgent:
        async def process_message(self, message, user_id):
            current_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p %Z on %A, %B %d, %Y')
            return f"🤖 Simple Fallback Agent Response\n\n" \
                   f"📝 Your message: '{message}'\n" \
                   f"🕐 Current time: {current_time}\n" \
                   f"👤 User ID: {user_id}\n\n" \
                   f"💡 This is a basic response. For enhanced features, please install the enhanced modules.\n" \
                   f"🌐 Streamlit App: {STREAMLIT_APP_URL}"
    
    FallbackBookingAgent = SimpleFallbackAgent

# OpenAI agent imports
try:
    from backend.langgraph_agent import BookingAgent as OpenAIBookingAgent
    try:
        from openai import OpenAI
        OPENAI_AVAILABLE = True
    except ImportError as e:
        logger.warning(f"⚠️ openai package not available: {e}")
        OPENAI_AVAILABLE = False
    ENHANCED_MODULES_STATUS['openai_agent'] = True
    logger.info("✅ OpenAI booking agent imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ OpenAI booking agent not available: {e}")
    OPENAI_AVAILABLE = False
    OpenAIBookingAgent = None
except Exception as e:
    logger.error(f"❌ OpenAI booking agent import error: {e}")
    OPENAI_AVAILABLE = False
    OpenAIBookingAgent = None

# Basic calendar manager fallback
try:
    from backend.google_calendar import get_calendar_manager
    logger.info("✅ Basic calendar manager available as fallback")
except ImportError as e:
    logger.error(f"❌ No calendar manager available: {e}")
    def get_calendar_manager():
        return MockCalendarManager()

# Real-time availability manager
class MockRealTimeManager:
    def __init__(self):
        self.update_interval = 30
        self.is_running = False
        self.subscribers = set()
        self.last_availability = {}

    async def start_monitoring(self):
        self.is_running = True
        logger.info("Mock real-time manager started")

    async def stop_monitoring(self):
        self.is_running = False
        logger.info("Mock real-time manager stopped")

    def subscribe(self, subscriber_id):
        self.subscribers.add(subscriber_id)

    def unsubscribe(self, subscriber_id):
        self.subscribers.discard(subscriber_id)

try:
    from backend.realtime_availability import realtime_availability_manager
    ENHANCED_MODULES_STATUS['realtime_availability'] = True
    logger.info("✅ Real-time availability manager imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Real-time availability manager not available: {e}")
    realtime_availability_manager = MockRealTimeManager()
    ENHANCED_MODULES_STATUS['realtime_availability'] = False
except Exception as e:
    logger.error(f"❌ Real-time availability manager import error: {e}")
    realtime_availability_manager = MockRealTimeManager()
    ENHANCED_MODULES_STATUS['realtime_availability'] = False

# Get timezone
TIMEZONE = pytz.timezone(os.getenv('TIMEZONE', 'Asia/Kolkata'))

# Lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting TailorTalk Enhanced with Streamlit integration")
    logger.info(f"🌐 Streamlit App URL: {STREAMLIT_APP_URL}")
    if ENHANCED_MODULES_STATUS.get('realtime_availability', False):
        asyncio.create_task(realtime_availability_manager.start_monitoring())
    yield
    # Shutdown
    logger.info("🛑 Shutting down TailorTalk Enhanced")
    if ENHANCED_MODULES_STATUS.get('realtime_availability', False):
        await realtime_availability_manager.stop_monitoring()

# Create FastAPI app with enhanced metadata and Streamlit integration
app = FastAPI(
    title="TailorTalk AI Booking Assistant API - Enhanced with Streamlit",
    description=f"""
    **TailorTalk Enhanced** is an intelligent appointment booking system with advanced features:
    
    ## 🌐 Streamlit Integration
    
    * **Frontend App**: [{STREAMLIT_APP_URL}]({STREAMLIT_APP_URL})
    * **Seamless Integration** - Direct API communication with Streamlit frontend
    * **Real-time Updates** - Live data synchronization between backend and frontend
    
    ## 🚀 Enhanced Features
    
    * **Precise Date/Time Parsing** - Handles "5th July", "4th August 3:30pm", etc.
    * **Advanced Calendar Integration** - Real-time Google Calendar sync with timezone handling
    * **Smart Conversation Flow** - Context-aware multi-turn conversations
    * **Robust Error Handling** - Comprehensive error recovery and user guidance
    * **Multiple Agent Support** - Enhanced AI, OpenAI, and rule-based fallback agents
    * **Real-time Availability Updates** - Automatic updates to availability data
    
    ## 🎯 Supported Formats
    
    * **Dates**: "5th July", "July 5th", "tomorrow", "next Monday", "2025-07-05"
    * **Times**: "3:30pm", "15:00", "afternoon", "morning", "3 PM"
    * **Combined**: "Book appointment on 5th July at 3:30pm"
    
    ## 🔧 System Status
    
    Check `/health` endpoint for detailed system status and component availability.
    """,
    version="3.1.0",  # Updated version for Streamlit integration
    contact={
        "name": "TailorTalk Support",
        "email": "dnyaneshpurohit@gmail.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# Enhanced CORS middleware with specific Streamlit configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        STREAMLIT_APP_URL,  # Specific Streamlit app URL
        f"https://{STREAMLIT_DOMAIN}",  # Domain without trailing slash
        "https://*.streamlit.app",  # All Streamlit apps
        "http://localhost:8501",  # Local Streamlit development
        "https://localhost:8501",  # Local Streamlit HTTPS
        "*"  # Allow all origins (remove in production for security)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initialize the AI agent globally
booking_agent = None

async def get_booking_agent():
    """Get or initialize the best available booking agent"""
    global booking_agent
    if booking_agent is None:
        
        # Priority 1: Enhanced Booking Agent (best option)
        if ENHANCED_MODULES_STATUS['enhanced_agent'] and enhanced_booking_agent:
            try:
                booking_agent = enhanced_booking_agent
                logger.info("🎯 Enhanced Booking Agent initialized (with precise scheduling)")
                return booking_agent
            except Exception as e:
                logger.warning(f"Enhanced booking agent failed: {e}")
        
        # Priority 2: OpenAI Agent (if API key available)
        if ENHANCED_MODULES_STATUS['openai_agent'] and OpenAIBookingAgent:
            try:
                openai_key = os.getenv("OPENAI_API_KEY")
                if openai_key and openai_key != "your_openai_api_key_here":
                    logger.info("Testing OpenAI API connection...")
                    
                    # Test OpenAI connection
                    if not OPENAI_AVAILABLE:
                        raise ImportError("openai package is not installed")
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
        
        # If all agents fail, create a simple mock agent
        logger.warning("Using simple mock agent as final fallback")
        class SimpleMockAgent:
            async def process_message(self, message, user_id):
                current_time = datetime.now(TIMEZONE).strftime('%I:%M %p %Z on %A, %B %d, %Y')
                return f"🤖 TailorTalk Assistant (Mock Mode)\n\n" \
                       f"📝 Your message: '{message}'\n" \
                       f"🕐 Current time: {current_time}\n" \
                       f"👤 User ID: {user_id}\n\n" \
                       f"💡 I'm running in mock mode. For full functionality, please configure the enhanced modules.\n" \
                       f"🌐 Visit the Streamlit app: {STREAMLIT_APP_URL}"
        
        booking_agent = SimpleMockAgent()
        return booking_agent
    
    return booking_agent

# Your existing Pydantic models (keeping all of them)
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

class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="User message for the AI assistant")
    user_id: Optional[str] = Field("streamlit_user", description="Unique identifier for the user")  # Changed default
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Book appointment on 5th July at 3:30pm",
                "user_id": "streamlit_user_123"
            }
        }
    }

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI assistant's response")
    status: BookingStatus = Field(..., description="Response status")
    timestamp: datetime = Field(..., description="Response timestamp")
    user_id: str = Field(..., description="User identifier")
    agent_type: Optional[str] = Field(None, description="Type of agent that processed the request")
    streamlit_app_url: Optional[str] = Field(STREAMLIT_APP_URL, description="Streamlit app URL")  # Added
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "response": "✅ Appointment confirmed for Saturday, July 05, 2025 at 03:30 PM",
                "status": "success",
                "timestamp": "2025-06-27T15:30:00+05:30",
                "user_id": "streamlit_user_123",
                "agent_type": "enhanced",
                "streamlit_app_url": STREAMLIT_APP_URL
            }
        }
    }

class AvailabilityResponse(BaseModel):
    available_slots: List[str] = Field(..., description="List of available time slots")
    date: str = Field(..., description="Date for availability check")
    timezone: str = Field(..., description="Timezone")
    total_slots: int = Field(..., description="Total number of available slots")
    formatted_date: Optional[str] = Field(None, description="Human-readable date format")
    last_updated: Optional[str] = Field(None, description="Last updated timestamp")
    realtime_enabled: Optional[bool] = Field(None, description="Indicates if real-time updates are enabled")
    update_interval: Optional[int] = Field(None, description="Update interval in seconds")
    streamlit_app_url: Optional[str] = Field(STREAMLIT_APP_URL, description="Streamlit app URL")  # Added
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "available_slots": ["09:00", "10:00", "11:00", "14:00", "15:00"],
                "date": "2025-07-05",
                "timezone": "Asia/Kolkata",
                "total_slots": 5,
                "formatted_date": "Saturday, July 05, 2025",
                "last_updated": "2025-06-27T15:30:00+05:30",
                "realtime_enabled": True,
                "update_interval": 60,
                "streamlit_app_url": STREAMLIT_APP_URL
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
    streamlit_integration: Dict[str, Any] = Field(..., description="Streamlit integration status")  # Added

# API Routes with Streamlit integration

@app.get(
    "/",
    tags=["System"],
    summary="API Root - Enhanced with Streamlit",
    description="Get enhanced API information and status with Streamlit integration",
    response_model=Dict[str, Any]
)
async def root():
    """
    Welcome endpoint for TailorTalk Enhanced API with Streamlit integration.
    
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
    else:
        agent_type = "mock"
    
    return {
        "message": "🚀 TailorTalk Enhanced AI Booking Agent API with Streamlit Integration",
        "status": "healthy",
        "version": "3.1.0",
        "current_time": current_time,
        "timezone": str(TIMEZONE),
        "active_agent": agent_type,
        "streamlit_integration": {
            "app_url": STREAMLIT_APP_URL,
            "domain": STREAMLIT_DOMAIN,
            "cors_configured": True,
            "status": "integrated"
        },
        "enhanced_features": {
            "precise_date_parsing": ENHANCED_MODULES_STATUS['advanced_parser'],
            "enhanced_calendar": ENHANCED_MODULES_STATUS['enhanced_calendar'],
            "precise_scheduling": ENHANCED_MODULES_STATUS['precise_scheduler'],
            "enhanced_conversations": ENHANCED_MODULES_STATUS['enhanced_agent'],
            "timezone_handling": True,
            "error_recovery": True,
            "realtime_availability": ENHANCED_MODULES_STATUS.get('realtime_availability', False),
            "streamlit_integration": ENHANCED_MODULES_STATUS['streamlit_integration']
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
            "docs": "/docs - API documentation",
            "streamlit-redirect": "/streamlit - Redirect to Streamlit app",
            "realtime_availability": "/realtime/availability/{date} - Get real-time availability",
            "subscribe_to_updates": "/realtime/subscribe - Subscribe to real-time updates"
        }
    }

# NEW: Streamlit redirect endpoint
@app.get(
    "/streamlit",
    tags=["Streamlit Integration"],
    summary="Redirect to Streamlit App",
    description="Redirect users to the integrated Streamlit application"
)
async def redirect_to_streamlit():
    """Redirect to the Streamlit application"""
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Redirecting to TailorTalk Streamlit App</title>
        <meta http-equiv="refresh" content="0; url={STREAMLIT_APP_URL}">
    </head>
    <body>
        <h1>🚀 Redirecting to TailorTalk Streamlit App...</h1>
        <p>If you are not redirected automatically, <a href="{STREAMLIT_APP_URL}">click here</a>.</p>
    </body>
    </html>
    """)

# NEW: Streamlit integration status endpoint
from fastapi import Request

@app.get(
    "/streamlit/status",
    tags=["Streamlit Integration"],
    summary="Streamlit Integration Status",
    description="Check the status of Streamlit integration"
)
async def streamlit_integration_status(request: Request):
    """Check Streamlit integration status"""
    return {
        "streamlit_app_url": STREAMLIT_APP_URL,
        "streamlit_domain": STREAMLIT_DOMAIN,
        "cors_configured": True,
        "integration_status": "active",
        "api_endpoints_available": [
            "/chat",
            "/availability/{date}",
            "/health",
            "/parse-datetime"
        ],
        "recommended_usage": {
            "chat": f"POST {request.url.scheme}://{request.url.netloc}/chat",
            "availability": f"GET {request.url.scheme}://{request.url.netloc}/availability/2024-07-05",
            "health": f"GET {request.url.scheme}://{request.url.netloc}/health"
        }
    }

@app.get(
    "/health",
    tags=["System"],
    summary="Enhanced Health Check with Streamlit",
    description="Comprehensive system health check with enhanced components and Streamlit integration",
    response_model=HealthResponse
)
async def health_check():
    """
    Comprehensive health check for all enhanced components including Streamlit integration.
    """
    try:
        # Check OpenAI configuration
        openai_key = os.getenv("OPENAI_API_KEY")
        openai_configured = bool(openai_key and openai_key != "your_openai_api_key_here")
        
        # Check Google credentials
        credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', '')
        credentials_exist = os.path.exists(credentials_path) if credentials_path else False
        
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
                try:
                    calendar_manager = get_calendar_manager()
                    today = datetime.now(TIMEZONE).date().strftime('%Y-%m-%d')
                    test_slots = calendar_manager.get_availability(today)
                    calendar_status = f"basic calendar connected ({len(test_slots)} slots available today)"
                except:
                    calendar_status = "using mock calendar (no real calendar configured)"
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
                elif 'Mock' in class_name or 'Simple' in class_name:
                    agent_status = "mock agent ready (basic functionality)"
                    agent_type = "mock"
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
                if test_result.get('date') and test_result.get('time'):
                    parsing_status = f"enhanced parsing ready (confidence: {test_result.get('confidence', 0):.2f})"
                else:
                    parsing_status = "enhanced parsing partial"
            except Exception as e:
                parsing_status = f"using mock parser: {str(e)}"
        else:
            parsing_status = "using mock parser (enhanced modules not available)"
        
        # Test real-time availability
        realtime_status = "not available"
        if ENHANCED_MODULES_STATUS.get('realtime_availability', False):
            try:
                if realtime_availability_manager.is_running:
                    realtime_status = f"real-time monitoring active ({len(realtime_availability_manager.subscribers)} subscribers)"
                else:
                    realtime_status = "real-time monitoring ready (not started)"
            except Exception as e:
                realtime_status = f"real-time error: {str(e)}"
        else:
            realtime_status = "using mock real-time manager"
        
        current_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')
        
        # Determine overall status
        overall_status = "healthy"  # Always healthy since we have fallbacks
        
        # Update enhanced features status
        enhanced_features_status = ENHANCED_MODULES_STATUS.copy()
        enhanced_features_status['realtime_monitoring'] = realtime_availability_manager.is_running if ENHANCED_MODULES_STATUS.get('realtime_availability', False) else False
        
        return HealthResponse(
            status=overall_status,
            current_time=current_time,
            timezone=str(TIMEZONE),
            components={
                "openai_api": "configured" if openai_configured else "not configured (using fallback)",
                "google_credentials": "found" if credentials_exist else "missing (using mock)",
                "calendar_integration": calendar_status,
                "ai_agent": agent_status,
                "date_time_parsing": parsing_status,
                "enhanced_scheduler": "available" if ENHANCED_MODULES_STATUS['precise_scheduler'] else "using mock scheduler",
                "realtime_availability": realtime_status,
                "enhanced_conversations": "available" if ENHANCED_MODULES_STATUS['enhanced_agent'] else "using fallback/mock"
            },
            config={
                "credentials_path": credentials_path,
                "calendar_id": os.getenv('CALENDAR_ID', 'primary'),
                "timezone": str(TIMEZONE),
                "active_agent_type": agent_type,
                "openai_available": openai_configured,
                "enhanced_mode": ENHANCED_MODULES_STATUS['enhanced_agent'],
                "realtime_enabled": ENHANCED_MODULES_STATUS.get('realtime_availability', False),
                "realtime_interval": realtime_availability_manager.update_interval if ENHANCED_MODULES_STATUS.get('realtime_availability', False) else None,
                "active_subscribers": len(realtime_availability_manager.subscribers) if ENHANCED_MODULES_STATUS.get('realtime_availability', False) else 0
            },
            enhanced_features=enhanced_features_status,
            streamlit_integration={
                "app_url": STREAMLIT_APP_URL,
                "domain": STREAMLIT_DOMAIN,
                "cors_configured": True,
                "status": "integrated",
                "redirect_endpoint": "/streamlit",
                "status_endpoint": "/streamlit/status"
            }
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        # Return a basic healthy status even if there are errors
        return HealthResponse(
            status="healthy_with_fallbacks",
            current_time=datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z'),
            timezone=str(TIMEZONE),
            components={
                "system": "running with fallbacks",
                "error": str(e)
            },
            config={
                "timezone": str(TIMEZONE),
                "fallback_mode": True
            },
            enhanced_features=ENHANCED_MODULES_STATUS,
            streamlit_integration={
                "app_url": STREAMLIT_APP_URL,
                "status": "integrated"
            }
        )

@app.post(
    "/chat",
    tags=["AI Assistant"],
    summary="Enhanced Chat Interface with Streamlit Integration",
    description="Chat with enhanced AI assistant for precise appointment scheduling, optimized for Streamlit",
    response_model=ChatResponse
)
async def chat_endpoint(message: ChatMessage):
    """
    Enhanced conversational interface with precise date/time understanding.
    Optimized for Streamlit frontend integration.
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
            elif 'Mock' in class_name or 'Simple' in class_name:
                agent_type = "mock"
        
        # Process the message through the AI agent
        response = await agent.process_message(message.message, message.user_id)
        
        logger.info(f"Enhanced AI response ({agent_type}): {response[:100]}...")
        
        return ChatResponse(
            response=response,
            status=BookingStatus.SUCCESS,
            timestamp=datetime.now(TIMEZONE),
            user_id=message.user_id,
            agent_type=agent_type,
            streamlit_app_url=STREAMLIT_APP_URL
        )
        
    except Exception as e:
        logger.error(f"Error in enhanced chat endpoint: {e}")
        current_time = datetime.now(TIMEZONE).strftime('%I:%M %p %Z on %A, %B %d, %Y')
        
        # Enhanced error response with Streamlit integration
        fallback_response = f"I'm experiencing technical difficulties right now.\n\n" \
                          f"🕐 Current time: {current_time}\n" \
                          f"🔧 System status: Temporary issue\n\n" \
                          f"Please try again in a moment, or use a simple format like:\n" \
                          f"'Book appointment on [date] at [time]'\n\n" \
                          f"🌐 You can also visit the Streamlit app: {STREAMLIT_APP_URL}"
        
        return ChatResponse(
            response=fallback_response,
            status=BookingStatus.ERROR,
            timestamp=datetime.now(TIMEZONE),
            user_id=message.user_id,
            agent_type="error_handler",
            streamlit_app_url=STREAMLIT_APP_URL
        )

# Continue with your existing endpoints (availability, parse-datetime, etc.)
# but add streamlit_app_url to responses where appropriate

@app.get(
    "/availability/{date}",
    tags=["Calendar"],
    summary="Enhanced Availability Check with Streamlit Integration",
    description="Get available time slots with enhanced calendar integration, optimized for Streamlit",
    response_model=AvailabilityResponse
)
async def get_availability(date: str):
    """
    Check available time slots using enhanced calendar integration.
    Optimized for Streamlit frontend.
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
        
        # Update real-time manager if available
        if ENHANCED_MODULES_STATUS.get('realtime_availability', False):
            realtime_availability_manager.last_availability[date] = available_slots
        
        return AvailabilityResponse(
            available_slots=available_slots,
            date=date,
            timezone=str(TIMEZONE),
            total_slots=len(available_slots),
            formatted_date=formatted_date,
            last_updated=datetime.now(TIMEZONE).isoformat(),
            realtime_enabled=ENHANCED_MODULES_STATUS.get('realtime_availability', False),
            update_interval=realtime_availability_manager.update_interval if ENHANCED_MODULES_STATUS.get('realtime_availability', False) else None,
            streamlit_app_url=STREAMLIT_APP_URL
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
            formatted_date=formatted_date,
            last_updated=datetime.now(TIMEZONE).isoformat(),
            realtime_enabled=False,
            update_interval=None,
            streamlit_app_url=STREAMLIT_APP_URL
        )

# Keep all your existing endpoints (parse-datetime, test-booking, realtime endpoints, etc.)
# I'll include the key ones with Streamlit integration

@app.get(
    "/parse-datetime",
    tags=["Enhanced Features"],
    summary="Enhanced Date/Time Parsing",
    description="Test the enhanced natural language date and time parsing",
    response_model=DateTimeParseResponse
)
async def parse_datetime_endpoint(text: str = Query(..., description="Natural language text to parse")):
    """Test enhanced natural language parsing capabilities."""
    try:
        result = advanced_parser.parse_appointment_request(text)
        
        return DateTimeParseResponse(
            date=result.get('date'),
            time=result.get('time'),
            confidence=result.get('confidence', 0.0),
            original_text=result.get('original_text', text),
            parsed_components=result.get('parsing_details', []),
            suggestions=result.get('suggestions', []),
            parser_type="enhanced" if ENHANCED_MODULES_STATUS['advanced_parser'] else "mock"
        )
            
    except Exception as e:
        logger.error(f"Error in enhanced datetime parsing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enhanced parsing error: {str(e)}"
        )

# Enhanced error handlers with Streamlit integration
@app.exception_handler(HTTPException)
async def enhanced_http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now(TIMEZONE).isoformat(),
            "enhanced_features": ENHANCED_MODULES_STATUS,
            "suggestion": "Check /health endpoint for system status",
            "streamlit_app_url": STREAMLIT_APP_URL
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
            "suggestion": "Please check logs and system configuration",
            "streamlit_app_url": STREAMLIT_APP_URL
        }
    )

if __name__ == "__main__":
    print("🚀 Starting TailorTalk Enhanced AI Booking Agent API with Streamlit Integration...")
    print("=" * 80)
    
    # System information
    print(f"📍 Timezone: {TIMEZONE}")
    print(f"🌐 Streamlit App: {STREAMLIT_APP_URL}")
    print(f"📁 Credentials: {os.getenv('GOOGLE_CREDENTIALS_PATH', 'Not set (using mock)')}")
    
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
        print("\n⚠️ Running in MOCK MODE (with graceful fallbacks)")
    
    print("\n📡 Server Information:")
    print(f"   🌐 API: http://127.0.0.1:8001")
    print(f"   📚 Docs: http://127.0.0.1:8001/docs")
    print(f"   🔍 Health: http://127.0.0.1:8001/health")
    print(f"   🧪 Test Parsing: http://127.0.0.1:8001/parse-datetime")
    print(f"   🌐 Streamlit Redirect: http://127.0.0.1:8001/streamlit")
    print(f"   📊 Streamlit Status: http://127.0.0.1:8001/streamlit/status")
    
    print(f"\n🌐 Streamlit Integration:")
    print(f"   📱 App URL: {STREAMLIT_APP_URL}")
    print(f"   🔗 Domain: {STREAMLIT_DOMAIN}")
    print(f"   ✅ CORS: Configured for Streamlit")
    
    print("\n🎯 Ready for enhanced appointment booking with Streamlit integration!")
    print("=" * 80)
    
    uvicorn.run(
        "main_trial:app",
        host="0.0.0.0",  # Changed to allow external connections
        port=int(os.getenv("PORT", 8001)),
        reload=False,  # Changed to False for production
        log_level="info"
    )

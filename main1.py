"""
Enhanced TailorTalk FastAPI Application with Google Authentication
Main application file with comprehensive Google account integration
"""
import os
import sys
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
import pytz
import uvicorn
from pathlib import Path

# FastAPI imports
from fastapi import FastAPI, HTTPException, Depends, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Import our enhanced modules
try:
    from backend.google_auth_manager import google_auth_manager
    from backend.multi_user_calendar import multi_user_calendar_manager
    from backend.secure_user_agent import secure_user_booking_agent
    from backend.advanced_date_parser import advanced_parser
    from backend.error_handler import error_handler
    from backend.monitoring import system_monitor
    from backend.timezone_manager import timezone_manager
    from auth_endpoints import auth_router
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all backend modules are properly installed")
    sys.exit(1)

# Configure logging with Windows-compatible format (no emojis)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/tailortalk_enhanced.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Ensure required directories exist
required_dirs = ['logs', 'auth_data', 'config', 'static']
for dir_name in required_dirs:
    Path(dir_name).mkdir(exist_ok=True)

# Global state for system components
system_state = {
    'auth_manager': None,
    'calendar_manager': None,
    'booking_agent': None,
    'parser': None,
    'monitor': None,
    'startup_time': None,
    'active_users': set(),
    'total_requests': 0,
    'successful_bookings': 0
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with startup and shutdown events"""
    
    # Startup
    logger.info("Starting TailorTalk Enhanced with Google Authentication...")
    
    try:
        # Initialize timezone
        timezone_manager.set_timezone('Asia/Kolkata')
        logger.info(f"Timezone set to: {timezone_manager.get_current_timezone()}")
        
        # Initialize system components
        system_state['auth_manager'] = google_auth_manager
        system_state['calendar_manager'] = multi_user_calendar_manager
        system_state['booking_agent'] = secure_user_booking_agent
        system_state['parser'] = advanced_parser
        system_state['monitor'] = system_monitor
        system_state['startup_time'] = datetime.now(pytz.timezone('Asia/Kolkata'))
        
        # Test Google credentials
        credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'config/credentials.json')
        if not os.path.exists(credentials_path):
            logger.warning(f"Google credentials not found at: {credentials_path}")
            logger.warning("Please run: python config/setup_google_credentials.py")
        else:
            logger.info(f"Google credentials found at: {credentials_path}")
        
        # Start background tasks
        asyncio.create_task(cleanup_expired_sessions())
        asyncio.create_task(monitor_system_health())
        
        logger.info("TailorTalk Enhanced startup completed successfully!")
        logger.info("Available endpoints:")
        logger.info("   - Authentication: /auth/*")
        logger.info("   - Chat: /chat")
        logger.info("   - Health: /health")
        logger.info("   - Docs: /docs")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down TailorTalk Enhanced...")
    
    try:
        # Cleanup expired sessions
        cleaned_sessions = google_auth_manager.cleanup_expired_sessions()
        logger.info(f"Cleaned up {cleaned_sessions} expired sessions")
        
        # Log final statistics
        uptime = datetime.now(pytz.timezone('Asia/Kolkata')) - system_state['startup_time']
        logger.info(f"Final Statistics:")
        logger.info(f"   - Uptime: {uptime}")
        logger.info(f"   - Total requests: {system_state['total_requests']}")
        logger.info(f"   - Successful bookings: {system_state['successful_bookings']}")
        logger.info(f"   - Active users: {len(system_state['active_users'])}")
        
        logger.info("TailorTalk Enhanced shutdown completed")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

# Create FastAPI application
app = FastAPI(
    title="TailorTalk Enhanced",
    description="AI-Powered Google Calendar Booking Assistant with Secure Authentication",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication router
app.include_router(auth_router)

# Serve static files
if Path("static").exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models
class ChatMessage(BaseModel):
    message: str = Field(..., description="User message")
    user_id: str = Field(..., description="Unique user identifier")
    session_id: Optional[str] = Field(None, description="Optional session identifier")

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI assistant response")
    user_id: str = Field(..., description="User identifier")
    timestamp: str = Field(..., description="Response timestamp")
    authenticated: bool = Field(..., description="User authentication status")
    session_info: Optional[Dict[str, Any]] = Field(None, description="Session information")

class AvailabilityRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    date: str = Field(..., description="Date in YYYY-MM-DD format")

class AvailabilityResponse(BaseModel):
    user_id: str
    date: str
    available_slots: List[str]
    total_slots: int
    user_info: Optional[Dict[str, Any]] = None

class BookingRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    time: str = Field(..., description="Time in HH:MM format")
    title: Optional[str] = Field("TailorTalk Appointment", description="Appointment title")
    description: Optional[str] = Field("", description="Appointment description")
    duration: Optional[int] = Field(60, description="Duration in minutes")

class BookingResponse(BaseModel):
    success: bool
    user_id: str
    event_id: Optional[str] = None
    event_link: Optional[str] = None
    message: str
    booking_details: Optional[Dict[str, Any]] = None

# Dependency to check user authentication
async def get_authenticated_user(user_id: str) -> Dict[str, Any]:
    """Dependency to verify user authentication"""
    try:
        credentials = google_auth_manager.get_user_credentials(user_id)
        
        if not credentials or not credentials.valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated or credentials expired"
            )
        
        user_info = google_auth_manager.get_user_info(user_id)
        return {
            'user_id': user_id,
            'credentials': credentials,
            'user_info': user_info
        }
        
    except Exception as e:
        logger.error(f"Authentication check failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

# Background tasks
async def cleanup_expired_sessions():
    """Background task to cleanup expired sessions"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            cleaned = google_auth_manager.cleanup_expired_sessions()
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired sessions")
        except Exception as e:
            logger.error(f"Error in session cleanup: {e}")

async def monitor_system_health():
    """Background task to monitor system health"""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            
            # Update system statistics
            authenticated_users = len(google_auth_manager.list_authenticated_users())
            active_sessions = len(google_auth_manager.active_sessions)
            
            logger.debug(f"System Health: {authenticated_users} users, {active_sessions} sessions")
            
        except Exception as e:
            logger.error(f"Error in health monitoring: {e}")

# API Endpoints

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with application information"""
    
    uptime = datetime.now(pytz.timezone('Asia/Kolkata')) - system_state['startup_time']
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>TailorTalk Enhanced</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                min-height: 100vh;
                color: white;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 40px;
                backdrop-filter: blur(10px);
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }}
            h1 {{
                text-align: center;
                font-size: 3em;
                margin-bottom: 10px;
            }}
            .subtitle {{
                text-align: center;
                font-size: 1.2em;
                opacity: 0.9;
                margin-bottom: 30px;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            .stat-card {{
                background: rgba(255, 255, 255, 0.2);
                padding: 20px;
                border-radius: 10px;
                text-align: center;
            }}
            .stat-number {{
                font-size: 2em;
                font-weight: bold;
                display: block;
            }}
            .endpoints {{
                background: rgba(255, 255, 255, 0.1);
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }}
            .endpoint {{
                margin: 10px 0;
                padding: 10px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 5px;
            }}
            a {{
                color: #fff;
                text-decoration: none;
                font-weight: bold;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>TailorTalk Enhanced</h1>
            <p class="subtitle">AI-Powered Google Calendar Booking Assistant</p>
            
            <div class="stats">
                <div class="stat-card">
                    <span class="stat-number">{len(google_auth_manager.list_authenticated_users())}</span>
                    <span>Authenticated Users</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{len(google_auth_manager.active_sessions)}</span>
                    <span>Active Sessions</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{system_state['total_requests']}</span>
                    <span>Total Requests</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{uptime.days}d {uptime.seconds//3600}h</span>
                    <span>Uptime</span>
                </div>
            </div>
            
            <div class="endpoints">
                <h3>Available Endpoints</h3>
                <div class="endpoint">
                    <strong>Streamlit UI:</strong> <a href="http://localhost:8501" target="_blank">http://localhost:8501</a>
                </div>
                <div class="endpoint">
                    <strong>API Documentation:</strong> <a href="/docs" target="_blank">/docs</a>
                </div>
                <div class="endpoint">
                    <strong>Authentication:</strong> <a href="/auth/health">/auth/*</a>
                </div>
                <div class="endpoint">
                    <strong>Health Check:</strong> <a href="/health">/health</a>
                </div>
                <div class="endpoint">
                    <strong>Chat API:</strong> <a href="/docs#/default/chat_endpoint_chat_post">/chat</a>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <p><strong>Secure Google Authentication</strong> | <strong>Calendar Integration</strong> | <strong>AI Assistant</strong></p>
                <p>Built with FastAPI, LangGraph, and Google Calendar API</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatMessage,
    background_tasks: BackgroundTasks,
    authenticated_user: Dict[str, Any] = Depends(lambda: None)
):
    """
    Main chat endpoint for AI assistant interaction
    Handles both authenticated and unauthenticated users
    """
    try:
        # Increment request counter
        system_state['total_requests'] += 1
        
        # Check if user is authenticated
        is_authenticated = False
        user_info = {}
        
        try:
            authenticated_user = await get_authenticated_user(request.user_id)
            is_authenticated = True
            user_info = authenticated_user['user_info']
            system_state['active_users'].add(request.user_id)
        except HTTPException:
            # User not authenticated - will get auth prompt
            pass
        
        # Process message with secure user agent
        response_text = await secure_user_booking_agent.process_user_message(
            request.message, 
            request.user_id
        )
        
        # Create response
        response = ChatResponse(
            response=response_text,
            user_id=request.user_id,
            timestamp=datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
            authenticated=is_authenticated,
            session_info={
                'user_info': user_info,
                'session_id': request.session_id,
                'message_count': system_state['total_requests']
            } if is_authenticated else None
        )
        
        # Log interaction
        logger.info(f"Chat interaction - User: {request.user_id[:8]}..., Auth: {is_authenticated}")
        
        return response
        
    except Exception as e:
        logger.error(f"Chat endpoint error for user {request.user_id}: {e}")
        
        error_response = ChatResponse(
            response=f"I'm experiencing technical difficulties. Please try again.\n\nError: {str(e)}",
            user_id=request.user_id,
            timestamp=datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
            authenticated=False
        )
        
        return error_response

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        uptime = current_time - system_state['startup_time']
        
        # Check system components
        components_status = {
            'auth_manager': 'healthy' if system_state['auth_manager'] else 'error',
            'calendar_manager': 'healthy' if system_state['calendar_manager'] else 'error',
            'booking_agent': 'healthy' if system_state['booking_agent'] else 'error',
            'parser': 'healthy' if system_state['parser'] else 'error',
            'monitor': 'healthy' if system_state['monitor'] else 'error'
        }
        
        # Check Google credentials
        credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'config/credentials.json')
        google_credentials_status = 'healthy' if os.path.exists(credentials_path) else 'missing'
        
        # Get authentication statistics
        authenticated_users = google_auth_manager.list_authenticated_users()
        active_sessions = len(google_auth_manager.active_sessions)
        
        # Overall health status
        overall_status = 'healthy' if all(
            status == 'healthy' for status in components_status.values()
        ) and google_credentials_status == 'healthy' else 'degraded'
        
        health_data = {
            'status': overall_status,
            'timestamp': current_time.isoformat(),
            'uptime': str(uptime),
            'uptime_seconds': uptime.total_seconds(),
            'version': '2.0.0',
            'components': components_status,
            'google_credentials': google_credentials_status,
            'statistics': {
                'authenticated_users': len(authenticated_users),
                'active_sessions': active_sessions,
                'total_requests': system_state['total_requests'],
                'successful_bookings': system_state['successful_bookings'],
                'active_users_count': len(system_state['active_users'])
            },
            'system_info': {
                'timezone': str(timezone_manager.get_current_timezone()),
                'startup_time': system_state['startup_time'].isoformat(),
                'python_version': sys.version,
                'platform': sys.platform
            },
            'endpoints': {
                'authentication': '/auth/*',
                'chat': '/chat',
                'availability': '/availability',
                'booking': '/book',
                'documentation': '/docs'
            }
        }
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            'status': 'error',
            'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
            'error': str(e),
            'message': 'Health check failed'
        }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc} - {request.url}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
            "path": str(request.url)
        }
    )

# Main execution
if __name__ == "__main__":
    # Environment configuration
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", 8001))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting TailorTalk Enhanced server...")
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Debug: {debug}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Check for Google credentials
    credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'config/credentials.json')
    if not os.path.exists(credentials_path):
        logger.warning("Google credentials not found!")
        logger.warning("Please run: python config/setup_google_credentials.py")
        logger.warning("Or place your credentials.json file in the config/ directory")
    
    # Start server
    uvicorn.run(
        "main1:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug",
        access_log=True
    )

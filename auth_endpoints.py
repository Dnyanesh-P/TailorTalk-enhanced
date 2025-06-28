"""
Authentication endpoints for TailorTalk Enhanced
Handles Google OAuth2 flow and user session management
"""
import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from backend.google_auth_manager import google_auth_manager

logger = logging.getLogger(__name__)

# Create router
auth_router = APIRouter(prefix="/auth", tags=["authentication"])

# Pydantic models
class AuthInitiateRequest(BaseModel):
    redirect_uri: str = "http://localhost:8001/auth/callback"

class AuthStatusResponse(BaseModel):
    authenticated: bool
    user_id: str = None
    user_info: Dict[str, Any] = None
    message: str

class AuthStatsResponse(BaseModel):
    total_users: int
    active_sessions: int
    authenticated_users: list

@auth_router.post("/initiate")
async def initiate_auth(request: AuthInitiateRequest):
    """Initiate Google OAuth2 authentication flow"""
    try:
        # Generate authorization URL
        auth_url, state = google_auth_manager.get_authorization_url(request.redirect_uri)
        
        # Record authentication attempt
        logger.info(f"Authentication initiated with state: {state[:8]}...")
        
        return {
            "success": True,
            "auth_url": auth_url,
            "state": state,
            "message": "Please visit the auth_url to complete authentication"
        }
        
    except Exception as e:
        logger.error(f"Failed to initiate authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication initiation failed: {str(e)}"
        )

@auth_router.get("/login", response_class=HTMLResponse)
async def login_page():
    """Display login page with Google OAuth2 link"""
    try:
        auth_url = google_auth_manager.get_auth_url()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>TailorTalk - Google Authentication</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .container {{
                    background: white;
                    border-radius: 15px;
                    padding: 40px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 500px;
                    width: 100%;
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 20px;
                }}
                .subtitle {{
                    color: #666;
                    margin-bottom: 30px;
                    line-height: 1.6;
                }}
                .google-btn {{
                    background: #4285f4;
                    color: white;
                    padding: 15px 30px;
                    border: none;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: 500;
                    text-decoration: none;
                    display: inline-flex;
                    align-items: center;
                    gap: 10px;
                    transition: background 0.3s;
                }}
                .google-btn:hover {{
                    background: #3367d6;
                }}
                .features {{
                    margin-top: 30px;
                    text-align: left;
                }}
                .feature {{
                    margin: 10px 0;
                    color: #555;
                }}
                .security {{
                    margin-top: 30px;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    font-size: 14px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 TailorTalk Enhanced</h1>
                <p class="subtitle">
                    Connect your Google Calendar to start booking appointments with our AI assistant.
                </p>
                
                <a href="{auth_url}" class="google-btn">
                    <svg width="20" height="20" viewBox="0 0 24 24">
                        <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    Sign in with Google
                </a>
                
                <div class="features">
                    <h3>What you'll get:</h3>
                    <div class="feature">📅 Smart calendar booking</div>
                    <div class="feature">🤖 AI-powered scheduling assistant</div>
                    <div class="feature">⏰ Automatic availability checking</div>
                    <div class="feature">🔔 Meeting reminders</div>
                    <div class="feature">📱 Cross-platform access</div>
                </div>
                
                <div class="security">
                    <strong>🔒 Your Privacy & Security</strong><br>
                    We only access your calendar to help you schedule appointments. 
                    Your data is encrypted and you can revoke access anytime.
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error creating login page: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create login page: {str(e)}"
        )

@auth_router.get("/callback")
async def auth_callback(code: str = None, state: str = None, error: str = None):
    """Handle OAuth2 callback from Google"""
    try:
        if error:
            logger.warning(f"OAuth2 error: {error}")
            return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head><title>Authentication Error</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1>❌ Authentication Failed</h1>
                <p>Error: {error}</p>
                <p><a href="/auth/login">Try Again</a></p>
            </body>
            </html>
            """)
        
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code not provided"
            )
        
        # Handle the callback and create user session
        user_id = google_auth_manager.handle_auth_callback(code, state)
        user_info = google_auth_manager.get_user_info(user_id)
        
        # Success page
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Successful</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .container {{
                    background: white;
                    border-radius: 15px;
                    padding: 40px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 500px;
                    width: 100%;
                }}
                .success {{
                    color: #28a745;
                    font-size: 48px;
                    margin-bottom: 20px;
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 20px;
                }}
                .user-info {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .next-steps {{
                    text-align: left;
                    margin: 20px 0;
                }}
                .step {{
                    margin: 10px 0;
                    padding: 10px;
                    background: #e3f2fd;
                    border-radius: 5px;
                }}
                .btn {{
                    background: #4285f4;
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 8px;
                    text-decoration: none;
                    display: inline-block;
                    margin: 10px;
                    font-weight: 500;
                }}
                .btn:hover {{
                    background: #3367d6;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">✅</div>
                <h1>Authentication Successful!</h1>
                
                <div class="user-info">
                    <strong>Welcome, {user_info.get('name', 'User')}!</strong><br>
                    <small>{user_info.get('email', '')}</small><br>
                    <small>User ID: {user_id}</small>
                </div>
                
                <div class="next-steps">
                    <h3>🚀 Next Steps:</h3>
                    <div class="step">1. Open the Streamlit app: <a href="http://localhost:8501" target="_blank">http://localhost:8501</a></div>
                    <div class="step">2. Use your User ID: <code>{user_id}</code></div>
                    <div class="step">3. Start chatting with the AI assistant!</div>
                </div>
                
                <a href="http://localhost:8501" class="btn" target="_blank">Open TailorTalk App</a>
                <a href="/docs" class="btn" target="_blank">View API Docs</a>
                
                <p style="margin-top: 30px; color: #666; font-size: 14px;">
                    🔒 Your Google Calendar is now connected securely. 
                    You can revoke access anytime from your Google Account settings.
                </p>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error handling auth callback: {e}")
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head><title>Authentication Error</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1>❌ Authentication Error</h1>
            <p>Error: {str(e)}</p>
            <p><a href="/auth/login">Try Again</a></p>
        </body>
        </html>
        """)

@auth_router.get("/status/{user_id}", response_model=AuthStatusResponse)
async def check_auth_status(user_id: str):
    """Check authentication status for a user"""
    try:
        is_authenticated = google_auth_manager.is_user_authenticated(user_id)
        
        if is_authenticated:
            user_info = google_auth_manager.get_user_info(user_id)
            return AuthStatusResponse(
                authenticated=True,
                user_id=user_id,
                user_info=user_info,
                message="User is authenticated"
            )
        else:
            return AuthStatusResponse(
                authenticated=False,
                message="User is not authenticated"
            )
            
    except Exception as e:
        logger.error(f"Error checking auth status for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check authentication status: {str(e)}"
        )

@auth_router.delete("/revoke/{user_id}")
async def revoke_user_access(user_id: str):
    """Revoke user access and delete stored credentials"""
    try:
        success = google_auth_manager.revoke_user_access(user_id)
        
        if success:
            logger.info(f"Access revoked for user: {user_id}")
            
            return {
                "success": True,
                "user_id": user_id,
                "message": "Access revoked successfully"
            }
        else:
            return {
                "success": False,
                "user_id": user_id,
                "message": "Failed to revoke access"
            }
            
    except Exception as e:
        logger.error(f"Access revocation failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke access: {str(e)}"
        )

@auth_router.post("/logout/{user_id}")
async def logout_user(user_id: str):
    """Logout user and revoke access"""
    try:
        success = google_auth_manager.revoke_user_access(user_id)
        
        if success:
            return {
                "success": True,
                "message": "User logged out successfully",
                "user_id": user_id
            }
        else:
            return {
                "success": False,
                "message": "Failed to logout user",
                "user_id": user_id
            }
            
    except Exception as e:
        logger.error(f"Error logging out user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to logout user: {str(e)}"
        )

@auth_router.get("/users")
async def list_authenticated_users():
    """List all authenticated users (admin endpoint)"""
    try:
        users = google_auth_manager.list_authenticated_users()
        
        return {
            "total_users": len(users),
            "users": users,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error listing authenticated users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )

@auth_router.get("/health")
async def auth_health_check():
    """Authentication system health check"""
    try:
        auth_status = google_auth_manager.get_auth_status()
        
        return {
            "status": "healthy",
            "auth_system": auth_status,
            "message": "Authentication system is operational"
        }
        
    except Exception as e:
        logger.error(f"Auth health check error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Authentication system error"
        }

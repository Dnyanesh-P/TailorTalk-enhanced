"""
Enhanced Streamlit Application for TailorTalk with Google Authentication
Provides a user-friendly interface for AI-powered calendar booking
"""
import streamlit as st
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import pytz
from urllib.parse import parse_qs, urlparse
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8001"
TIMEZONE = pytz.timezone('Asia/Kolkata')

# Page configuration
st.set_page_config(
    page_title="TailorTalk Enhanced - AI Calendar Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .auth-status {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .auth-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    
    .auth-pending {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
    }
    
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    
    .stats-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = f"user_{int(time.time())}"
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'user_info' not in st.session_state:
        st.session_state.user_info = {}
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'auth_checked' not in st.session_state:
        st.session_state.auth_checked = False

def check_url_params():
    """Check URL parameters for authentication results"""
    try:
        # Get query parameters from URL
        query_params = st.experimental_get_query_params()
        
        if 'auth_success' in query_params and query_params['auth_success'][0] == 'true':
            st.session_state.authenticated = True
            st.session_state.user_id = query_params.get('user_id', [st.session_state.user_id])[0]
            
            # Store user info
            st.session_state.user_info = {
                'name': query_params.get('user_name', [''])[0],
                'email': query_params.get('user_email', [''])[0]
            }
            
            st.success("🎉 Authentication successful! You can now book appointments.")
            
            # Clear URL parameters
            st.experimental_set_query_params()
        
        elif 'error' in query_params:
            error_msg = query_params['error'][0]
            st.error(f"❌ Authentication failed: {error_msg}")
            
            # Clear URL parameters
            st.experimental_set_query_params()
            
    except Exception as e:
        logger.error(f"Error checking URL parameters: {e}")

def check_authentication_status():
    """Check current authentication status with the API"""
    try:
        response = requests.get(f"{API_BASE_URL}/auth/status/{st.session_state.user_id}")
        
        if response.status_code == 200:
            auth_data = response.json()
            st.session_state.authenticated = auth_data['authenticated']
            
            if auth_data['authenticated'] and auth_data['user_info']:
                st.session_state.user_info = auth_data['user_info']
            
            st.session_state.auth_checked = True
            return auth_data
        else:
            st.session_state.authenticated = False
            return None
            
    except Exception as e:
        logger.error(f"Authentication status check failed: {e}")
        st.session_state.authenticated = False
        return None

def initiate_google_auth():
    """Initiate Google authentication flow"""
    try:
        with st.spinner("Initiating Google authentication..."):
            response = requests.post(
                f"{API_BASE_URL}/auth/initiate",
                json={"redirect_uri": f"{API_BASE_URL}/auth/callback"}
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                
                if auth_data['success']:
                    st.markdown(f"""
                    ### 🔐 Google Authentication Required
                    
                    Please click the link below to authenticate with your Google account:
                    
                    **[🔗 Authenticate with Google]({auth_data['auth_url']})**
                    
                    After authentication, you'll be redirected back to this application.
                    """)
                    
                    return True
                else:
                    st.error("Failed to initiate authentication")
                    return False
            else:
                st.error(f"Authentication initiation failed: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"Google auth initiation failed: {e}")
        st.error(f"Authentication error: {str(e)}")
        return False

def revoke_access():
    """Revoke user access"""
    try:
        with st.spinner("Revoking access..."):
            response = requests.delete(f"{API_BASE_URL}/auth/revoke/{st.session_state.user_id}")
            
            if response.status_code == 200:
                result = response.json()
                
                if result['success']:
                    st.session_state.authenticated = False
                    st.session_state.user_info = {}
                    st.session_state.chat_history = []
                    st.success("✅ Access revoked successfully")
                else:
                    st.error("Failed to revoke access")
            else:
                st.error("Failed to revoke access")
                
    except Exception as e:
        logger.error(f"Access revocation failed: {e}")
        st.error(f"Revocation error: {str(e)}")

def send_chat_message(message: str) -> Optional[str]:
    """Send chat message to the API"""
    try:
        with st.spinner("AI is thinking..."):
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json={
                    "message": message,
                    "user_id": st.session_state.user_id,
                    "session_id": f"streamlit_{int(time.time())}"
                }
            )
            
            if response.status_code == 200:
                chat_response = response.json()
                return chat_response['response']
            else:
                return f"❌ Error: {response.status_code} - {response.text}"
                
    except Exception as e:
        logger.error(f"Chat message failed: {e}")
        return f"❌ Connection error: {str(e)}"

def get_availability(date_str: str) -> Optional[Dict[str, Any]]:
    """Get availability for a specific date"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/availability",
            json={
                "user_id": st.session_state.user_id,
                "date": date_str
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
            
    except Exception as e:
        logger.error(f"Availability check failed: {e}")
        return None

def get_upcoming_events() -> Optional[List[Dict[str, Any]]]:
    """Get upcoming events"""
    try:
        response = requests.get(f"{API_BASE_URL}/users/{st.session_state.user_id}/upcoming-events")
        
        if response.status_code == 200:
            result = response.json()
            return result.get('upcoming_events', [])
        else:
            return None
            
    except Exception as e:
        logger.error(f"Upcoming events fetch failed: {e}")
        return None

def render_header():
    """Render the main header"""
    st.markdown("""
    <div class="main-header">
        <h1>🤖 TailorTalk Enhanced</h1>
        <p>AI-Powered Google Calendar Booking Assistant</p>
    </div>
    """, unsafe_allow_html=True)

def render_authentication_section():
    """Render authentication section"""
    st.sidebar.header("🔐 Authentication")
    
    if not st.session_state.auth_checked:
        auth_status = check_authentication_status()
    
    if st.session_state.authenticated:
        user_name = st.session_state.user_info.get('name', 'User')
        user_email = st.session_state.user_info.get('email', '')
        
        st.sidebar.markdown(f"""
        <div class="auth-status auth-success">
            <strong>✅ Authenticated</strong><br>
            👤 {user_name}<br>
            📧 {user_email}
        </div>
        """, unsafe_allow_html=True)
        
        if st.sidebar.button("🚪 Sign Out", type="secondary"):
            revoke_access()
            st.experimental_rerun()
    else:
        st.sidebar.markdown("""
        <div class="auth-status auth-pending">
            <strong>⚠️ Not Authenticated</strong><br>
            Please authenticate with Google to access calendar features.
        </div>
        """, unsafe_allow_html=True)
        
        if st.sidebar.button("🔑 Authenticate with Google", type="primary"):
            initiate_google_auth()

def render_quick_actions():
    """Render quick action buttons"""
    if st.session_state.authenticated:
        st.sidebar.header("⚡ Quick Actions")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("📅 Check Today", use_container_width=True):
                today = datetime.now(TIMEZONE).strftime('%Y-%m-%d')
                availability = get_availability(today)
                
                if availability:
                    slots = availability['available_slots']
                    if slots:
                        st.success(f"📅 Available today: {', '.join(slots[:3])}{'...' if len(slots) > 3 else ''}")
                    else:
                        st.info("📅 No available slots today")
                else:
                    st.error("❌ Could not check availability")
        
        with col2:
            if st.button("📋 Upcoming", use_container_width=True):
                events = get_upcoming_events()
                
                if events:
                    st.success(f"📋 You have {len(events)} upcoming events")
                else:
                    st.info("📋 No upcoming events")

def render_system_stats():
    """Render system statistics"""
    st.sidebar.header("📊 System Stats")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        
        if response.status_code == 200:
            health_data = response.json()
            stats = health_data.get('statistics', {})
            
            st.sidebar.markdown(f"""
            <div class="stats-card">
                <strong>System Health</strong><br>
                Status: {health_data.get('status', 'Unknown').title()}<br>
                Users: {stats.get('authenticated_users', 0)}<br>
                Requests: {stats.get('total_requests', 0)}<br>
                Bookings: {stats.get('successful_bookings', 0)}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.sidebar.error("❌ Could not fetch system stats")
            
    except Exception as e:
        st.sidebar.error(f"❌ Stats error: {str(e)}")

def render_chat_interface():
    """Render the main chat interface"""
    st.header("💬 Chat with AI Assistant")
    
    # Display chat history
    for i, (role, message, timestamp) in enumerate(st.session_state.chat_history):
        if role == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 You</strong> <small>({timestamp})</small><br>
                {message}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 TailorTalk</strong> <small>({timestamp})</small><br>
                {message}
            </div>
            """, unsafe_allow_html=True)
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message to history
        timestamp = datetime.now(TIMEZONE).strftime('%H:%M')
        st.session_state.chat_history.append(("user", user_input, timestamp))
        
        # Get AI response
        ai_response = send_chat_message(user_input)
        
        if ai_response:
            # Add AI response to history
            st.session_state.chat_history.append(("assistant", ai_response, timestamp))
        
        # Rerun to update the display
        st.experimental_rerun()

def render_calendar_tools():
    """Render calendar management tools"""
    if st.session_state.authenticated:
        st.header("📅 Calendar Tools")
        
        tab1, tab2, tab3 = st.tabs(["📅 Check Availability", "📋 Upcoming Events", "⚙️ Quick Book"])
        
        with tab1:
            st.subheader("Check Availability")
            
            selected_date = st.date_input(
                "Select Date",
                value=datetime.now(TIMEZONE).date(),
                min_value=datetime.now(TIMEZONE).date()
            )
            
            if st.button("Check Availability", type="primary"):
                date_str = selected_date.strftime('%Y-%m-%d')
                availability = get_availability(date_str)
                
                if availability:
                    slots = availability['available_slots']
                    
                    if slots:
                        st.success(f"✅ Found {len(slots)} available slots:")
                        
                        cols = st.columns(min(len(slots), 4))
                        for i, slot in enumerate(slots):
                            with cols[i % 4]:
                                st.info(f"🕐 {slot}")
                    else:
                        st.warning("⚠️ No available slots for this date")
                else:
                    st.error("❌ Could not check availability")
        
        with tab2:
            st.subheader("Upcoming Events")
            
            if st.button("Refresh Events", type="secondary"):
                events = get_upcoming_events()
                
                if events:
                    st.success(f"📋 Found {len(events)} upcoming events:")
                    
                    for event in events[:10]:  # Show first 10 events
                        start_time = event['start']
                        
                        # Parse and format the datetime
                        try:
                            if 'T' in start_time:
                                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                formatted_time = dt.strftime('%A, %B %d at %I:%M %p')
                            else:
                                formatted_time = start_time
                        except:
                            formatted_time = start_time
                        
                        st.markdown(f"""
                        **{event['summary']}**  
                        📅 {formatted_time}  
                        📍 {event.get('location', 'No location')}
                        """)
                        st.divider()
                else:
                    st.info("📋 No upcoming events found")
        
        with tab3:
            st.subheader("Quick Book Appointment")
            
            with st.form("quick_book_form"):
                book_date = st.date_input(
                    "Date",
                    value=datetime.now(TIMEZONE).date() + timedelta(days=1),
                    min_value=datetime.now(TIMEZONE).date()
                )
                
                book_time = st.time_input("Time", value=datetime.now(TIMEZONE).time())
                
                book_title = st.text_input("Title", value="TailorTalk Appointment")
                
                book_duration = st.selectbox("Duration", [30, 60, 90, 120], index=1)
                
                submitted = st.form_submit_button("📅 Book Appointment", type="primary")
                
                if submitted:
                    # Format the booking request as a natural language message
                    date_str = book_date.strftime('%Y-%m-%d')
                    time_str = book_time.strftime('%H:%M')
                    
                    booking_message = f"Book '{book_title}' on {date_str} at {time_str} for {book_duration} minutes"
                    
                    # Send to AI assistant
                    ai_response = send_chat_message(booking_message)
                    
                    if "successfully booked" in ai_response.lower():
                        st.success("✅ " + ai_response)
                    else:
                        st.error("❌ " + ai_response)

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Check URL parameters for auth results
    check_url_params()
    
    # Render header
    render_header()
    
    # Render sidebar components
    render_authentication_section()
    render_quick_actions()
    render_system_stats()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_chat_interface()
    
    with col2:
        render_calendar_tools()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        🤖 <strong>TailorTalk Enhanced</strong> - AI-Powered Calendar Assistant<br>
        Built with FastAPI, LangGraph, and Google Calendar API
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

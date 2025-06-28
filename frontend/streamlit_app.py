import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import time
import pytz

def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "api_url" not in st.session_state:
        st.session_state.api_url = "http://127.0.0.1:8001"

def setup_page_config():
    """Setup page configuration"""
    st.set_page_config(
        page_title="TailorTalk - AI Booking Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def apply_custom_css():
    """Apply custom CSS styles"""
    st.markdown("""
    <style>
        .chat-message {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: flex-start;
        }
        .user-message {
            background-color: #e3f2fd;
            margin-left: 2rem;
        }
        .assistant-message {
            background-color: #f5f5f5;
            margin-right: 2rem;
        }
        .message-content {
            margin-left: 0.5rem;
        }
        .status-success {
            color: #4caf50;
            font-weight: bold;
        }
        .status-error {
            color: #f44336;
            font-weight: bold;
        }
        .status-warning {
            color: #ff9800;
            font-weight: bold;
        }
        .feature-box {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #2196f3;
            margin: 0.5rem 0;
        }
    </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render the sidebar with settings and controls"""
    with st.sidebar:
        st.header("⚙️ Settings")
        api_url = st.text_input("API URL", value=st.session_state.api_url)
        st.session_state.api_url = api_url
        
        # Connection test with detailed health check
        if st.button("🔍 Test Connection & Health"):
            try:
                with st.spinner("Testing connection and checking system health..."):
                    response = requests.get(f"{api_url}/health", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        st.success("✅ API Connected!")
                        
                        # Display health status
                        status = data.get('status', 'unknown')
                        if status == 'healthy':
                            st.markdown('<p class="status-success">🟢 System Status: Healthy</p>', unsafe_allow_html=True)
                        elif status == 'partial':
                            st.markdown('<p class="status-warning">🟡 System Status: Partial (some components need attention)</p>', unsafe_allow_html=True)
                        else:
                            st.markdown('<p class="status-error">🔴 System Status: Unhealthy</p>', unsafe_allow_html=True)
                        
                        # Component status
                        components = data.get('components', {})
                        st.markdown("**Component Status:**")
                        for component, status in components.items():
                            if 'error' in status:
                                st.markdown(f"❌ {component}: {status}")
                            elif 'configured' in status or 'connected' in status or 'initialized' in status:
                                st.markdown(f"✅ {component}: {status}")
                            else:
                                st.markdown(f"⚠️ {component}: {status}")
                        
                        # Configuration info
                        config = data.get('config', {})
                        if config:
                            st.markdown("**Configuration:**")
                            st.json(config)
                    else:
                        st.error(f"❌ Connection failed: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Cannot connect to API: {str(e)}")
                st.info("💡 Make sure your FastAPI server is running:\n\`\`\`\npython main.py\n\`\`\`")
        
        st.markdown("---")
        
        # Quick actions
        st.markdown("### 🚀 Quick Actions")
        
        # Get timezone
        TIMEZONE = pytz.timezone('Asia/Kolkata')
        
        # Check today's availability
        if st.button("📅 Check Today's Availability"):
            today = datetime.now(TIMEZONE).strftime('%Y-%m-%d')
            try:
                with st.spinner("Checking availability..."):
                    response = requests.get(f"{api_url}/availability/{today}", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"Available slots for {today}:")
                        slots = data["available_slots"]
                        if slots:
                            for slot in slots:
                                st.write(f"• {slot} IST")
                        else:
                            st.write("No available slots found")
                    else:
                        st.error("Error checking availability")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        # Check tomorrow's availability
        if st.button("📅 Check Tomorrow's Availability"):
            tomorrow = (datetime.now(TIMEZONE) + timedelta(days=1)).strftime('%Y-%m-%d')
            try:
                with st.spinner("Checking availability..."):
                    response = requests.get(f"{api_url}/availability/{tomorrow}", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"Available slots for {tomorrow}:")
                        slots = data["available_slots"]
                        if slots:
                            for slot in slots:
                                st.write(f"• {slot} IST")
                        else:
                            st.write("No available slots found")
                    else:
                        st.error("Error checking availability")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        # API Status
        if st.button("📊 API Status"):
            try:
                response = requests.get(f"{api_url}/", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ API is running")
                    st.json(data)
                    st.write("🌐 FastAPI docs:", f"{api_url}/docs")
                else:
                    st.error("❌ API not responding")
            except:
                st.error("❌ Cannot reach API")
        
        st.markdown("---")
        
        # Features info
        st.markdown("### ✨ Features")
        st.markdown("""
        <div class="feature-box">
            <strong>🤖 AI-Powered Conversations</strong><br>
            Natural language understanding for booking requests
        </div>
        <div class="feature-box">
            <strong>📅 Google Calendar Integration</strong><br>
            Real-time availability checking and booking
        </div>
        <div class="feature-box">
            <strong>🕐 Smart Time Recognition</strong><br>
            Understands "tomorrow afternoon", "next week", etc.
        </div>
        <div class="feature-box">
            <strong>⚡ Instant Booking</strong><br>
            Books appointments directly to your calendar
        </div>
        """, unsafe_allow_html=True)

def render_chat_interface():
    """Render the main chat interface"""
    # Title and description
    st.title("🤖 TailorTalk - AI Booking Assistant")
    st.markdown("**Your intelligent appointment booking companion with real-time Google Calendar integration!**")
    
    # Main chat interface
    st.markdown("### 💬 Chat with TailorTalk")
    
    # Display current time
    TIMEZONE = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(TIMEZONE).strftime('%I:%M %p IST on %A, %B %d, %Y')
    st.info(f"🕐 Current time: {current_time}")
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <div>👤</div>
                    <div class="message-content"><strong>You:</strong><br>{message["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <div>🤖</div>
                    <div class="message-content"><strong>TailorTalk:</strong><br>{message["content"]}</div>
                </div>
                """, unsafe_allow_html=True)

def handle_chat_input():
    """Handle chat input and API communication"""
    # Chat input
    user_input = st.chat_input("Type your message here... (e.g., 'I want to schedule a call for tomorrow afternoon')")
    
    if user_input:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Send to API
        try:
            with st.spinner("🤖 TailorTalk is thinking..."):
                response = requests.post(
                    f"{st.session_state.api_url}/chat",
                    json={"message": user_input},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    assistant_response = data["response"]
                    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                    st.success("✅ Response received!")
                else:
                    st.error(f"❌ API Error: {response.status_code}")
                    error_response = f"I apologize, but I encountered an error (Status: {response.status_code}). Please try again."
                    st.session_state.messages.append({"role": "assistant", "content": error_response})
                    
        except requests.exceptions.Timeout:
            st.error("⏰ Request timed out. The AI might be processing a complex request.")
            timeout_response = "I'm taking longer than usual to process your request. Please try again."
            st.session_state.messages.append({"role": "assistant", "content": timeout_response})
        except requests.exceptions.ConnectionError:
            st.error("🔌 Connection error. Make sure your FastAPI server is running.")
            st.info("💡 Start the server with: `python main.py`")
            connection_error_response = "I'm having trouble connecting to my backend services. Please make sure the API server is running."
            st.session_state.messages.append({"role": "assistant", "content": connection_error_response})
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
            error_response = f"I encountered an unexpected error: {str(e)}. Please try again."
            st.session_state.messages.append({"role": "assistant", "content": error_response})
        
        # Rerun to update the chat display
        st.rerun()

def render_example_prompts():
    """Render example prompt buttons"""
    # Example prompts
    st.markdown("---")
    st.markdown("### 💡 Try these examples:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📅 Book tomorrow afternoon", key="example1"):
            # Add message and trigger API call
            user_input = "I want to schedule a call for tomorrow afternoon"
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Make API call
            try:
                with st.spinner("🤖 TailorTalk is thinking..."):
                    response = requests.post(
                        f"{st.session_state.api_url}/chat",
                        json={"message": user_input},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        assistant_response = data["response"]
                        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                        st.success("✅ Response received!")
                    else:
                        error_response = f"API Error: {response.status_code}"
                        st.session_state.messages.append({"role": "assistant", "content": error_response})
            except Exception as e:
                error_response = f"Error: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": error_response})
            
            st.rerun()
    
    with col2:
        if st.button("🕐 Check Friday availability", key="example2"):
            user_input = "Do you have any free time this Friday?"
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            try:
                with st.spinner("🤖 TailorTalk is thinking..."):
                    response = requests.post(
                        f"{st.session_state.api_url}/chat",
                        json={"message": user_input},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        assistant_response = data["response"]
                        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                        st.success("✅ Response received!")
                    else:
                        error_response = f"API Error: {response.status_code}"
                        st.session_state.messages.append({"role": "assistant", "content": error_response})
            except Exception as e:
                error_response = f"Error: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": error_response})
            
            st.rerun()
    
    with col3:
        if st.button("📞 Book next week", key="example3"):
            user_input = "Book a meeting between 3-5 PM next week"
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            try:
                with st.spinner("🤖 TailorTalk is thinking..."):
                    response = requests.post(
                        f"{st.session_state.api_url}/chat",
                        json={"message": user_input},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        assistant_response = data["response"]
                        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                        st.success("✅ Response received!")
                    else:
                        error_response = f"API Error: {response.status_code}"
                        st.session_state.messages.append({"role": "assistant", "content": error_response})
            except Exception as e:
                error_response = f"Error: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": error_response})
            
            st.rerun()
    
    # More examples
    col4, col5, col6 = st.columns(3)
    
    with col4:
        if st.button("🌅 Morning meeting", key="example4"):
            st.session_state.messages.append({"role": "user", "content": "Schedule a meeting for tomorrow morning at 10 AM"})
            st.rerun()
    
    with col5:
        if st.button("📋 Check today's schedule", key="example5"):
            st.session_state.messages.append({"role": "user", "content": "What's my availability for today?"})
            st.rerun()
    
    with col6:
        if st.button("👋 Say hello", key="example6"):
            st.session_state.messages.append({"role": "user", "content": "Hello! How can you help me?"})
            st.rerun()

def render_controls():
    """Render additional controls"""
    # Additional controls
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh Page", key="refresh"):
            st.rerun()
    
    with col3:
        if st.button("📖 Show Instructions", key="instructions"):
            st.info("""
            **How to use TailorTalk:**
            
            1. **Natural Language**: Just type what you want in plain English
            2. **Be Specific**: Include date and time preferences when possible
            3. **Confirm Bookings**: The AI will ask for confirmation before booking
            4. **Check Status**: Use the sidebar to check system health and availability
            
            **Example phrases:**
            - "Book a call for tomorrow at 3 PM"
            - "Do I have any free time this Friday afternoon?"
            - "Schedule a meeting for next Monday morning"
            - "I need to book an appointment for next week"
            """)

def render_footer():
    """Render the footer"""
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9em;">
        <p>🤖 <strong>TailorTalk AI Booking Assistant</strong> - Powered by OpenAI GPT, LangGraph, and Google Calendar API</p>
        <p>Built with FastAPI, Streamlit, and ❤️</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    """Main application function"""
    # Setup page configuration first
    setup_page_config()
    
    # Initialize session state
    initialize_session_state()
    
    # Apply custom CSS
    apply_custom_css()
    
    # Render sidebar
    render_sidebar()
    
    # Render main chat interface
    render_chat_interface()
    
    # Handle chat input
    handle_chat_input()
    
    # Render example prompts
    render_example_prompts()
    
    # Render controls
    render_controls()
    
    # Render footer
    render_footer()

if __name__ == "__main__":
    main()

import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import time
import pytz
import asyncio
import threading
from typing import Dict, List, Optional

def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "api_url" not in st.session_state:
        st.session_state.api_url = "http://127.0.0.1:8001"
    if "availability_data" not in st.session_state:
        st.session_state.availability_data = {}
    if "last_availability_check" not in st.session_state:
        st.session_state.last_availability_check = None
    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = True
    if "system_status" not in st.session_state:
        st.session_state.system_status = None
    if "enhanced_features" not in st.session_state:
        st.session_state.enhanced_features = {}

def setup_page_config():
    """Setup page configuration"""
    st.set_page_config(
        page_title="TailorTalk Enhanced - AI Booking Assistant",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def apply_custom_css():
    """Apply enhanced custom CSS styles"""
    st.markdown("""
    <style>
        .chat-message {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: flex-start;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .user-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin-left: 2rem;
        }
        .assistant-message {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            margin-right: 2rem;
        }
        .system-message {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            margin: 0 1rem;
        }
        .message-content {
            margin-left: 0.5rem;
            flex: 1;
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
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .availability-slot {
            padding: 0.5rem;
            margin: 0.25rem 0;
            border-radius: 0.25rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .slot-available {
            background-color: #e8f5e8;
            border-left: 4px solid #4caf50;
        }
        .slot-booked {
            background-color: #ffeaea;
            border-left: 4px solid #f44336;
        }
        .realtime-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            background-color: #4caf50;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .enhanced-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .enhanced-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .agent-badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 1rem;
            font-size: 0.75rem;
            font-weight: bold;
            margin-left: 0.5rem;
        }
        .agent-enhanced {
            background-color: #4caf50;
            color: white;
        }
        .agent-openai {
            background-color: #2196f3;
            color: white;
        }
        .agent-fallback {
            background-color: #ff9800;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

def check_api_health():
    """Check API health and return detailed status"""
    try:
        response = requests.get(f"{st.session_state.api_url}/health", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_availability(date_str: str, use_realtime: bool = True):
    """Get availability for a specific date with real-time option"""
    try:
        endpoint = f"/realtime/availability/{date_str}" if use_realtime else f"/availability/{date_str}"
        response = requests.get(f"{st.session_state.api_url}{endpoint}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            st.session_state.availability_data[date_str] = data
            st.session_state.last_availability_check = datetime.now()
            return data
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching availability: {e}")
        return None

def render_enhanced_sidebar():
    """Render the enhanced sidebar with real-time features"""
    with st.sidebar:
        st.header("⚙️ Enhanced Settings")
        
        # API Configuration
        api_url = st.text_input("API URL", value=st.session_state.api_url)
        st.session_state.api_url = api_url
        
        # Auto-refresh toggle
        st.session_state.auto_refresh = st.checkbox("🔄 Auto-refresh availability", value=st.session_state.auto_refresh)
        
        # Enhanced connection test
        if st.button("🔍 Test Enhanced Connection"):
            with st.spinner("Testing enhanced connection..."):
                health_data = check_api_health()
                st.session_state.system_status = health_data
                
                if health_data.get('status') == 'healthy':
                    st.success("✅ Enhanced API Connected!")
                    
                    # Display enhanced features status
                    enhanced_features = health_data.get('enhanced_features', {})
                    st.session_state.enhanced_features = enhanced_features
                    
                    st.markdown("**🎯 Enhanced Features:**")
                    for feature, enabled in enhanced_features.items():
                        icon = "✅" if enabled else "❌"
                        feature_name = feature.replace('_', ' ').title()
                        st.markdown(f"{icon} {feature_name}")
                    
                    # Display agent type
                    config = health_data.get('config', {})
                    agent_type = config.get('active_agent_type', 'unknown')
                    if agent_type == 'enhanced':
                        st.markdown('<span class="agent-badge agent-enhanced">🎯 Enhanced Agent</span>', unsafe_allow_html=True)
                    elif agent_type == 'openai':
                        st.markdown('<span class="agent-badge agent-openai">🤖 OpenAI Agent</span>', unsafe_allow_html=True)
                    elif agent_type == 'fallback':
                        st.markdown('<span class="agent-badge agent-fallback">🔄 Fallback Agent</span>', unsafe_allow_html=True)
                    
                    # Component status
                    components = health_data.get('components', {})
                    with st.expander("🔧 Component Details"):
                        for component, status in components.items():
                            if 'error' in status.lower():
                                st.markdown(f"❌ **{component}**: {status}")
                            elif any(word in status.lower() for word in ['configured', 'connected', 'ready', 'available']):
                                st.markdown(f"✅ **{component}**: {status}")
                            else:
                                st.markdown(f"⚠️ **{component}**: {status}")
                
                elif health_data.get('status') == 'degraded':
                    st.warning("⚠️ API Connected (Degraded)")
                    st.markdown(f"**Issue**: {health_data.get('message', 'Some components need attention')}")
                else:
                    st.error("❌ Connection Failed")
                    st.markdown(f"**Error**: {health_data.get('message', 'Unknown error')}")
        
        st.markdown("---")
        
        # Enhanced Quick Actions
        st.markdown("### 🚀 Enhanced Quick Actions")
        
        TIMEZONE = pytz.timezone('Asia/Kolkata')
        
        # Real-time availability checks
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📅 Today", key="check_today", help="Check today's availability with real-time updates"):
                today = datetime.now(TIMEZONE).strftime('%Y-%m-%d')
                with st.spinner("🔄 Getting real-time availability..."):
                    data = get_availability(today, use_realtime=True)
                    if data:
                        st.success(f"✅ Today ({data.get('formatted_date', today)})")
                        display_availability_sidebar(data)
                    else:
                        st.error("❌ Failed to get availability")
        
        with col2:
            if st.button("📅 Tomorrow", key="check_tomorrow", help="Check tomorrow's availability"):
                tomorrow = (datetime.now(TIMEZONE) + timedelta(days=1)).strftime('%Y-%m-%d')
                with st.spinner("🔄 Getting real-time availability..."):
                    data = get_availability(tomorrow, use_realtime=True)
                    if data:
                        st.success(f"✅ Tomorrow ({data.get('formatted_date', tomorrow)})")
                        display_availability_sidebar(data)
                    else:
                        st.error("❌ Failed to get availability")
        
        # Date picker for custom dates
        st.markdown("**📆 Custom Date:**")
        selected_date = st.date_input("Select date", min_value=datetime.now().date())
        if st.button("🔍 Check Selected Date", key="check_custom"):
            date_str = selected_date.strftime('%Y-%m-%d')
            with st.spinner("🔄 Getting availability..."):
                data = get_availability(date_str, use_realtime=True)
                if data:
                    st.success(f"✅ {data.get('formatted_date', date_str)}")
                    display_availability_sidebar(data)
                else:
                    st.error("❌ Failed to get availability")
        
        # Enhanced parsing test
        st.markdown("---")
        st.markdown("### 🧪 Enhanced Parsing Test")
        test_text = st.text_input("Test parsing:", placeholder="e.g., '5th July at 3:30pm'")
        if st.button("🔍 Parse", key="test_parse") and test_text:
            try:
                response = requests.get(f"{api_url}/parse-datetime", params={"text": test_text}, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ Parsing Result:")
                    st.json({
                        "Date": data.get('date'),
                        "Time": data.get('time'),
                        "Confidence": f"{data.get('confidence', 0):.2f}",
                        "Parser": data.get('parser_type', 'unknown')
                    })
                else:
                    st.error("❌ Parsing failed")
            except Exception as e:
                st.error(f"❌ Error: {e}")
        
        st.markdown("---")
        
        # Enhanced Features Info
        st.markdown("### ✨ Enhanced Features")
        
        features_info = [
            ("🎯 Precise Date Parsing", "Handles '5th July', '4th August 3:30pm', etc."),
            ("🔄 Real-time Updates", "Availability updates every 30 seconds"),
            ("🤖 Smart Conversations", "Context-aware multi-turn dialogues"),
            ("📅 Enhanced Calendar", "Advanced Google Calendar integration"),
            ("⚡ Instant Booking", "Direct calendar event creation"),
            ("🛡️ Error Recovery", "Robust error handling and fallbacks")
        ]
        
        for title, description in features_info:
            with st.expander(title):
                st.markdown(description)

def display_availability_sidebar(data: Dict):
    """Display availability data in sidebar"""
    if not data:
        return
    
    slots = data.get('available_slots', [])
    total_slots = data.get('total_slots', 0)
    last_updated = data.get('last_updated', '')
    realtime_enabled = data.get('realtime_enabled', False)
    
    st.markdown(f"**📊 Available Slots: {total_slots}**")
    
    if realtime_enabled:
        st.markdown('<span class="realtime-indicator"></span> Real-time enabled', unsafe_allow_html=True)
    
    if slots:
        for slot in slots[:6]:  # Show first 6 slots
            time_obj = datetime.strptime(slot, '%H:%M').time()
            formatted_time = time_obj.strftime('%I:%M %p')
            st.markdown(f"🟢 {slot} ({formatted_time})")
        
        if len(slots) > 6:
            st.markdown(f"... and {len(slots) - 6} more slots")
    else:
        st.markdown("❌ No available slots")
    
    if last_updated:
        try:
            updated_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            st.markdown(f"🕐 Updated: {updated_time.strftime('%H:%M:%S')}")
        except:
            st.markdown(f"🕐 Updated: {last_updated}")

def render_enhanced_chat_interface():
    """Render the enhanced main chat interface"""
    # Enhanced title and description
    st.title("🚀 TailorTalk Enhanced - AI Booking Assistant")
    st.markdown("**Your intelligent appointment booking companion with real-time Google Calendar integration and enhanced AI capabilities!**")
    
    # System status indicator
    if st.session_state.system_status:
        status = st.session_state.system_status.get('status', 'unknown')
        if status == 'healthy':
            st.success("🟢 System Status: Healthy - All enhanced features operational")
        elif status == 'degraded':
            st.warning("🟡 System Status: Degraded - Some features may be limited")
        else:
            st.error("🔴 System Status: Unhealthy - Please check configuration")
    
    # Enhanced features status
    if st.session_state.enhanced_features:
        enabled_features = [k.replace('_', ' ').title() for k, v in st.session_state.enhanced_features.items() if v]
        if enabled_features:
            st.info(f"✨ Enhanced Features Active: {', '.join(enabled_features)}")
    
    # Main chat interface
    st.markdown("### 💬 Chat with TailorTalk Enhanced")
    
    # Display current time with timezone
    TIMEZONE = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(TIMEZONE).strftime('%I:%M %p IST on %A, %B %d, %Y')
    st.info(f"🕐 Current time: {current_time}")
    
    # Auto-refresh indicator
    if st.session_state.auto_refresh:
        st.markdown('<span class="realtime-indicator"></span> Auto-refresh enabled', unsafe_allow_html=True)
    
    # Display enhanced chat messages
    chat_container = st.container()
    with chat_container:
        for i, message in enumerate(st.session_state.messages):
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <div>👤</div>
                    <div class="message-content">
                        <strong>You:</strong><br>
                        {message["content"]}
                        <div style="font-size: 0.8em; opacity: 0.8; margin-top: 0.5rem;">
                            {message.get('timestamp', '')}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif message["role"] == "assistant":
                agent_type = message.get('agent_type', 'unknown')
                agent_badge = ""
                if agent_type == 'enhanced':
                    agent_badge = '<span class="agent-badge agent-enhanced">Enhanced</span>'
                elif agent_type == 'openai':
                    agent_badge = '<span class="agent-badge agent-openai">OpenAI</span>'
                elif agent_type == 'fallback':
                    agent_badge = '<span class="agent-badge agent-fallback">Fallback</span>'
                
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <div>🤖</div>
                    <div class="message-content">
                        <strong>TailorTalk Enhanced:</strong> {agent_badge}<br>
                        {message["content"]}
                        <div style="font-size: 0.8em; opacity: 0.8; margin-top: 0.5rem;">
                            {message.get('timestamp', '')}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:  # system messages
                st.markdown(f"""
                <div class="chat-message system-message">
                    <div>🔧</div>
                    <div class="message-content">
                        <strong>System:</strong><br>
                        {message["content"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)

def handle_enhanced_chat_input():
    """Handle enhanced chat input with better error handling and features"""
    # Enhanced chat input
    user_input = st.chat_input("Type your message here... (e.g., 'Book appointment on 5th July at 3:30pm')")
    
    if user_input:
        # Add timestamp to user message
        timestamp = datetime.now().strftime('%H:%M:%S')
        st.session_state.messages.append({
            "role": "user", 
            "content": user_input,
            "timestamp": timestamp
        })
        
        # Send to enhanced API
        try:
            with st.spinner("🤖 TailorTalk Enhanced is processing..."):
                response = requests.post(
                    f"{st.session_state.api_url}/chat",
                    json={
                        "message": user_input,
                        "user_id": f"streamlit_user_{int(time.time())}"
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    assistant_response = data["response"]
                    agent_type = data.get("agent_type", "unknown")
                    
                    # Add assistant message with metadata
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": assistant_response,
                        "agent_type": agent_type,
                        "timestamp": timestamp
                    })
                    
                    # Show success with agent type
                    if agent_type == 'enhanced':
                        st.success("✅ Response from Enhanced Agent!")
                    elif agent_type == 'openai':
                        st.success("✅ Response from OpenAI Agent!")
                    else:
                        st.success("✅ Response received!")
                    
                    # Auto-refresh availability if booking-related
                    if any(word in assistant_response.lower() for word in ['book', 'schedule', 'available', 'appointment']):
                        if st.session_state.auto_refresh:
                            # Trigger availability refresh
                            today = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d')
                            get_availability(today, use_realtime=True)
                
                else:
                    st.error(f"❌ Enhanced API Error: {response.status_code}")
                    try:
                        error_data = response.json()
                        error_message = error_data.get('detail', f'HTTP {response.status_code}')
                    except:
                        error_message = f"HTTP {response.status_code}"
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": f"I apologize, but I encountered an error: {error_message}. Please try again.",
                        "timestamp": timestamp
                    })
                    
        except requests.exceptions.Timeout:
            st.error("⏰ Request timed out. The enhanced AI might be processing a complex request.")
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "I'm taking longer than usual to process your request. Please try again.",
                "timestamp": timestamp
            })
        except requests.exceptions.ConnectionError:
            st.error("🔌 Connection error. Make sure your Enhanced FastAPI server is running.")
            st.info("💡 Start the server with: `python main_with_ai.py`")
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "I'm having trouble connecting to my enhanced backend services. Please make sure the API server is running.",
                "timestamp": timestamp
            })
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
            st.session_state.messages.append({
                "role": "assistant", 
                "content": f"I encountered an unexpected error: {str(e)}. Please try again.",
                "timestamp": timestamp
            })
        
        # Rerun to update the chat display
        st.rerun()

def send_message_to_api(message: str):
    """Helper function to send message to API and handle response"""
    try:
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        with st.spinner("🤖 TailorTalk Enhanced is thinking..."):
            response = requests.post(
                f"{st.session_state.api_url}/chat",
                json={
                    "message": message,
                    "user_id": f"streamlit_user_{int(time.time())}"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                assistant_response = data["response"]
                agent_type = data.get("agent_type", "unknown")
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": assistant_response,
                    "agent_type": agent_type,
                    "timestamp": timestamp
                })
                
                # Show success notification
                if agent_type == 'enhanced':
                    st.success("✅ Enhanced Agent Response!")
                else:
                    st.success("✅ Response received!")
                
                return True
            else:
                st.error(f"❌ API Error: {response.status_code}")
                return False
                
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return False

def render_enhanced_example_prompts():
    """Render enhanced example prompt buttons with working functionality"""
    st.markdown("---")
    st.markdown("### 💡 Try these enhanced examples:")
    
    # Row 1: Booking examples
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📅 Book tomorrow afternoon", key="example1", help="Book appointment for tomorrow afternoon"):
            message = "Book appointment on tomorrow afternoon"
            timestamp = datetime.now().strftime('%H:%M:%S')
            st.session_state.messages.append({"role": "user", "content": message, "timestamp": timestamp})
            
            if send_message_to_api(message):
                st.rerun()
    
    with col2:
        if st.button("🕐 Check Friday availability", key="example2", help="Check what's available this Friday"):
            message = "Check Friday availability"
            timestamp = datetime.now().strftime('%H:%M:%S')
            st.session_state.messages.append({"role": "user", "content": message, "timestamp": timestamp})
            
            if send_message_to_api(message):
                st.rerun()
    
    with col3:
        if st.button("📞 Book next week", key="example3", help="Schedule something for next week"):
            message = "Book a meeting for next week"
            timestamp = datetime.now().strftime('%H:%M:%S')
            st.session_state.messages.append({"role": "user", "content": message, "timestamp": timestamp})
            
            if send_message_to_api(message):
                st.rerun()
    
    # Row 2: More specific examples
    col4, col5, col6 = st.columns(3)
    
    with col4:
        if st.button("🌅 Morning meeting", key="example4", help="Schedule a morning meeting"):
            message = "Schedule a meeting for tomorrow morning at 10 AM"
            timestamp = datetime.now().strftime('%H:%M:%S')
            st.session_state.messages.append({"role": "user", "content": message, "timestamp": timestamp})
            
            if send_message_to_api(message):
                st.rerun()
    
    with col5:
        if st.button("📋 Check today's schedule", key="example5", help="See today's availability"):
            message = "What's my availability for today?"
            timestamp = datetime.now().strftime('%H:%M:%S')
            st.session_state.messages.append({"role": "user", "content": message, "timestamp": timestamp})
            
            if send_message_to_api(message):
                st.rerun()
    
    with col6:
        if st.button("👋 Say hello", key="example6", help="Greet TailorTalk"):
            message = "Hello! How can you help me with scheduling?"
            timestamp = datetime.now().strftime('%H:%M:%S')
            st.session_state.messages.append({"role": "user", "content": message, "timestamp": timestamp})
            
            if send_message_to_api(message):
                st.rerun()
    
    # Row 3: Enhanced examples
    st.markdown("**🎯 Enhanced Parsing Examples:**")
    col7, col8, col9 = st.columns(3)
    
    with col7:
        if st.button("📅 5th July 3:30pm", key="example7", help="Test precise date/time parsing"):
            message = "Book appointment on 5th July at 3:30pm"
            timestamp = datetime.now().strftime('%H:%M:%S')
            st.session_state.messages.append({"role": "user", "content": message, "timestamp": timestamp})
            
            if send_message_to_api(message):
                st.rerun()
    
    with col8:
        if st.button("📅 4th August 15:00", key="example8", help="Test 24-hour format"):
            message = "Schedule meeting for 4th August at 15:00"
            timestamp = datetime.now().strftime('%H:%M:%S')
            st.session_state.messages.append({"role": "user", "content": message, "timestamp": timestamp})
            
            if send_message_to_api(message):
                st.rerun()
    
    with col9:
        if st.button("📅 Next Monday morning", key="example9", help="Test relative date parsing"):
            message = "Book appointment for next Monday morning"
            timestamp = datetime.now().strftime('%H:%M:%S')
            st.session_state.messages.append({"role": "user", "content": message, "timestamp": timestamp})
            
            if send_message_to_api(message):
                st.rerun()

def render_enhanced_controls():
    """Render enhanced controls with real-time features"""
    st.markdown("---")
    st.markdown("### 🔧 Enhanced Controls")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.messages = []
            st.success("✅ Chat cleared!")
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh All", key="refresh_all"):
            # Refresh system status
            st.session_state.system_status = check_api_health()
            
            # Refresh current availability
            if st.session_state.availability_data:
                for date_str in st.session_state.availability_data.keys():
                    get_availability(date_str, use_realtime=True)
            
            st.success("✅ All data refreshed!")
            st.rerun()
    
    with col3:
        if st.button("📖 Enhanced Help", key="enhanced_help"):
            help_message = """
            **🚀 TailorTalk Enhanced Help:**
            
            **Enhanced Features:**
            • **Precise Parsing**: "5th July at 3:30pm", "4th August 15:00"
            • **Real-time Updates**: Availability refreshes automatically
            • **Smart Conversations**: Context-aware responses
            • **Multiple Agents**: Enhanced, OpenAI, and Fallback modes
            
            **Booking Examples:**
            • "Book appointment on 5th July at 3:30pm"
            • "Schedule meeting for August 4th at 15:00"
            • "Book for tomorrow at 2 PM"
            • "Show me availability for next Monday"
            
            **Date Formats Supported:**
            • Specific: "5th July", "August 4th", "July 5th"
            • Relative: "tomorrow", "next Monday", "next week"
            • Numeric: "2025-07-05", "5/7/2025"
            
            **Time Formats Supported:**
            • 12-hour: "3:30pm", "11:45am"
            • 24-hour: "15:00", "09:30"
            • Relative: "morning", "afternoon", "evening"
            
            **Real-time Features:**
            • Auto-refresh availability every 30 seconds
            • Live status indicators
            • Instant booking confirmations
            """
            
            timestamp = datetime.now().strftime('%H:%M:%S')
            st.session_state.messages.append({
                "role": "system", 
                "content": help_message,
                "timestamp": timestamp
            })
            st.rerun()
    
    with col4:
        if st.button("🧪 Test Enhanced API", key="test_enhanced"):
            with st.spinner("Testing enhanced API endpoints..."):
                # Test health endpoint
                health_data = check_api_health()
                
                # Test parsing endpoint
                try:
                    parse_response = requests.get(
                        f"{st.session_state.api_url}/parse-datetime",
                        params={"text": "5th July at 3:30pm"},
                        timeout=10
                    )
                    parse_success = parse_response.status_code == 200
                except:
                    parse_success = False
                
                # Test availability endpoint
                try:
                    today = datetime.now().strftime('%Y-%m-%d')
                    avail_response = requests.get(
                        f"{st.session_state.api_url}/availability/{today}",
                        timeout=10
                    )
                    avail_success = avail_response.status_code == 200
                except:
                    avail_success = False
                
                # Display results
                results = f"""
                **🧪 Enhanced API Test Results:**
                
                • **Health Check**: {'✅ Pass' if health_data.get('status') == 'healthy' else '❌ Fail'}
                • **Enhanced Parsing**: {'✅ Pass' if parse_success else '❌ Fail'}
                • **Availability Check**: {'✅ Pass' if avail_success else '❌ Fail'}
                • **System Status**: {health_data.get('status', 'unknown').title()}
                • **Active Agent**: {health_data.get('config', {}).get('active_agent_type', 'unknown').title()}
                
                **Enhanced Features Status:**
                """
                
                enhanced_features = health_data.get('enhanced_features', {})
                for feature, enabled in enhanced_features.items():
                    status = '✅ Enabled' if enabled else '❌ Disabled'
                    feature_name = feature.replace('_', ' ').title()
                    results += f"\n• **{feature_name}**: {status}"
                
                timestamp = datetime.now().strftime('%H:%M:%S')
                st.session_state.messages.append({
                    "role": "system", 
                    "content": results,
                    "timestamp": timestamp
                })
                st.rerun()

def render_real_time_availability():
    """Render real-time availability display"""
    if st.session_state.availability_data:
        st.markdown("---")
        st.markdown("### 📊 Real-time Availability")
        
        for date_str, data in st.session_state.availability_data.items():
            with st.expander(f"📅 {data.get('formatted_date', date_str)} ({data.get('total_slots', 0)} slots)"):
                slots = data.get('available_slots', [])
                realtime_enabled = data.get('realtime_enabled', False)
                last_updated = data.get('last_updated', '')
                
                if realtime_enabled:
                    st.markdown('<span class="realtime-indicator"></span> Real-time updates enabled', unsafe_allow_html=True)
                
                if slots:
                    # Create a grid of available slots
                    cols = st.columns(3)
                    for i, slot in enumerate(slots):
                        with cols[i % 3]:
                            time_obj = datetime.strptime(slot, '%H:%M').time()
                            formatted_time = time_obj.strftime('%I:%M %p')
                            st.markdown(f"""
                            <div class="availability-slot slot-available">
                                <span><strong>{slot}</strong></span>
                                <span>{formatted_time}</span>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.markdown('<div class="availability-slot slot-booked">No available slots</div>', unsafe_allow_html=True)
                
                if last_updated:
                    try:
                        updated_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                        st.caption(f"🕐 Last updated: {updated_time.strftime('%H:%M:%S')}")
                    except:
                        st.caption(f"🕐 Last updated: {last_updated}")

def render_enhanced_footer():
    """Render the enhanced footer"""
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9em;">
        <p>🚀 <strong>TailorTalk Enhanced AI Booking Assistant</strong></p>
        <p>Powered by Enhanced AI Agents, Precise Date/Time Parsing, Real-time Calendar Integration</p>
        <p>Built with FastAPI, Streamlit, Google Calendar API, and ❤️</p>
        <p>✨ Features: Real-time Updates • Enhanced Parsing • Smart Conversations • Multiple AI Agents</p>
    </div>
    """, unsafe_allow_html=True)

def auto_refresh_availability():
    """Auto-refresh availability data if enabled"""
    if st.session_state.auto_refresh and st.session_state.availability_data:
        current_time = time.time()
        if (st.session_state.last_availability_check is None or 
            current_time - st.session_state.last_availability_check.timestamp() > 30):
            
            # Refresh availability for all tracked dates
            for date_str in list(st.session_state.availability_data.keys()):
                get_availability(date_str, use_realtime=True)

def main():
    """Enhanced main application function"""
    # Setup page configuration first
    setup_page_config()
    
    # Initialize session state
    initialize_session_state()
    
    # Apply enhanced custom CSS
    apply_custom_css()
    
    # Auto-refresh availability if enabled
    auto_refresh_availability()
    
    # Render enhanced sidebar
    render_enhanced_sidebar()
    
    # Render enhanced main chat interface
    render_enhanced_chat_interface()
    
    # Handle enhanced chat input
    handle_enhanced_chat_input()
    
    # Render enhanced example prompts
    render_enhanced_example_prompts()
    
    # Render enhanced controls
    render_enhanced_controls()
    
    # Render real-time availability
    render_real_time_availability()
    
    # Render enhanced footer
    render_enhanced_footer()

if __name__ == "__main__":
    main()

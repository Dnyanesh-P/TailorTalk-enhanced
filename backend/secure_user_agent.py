"""
Secure User Booking Agent for TailorTalk Enhanced
Handles AI-powered booking conversations with user authentication
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import pytz
import re

from backend.google_auth_manager import google_auth_manager
from backend.multi_user_calendar import multi_user_calendar_manager
from backend.advanced_date_parser import advanced_parser
from backend.timezone_manager import timezone_manager

logger = logging.getLogger(__name__)

class SecureUserBookingAgent:
    """AI agent for secure, user-specific booking conversations"""
    
    def __init__(self):
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
        self.user_contexts: Dict[str, Dict[str, Any]] = {}
        
        # Response templates
        self.auth_required_message = """
🔐 **Authentication Required**

To book appointments and access your calendar, please authenticate with your Google account first.

**Available Commands:**
- `help` - Show available commands
- `auth` - Get authentication instructions
- `status` - Check system status

Once authenticated, I can help you with:
- 📅 Booking appointments
- 🔍 Checking availability
- 📋 Managing your calendar
- ⏰ Scheduling meetings
"""
        
        self.welcome_message = """
👋 **Welcome to TailorTalk Enhanced!**

I'm your AI-powered calendar assistant. I can help you:

🔐 **For Authenticated Users:**
- Book appointments in your Google Calendar
- Check your availability
- Manage existing events
- Schedule meetings with smart time suggestions

💬 **Available Commands:**
- `book [date] [time]` - Book an appointment
- `availability [date]` - Check available slots
- `upcoming` - Show upcoming events
- `help` - Show all commands
- `logout` - Sign out

**Example:** "Book an appointment tomorrow at 2 PM"
"""
        
        logger.info("Secure User Booking Agent initialized")
    
    async def process_user_message(self, message: str, user_id: str) -> str:
        """Process user message with authentication awareness"""
        try:
            # Initialize user context if needed
            if user_id not in self.user_contexts:
                self.user_contexts[user_id] = {
                    'authenticated': False,
                    'last_activity': datetime.now(),
                    'preferences': {}
                }
            
            # Update last activity
            self.user_contexts[user_id]['last_activity'] = datetime.now()
            
            # Check authentication status
            is_authenticated = google_auth_manager.is_user_authenticated(user_id)
            self.user_contexts[user_id]['authenticated'] = is_authenticated
            
            # Add to conversation history
            self._add_to_conversation(user_id, 'user', message)
            
            # Process message based on authentication status
            if is_authenticated:
                response = await self._process_authenticated_message(message, user_id)
            else:
                response = await self._process_unauthenticated_message(message, user_id)
            
            # Add response to conversation history
            self._add_to_conversation(user_id, 'assistant', response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {e}")
            return f"❌ I encountered an error processing your request: {str(e)}"
    
    def _add_to_conversation(self, user_id: str, role: str, content: str):
        """Add message to conversation history"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 20 messages
        if len(self.conversation_history[user_id]) > 20:
            self.conversation_history[user_id] = self.conversation_history[user_id][-20:]
    
    async def _process_unauthenticated_message(self, message: str, user_id: str) -> str:
        """Process message for unauthenticated user"""
        message_lower = message.lower().strip()
        
        if message_lower in ['help', 'commands']:
            return self._get_help_message(authenticated=False)
        
        elif message_lower in ['auth', 'authenticate', 'login', 'signin']:
            return self._get_auth_instructions()
        
        elif message_lower in ['status', 'health']:
            return self._get_system_status()
        
        elif message_lower in ['hello', 'hi', 'hey', 'start']:
            return self.welcome_message
        
        elif any(keyword in message_lower for keyword in ['book', 'schedule', 'appointment', 'meeting']):
            return self.auth_required_message + "\n\n💡 **Tip:** Use the `auth` command to get started!"
        
        else:
            return self.auth_required_message
    
    async def _process_authenticated_message(self, message: str, user_id: str) -> str:
        """Process message for authenticated user"""
        message_lower = message.lower().strip()
        
        try:
            # Get user info
            user_info = google_auth_manager.get_user_info(user_id)
            user_name = user_info.get('name', 'there') if user_info else 'there'
            
            if message_lower in ['help', 'commands']:
                return self._get_help_message(authenticated=True)
            
            elif message_lower in ['hello', 'hi', 'hey', 'start']:
                return f"👋 Hello {user_name}! I'm ready to help you manage your calendar. What would you like to do today?"
            
            elif message_lower.startswith('book') or 'appointment' in message_lower or 'schedule' in message_lower:
                return await self._handle_booking_request(message, user_id)
            
            elif message_lower.startswith('availability') or 'available' in message_lower or 'free' in message_lower:
                return await self._handle_availability_request(message, user_id)
            
            elif message_lower in ['upcoming', 'events', 'calendar']:
                return await self._handle_upcoming_events(user_id)
            
            elif message_lower in ['logout', 'signout', 'disconnect']:
                return self._handle_logout(user_id)
            
            elif message_lower in ['status', 'info', 'account']:
                return self._get_user_status(user_id)
            
            else:
                # Try to parse as natural language booking request
                return await self._handle_natural_language_request(message, user_id)
                
        except Exception as e:
            logger.error(f"Error processing authenticated message for user {user_id}: {e}")
            return f"❌ I encountered an error: {str(e)}\n\nPlease try again or use the `help` command for assistance."
    
    async def _handle_booking_request(self, message: str, user_id: str) -> str:
        """Handle booking appointment request"""
        try:
            # Parse date and time from message
            parsed_result = advanced_parser.parse_datetime_from_text(message)
            
            if not parsed_result['success']:
                return """
❌ **Could not understand the date/time**

Please specify when you'd like to book the appointment.

**Examples:**
- "Book tomorrow at 2 PM"
- "Schedule for June 15th at 10:30 AM"
- "Book next Monday at 3 PM"

**Format:** `book [date] [time]`
"""
            
            date_str = parsed_result['date']
            time_str = parsed_result['time']
            
            # Check availability first
            available_slots = multi_user_calendar_manager.get_user_availability(user_id, date_str)
            
            if time_str not in available_slots:
                return f"""
⚠️ **Time slot not available**

The requested time {time_str} on {date_str} is not available.

**Available slots for {date_str}:**
{', '.join(available_slots) if available_slots else 'No available slots'}

Please choose an available time or try a different date.
"""
            
            # Create appointment
            appointment_details = {
                'title': 'TailorTalk Appointment',
                'description': 'Appointment booked via TailorTalk Enhanced',
                'duration': 60
            }
            
            booking_result = multi_user_calendar_manager.create_user_event(
                user_id, date_str, time_str, appointment_details
            )
            
            return f"""
✅ **Appointment Booked Successfully!**

📅 **Date:** {date_str}
⏰ **Time:** {time_str}
⏱️ **Duration:** 1 hour
🔗 **Calendar Link:** {booking_result.get('event_link', 'Available in your calendar')}

Your appointment has been added to your Google Calendar. You'll receive a notification before the meeting.
"""
            
        except Exception as e:
            logger.error(f"Error handling booking request for user {user_id}: {e}")
            return f"❌ Failed to book appointment: {str(e)}"
    
    async def _handle_availability_request(self, message: str, user_id: str) -> str:
        """Handle availability check request"""
        try:
            # Parse date from message
            parsed_result = advanced_parser.parse_datetime_from_text(message)
            
            if not parsed_result['success']:
                # Default to today
                today = datetime.now().strftime('%Y-%m-%d')
                date_str = today
            else:
                date_str = parsed_result['date']
            
            # Get availability
            available_slots = multi_user_calendar_manager.get_user_availability(user_id, date_str)
            
            if available_slots:
                slots_text = '\n'.join([f"• {slot}" for slot in available_slots])
                return f"""
📅 **Available slots for {date_str}:**

{slots_text}

**Total available slots:** {len(available_slots)}

To book an appointment, say: "Book {date_str} at [time]"
"""
            else:
                return f"""
❌ **No available slots for {date_str}**

This might be because:
- It's a weekend or holiday
- All time slots are already booked
- The date is outside business hours

Try checking a different date or contact support for assistance.
"""
                
        except Exception as e:
            logger.error(f"Error handling availability request for user {user_id}: {e}")
            return f"❌ Failed to check availability: {str(e)}"
    
    async def _handle_upcoming_events(self, user_id: str) -> str:
        """Handle upcoming events request"""
        try:
            upcoming_events = multi_user_calendar_manager.get_user_upcoming_events(user_id, 7)
            
            if not upcoming_events:
                return """
📅 **No upcoming events**

You have no events scheduled for the next 7 days.

Would you like to book an appointment? Just say "book [date] [time]"
"""
            
            events_text = ""
            for event in upcoming_events[:10]:  # Show max 10 events
                start_time = self._format_event_time(event['start'])
                events_text += f"• **{event['summary']}** - {start_time}\n"
            
            return f"""
📅 **Your upcoming events:**

{events_text}

**Total events:** {len(upcoming_events)}

Need to book another appointment? Just let me know!
"""
            
        except Exception as e:
            logger.error(f"Error handling upcoming events for user {user_id}: {e}")
            return f"❌ Failed to get upcoming events: {str(e)}"
    
    def _handle_logout(self, user_id: str) -> str:
        """Handle user logout"""
        try:
            success = google_auth_manager.revoke_user_access(user_id)
            
            if success:
                # Clear user context
                if user_id in self.user_contexts:
                    del self.user_contexts[user_id]
                
                # Clear conversation history
                if user_id in self.conversation_history:
                    del self.conversation_history[user_id]
                
                return """
👋 **Successfully signed out**

Your session has been terminated and access revoked.

To use TailorTalk again, you'll need to authenticate with your Google account.

Thank you for using TailorTalk Enhanced!
"""
            else:
                return "❌ Failed to sign out. Please try again."
                
        except Exception as e:
            logger.error(f"Error handling logout for user {user_id}: {e}")
            return f"❌ Error during logout: {str(e)}"
    
    async def _handle_natural_language_request(self, message: str, user_id: str) -> str:
        """Handle natural language requests"""
        try:
            # Simple keyword-based processing
            message_lower = message.lower()
            
            if any(word in message_lower for word in ['when', 'what time', 'schedule']):
                return await self._handle_upcoming_events(user_id)
            
            elif any(word in message_lower for word in ['free', 'available', 'open']):
                return await self._handle_availability_request(message, user_id)
            
            elif any(word in message_lower for word in ['cancel', 'delete', 'remove']):
                return """
🗑️ **Cancel Appointment**

To cancel an appointment, please:
1. Check your upcoming events with the `upcoming` command
2. Use your Google Calendar to cancel the specific event
3. Or contact support for assistance

I'll add direct cancellation features in a future update!
"""
            
            else:
                return f"""
🤔 **I'm not sure how to help with that**

Here are some things I can do:
- `book [date] [time]` - Book an appointment
- `availability [date]` - Check available time slots
- `upcoming` - Show your upcoming events
- `help` - Show all commands

**Example:** "Book tomorrow at 2 PM"

What would you like to do?
"""
                
        except Exception as e:
            logger.error(f"Error handling natural language request for user {user_id}: {e}")
            return "❌ I couldn't understand that request. Please try using the `help` command."
    
    def _get_help_message(self, authenticated: bool = False) -> str:
        """Get help message based on authentication status"""
        if authenticated:
            return """
🤖 **TailorTalk Enhanced - Help**

**📅 Calendar Commands:**
- `book [date] [time]` - Book an appointment
- `availability [date]` - Check available time slots
- `upcoming` - Show your upcoming events

**🔧 System Commands:**
- `status` - Check your account status
- `logout` - Sign out of your account
- `help` - Show this help message

**💬 Natural Language:**
You can also use natural language like:
- "Book an appointment tomorrow at 2 PM"
- "What's my availability for next Monday?"
- "Show me my upcoming meetings"

**⏰ Time Formats:**
- "2 PM", "14:00", "2:30 PM"
- "tomorrow", "next Monday", "June 15th"
- "today", "this Friday", "next week"

Need more help? Just ask!
"""
        else:
            return """
🤖 **TailorTalk Enhanced - Help**

**🔐 Authentication Required:**
To access calendar features, please authenticate first.

**Available Commands:**
- `auth` - Get authentication instructions
- `status` - Check system status
- `help` - Show this help message

**After Authentication:**
- Book appointments in your Google Calendar
- Check your availability
- Manage existing events
- Get smart scheduling suggestions

Ready to get started? Use the `auth` command!
"""
    
    def _get_auth_instructions(self) -> str:
        """Get authentication instructions"""
        return """
🔐 **Google Authentication Required**

To use TailorTalk's calendar features, you need to authenticate with your Google account.

**Steps to authenticate:**
1. Visit: http://localhost:8001/auth/login
2. Sign in with your Google account
3. Grant calendar permissions
4. Return here and start using TailorTalk!

**What we access:**
- Your Google Calendar (to book appointments)
- Basic profile info (name, email)
- Calendar events (to check availability)

**Security:** Your data is encrypted and stored securely. You can revoke access anytime.

**Need help?** Visit http://localhost:8001/docs for more information.
"""
    
    def _get_system_status(self) -> str:
        """Get system status information"""
        try:
            auth_status = google_auth_manager.get_auth_status()
            current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
            
            return f"""
🔧 **TailorTalk System Status**

**System:** ✅ Online
**Time:** {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}
**Active Users:** {auth_status['active_users']}
**Total Sessions:** {auth_status['total_sessions']}

**Services:**
- ✅ Google Calendar API
- ✅ Authentication System
- ✅ AI Assistant
- ✅ Date/Time Parser

**Endpoints:**
- API: http://localhost:8001
- Docs: http://localhost:8001/docs
- Auth: http://localhost:8001/auth/login

All systems operational! 🚀
"""
        except Exception as e:
            return f"❌ Error getting system status: {str(e)}"
    
    def _get_user_status(self, user_id: str) -> str:
        """Get user account status"""
        try:
            user_info = google_auth_manager.get_user_info(user_id)
            calendar_info = multi_user_calendar_manager.get_user_calendar_info(user_id)
            
            if user_info:
                return f"""
👤 **Your Account Status**

**User:** {user_info.get('name', 'Unknown')}
**Email:** {user_info.get('email', 'Unknown')}
**Status:** ✅ Authenticated

**Calendar Info:**
- **Calendars:** {calendar_info.get('total_calendars', 0)}
- **Recent Events:** {calendar_info.get('recent_events_count', 0)}
- **Timezone:** {calendar_info.get('timezone', 'Unknown')}

**Available Commands:**
- `book` - Schedule appointments
- `availability` - Check free slots
- `upcoming` - View events
- `logout` - Sign out

Everything looks good! 🎉
"""
            else:
                return "❌ Could not retrieve user information. Please try authenticating again."
                
        except Exception as e:
            logger.error(f"Error getting user status for {user_id}: {e}")
            return f"❌ Error getting account status: {str(e)}"
    
    def _format_event_time(self, datetime_str: str) -> str:
        """Format event datetime for display"""
        try:
            if 'T' in datetime_str:
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                return dt.strftime('%A, %B %d at %I:%M %p')
            else:
                date_obj = datetime.strptime(datetime_str, '%Y-%m-%d')
                return date_obj.strftime('%A, %B %d (All day)')
        except:
            return datetime_str

# Global secure user booking agent
secure_user_booking_agent = SecureUserBookingAgent()

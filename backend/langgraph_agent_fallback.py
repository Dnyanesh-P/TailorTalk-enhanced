"""
Fallback AI agent that works without OpenAI API
Uses rule-based logic for booking requests
"""

from typing import TypedDict, List, Optional
import re
from datetime import datetime, timedelta
import json
import os
import pytz
from dotenv import load_dotenv
from backend.google_calendar import get_calendar_manager

# Load environment variables
load_dotenv()

# Define the state structure
class ConversationState(TypedDict):
    messages: List[dict]
    user_intent: Optional[str]
    extracted_info: dict
    current_step: str
    available_slots: List[str]
    selected_slot: Optional[str]
    booking_confirmed: bool

class FallbackBookingAgent:
    def __init__(self):
        # Get timezone
        self.timezone_str = os.getenv('TIMEZONE', 'Asia/Kolkata')
        self.timezone = pytz.timezone(self.timezone_str)
        
        print(f"🤖 Initializing Fallback BookingAgent with timezone: {self.timezone_str}")
        print("⚠️ Using rule-based logic (no OpenAI API required)")
        print("✅ Fallback BookingAgent initialized successfully!")
    
    def _understand_intent(self, message: str) -> str:
        """Understand user intent using rule-based logic"""
        message_lower = message.lower().strip()
        
        # Time pattern matching (e.g., "10:00", "3pm", "15:30")
        time_patterns = [
            r'\b\d{1,2}:\d{2}\b',  # 10:00, 15:30
            r'\b\d{1,2}\s*pm\b',   # 3pm, 3 pm
            r'\b\d{1,2}\s*am\b',   # 10am, 10 am
        ]
        
        has_time = any(re.search(pattern, message_lower) for pattern in time_patterns)
        
        # Booking keywords
        booking_keywords = ["book", "schedule", "appointment", "meeting", "call", "tomorrow", "today", "next week", "afternoon", "morning", "evening"]
        confirmation_keywords = ["yes", "confirm", "book it", "that works", "sounds good", "perfect", "ok", "okay", "sure"]
        availability_keywords = ["availability", "available", "free time", "free", "check", "slots"]
        
        # If message is just a time (like "10:00"), treat as time selection
        if has_time and len(message_lower.split()) <= 2:
            return "time_selection"
        elif any(keyword in message_lower for keyword in confirmation_keywords):
            return "confirmation"
        elif any(keyword in message_lower for keyword in booking_keywords) or has_time:
            return "booking_request"
        elif any(keyword in message_lower for keyword in availability_keywords):
            return "availability_check"
        else:
            return "general_question"
    
    def _extract_time_from_message(self, message: str) -> Optional[str]:
        """Extract time from message and convert to 24-hour format"""
        message_lower = message.lower().strip()
        
        # Pattern for HH:MM format
        time_match = re.search(r'\b(\d{1,2}):(\d{2})\b', message_lower)
        if time_match:
            hour, minute = time_match.groups()
            return f"{int(hour):02d}:{minute}"
        
        # Pattern for AM/PM format
        am_pm_match = re.search(r'\b(\d{1,2})\s*(am|pm)\b', message_lower)
        if am_pm_match:
            hour, period = am_pm_match.groups()
            hour = int(hour)
            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
            return f"{hour:02d}:00"
        
        return None
    
    def _extract_booking_info(self, message: str) -> dict:
        """Extract booking information using rule-based logic"""
        message_lower = message.lower()
        now_ist = datetime.now(self.timezone)
        today = now_ist.date()
        tomorrow = today + timedelta(days=1)
        
        extracted_info = {
            "date": None,
            "time": None,
            "duration": 60,
            "meeting_type": "Meeting"
        }
        
        # Extract date
        if "today" in message_lower:
            extracted_info["date"] = today.strftime('%Y-%m-%d')
        elif "tomorrow" in message_lower:
            extracted_info["date"] = tomorrow.strftime('%Y-%m-%d')
        elif "next week" in message_lower:
            next_week = today + timedelta(days=7)
            extracted_info["date"] = next_week.strftime('%Y-%m-%d')
        
        # Extract time
        if "morning" in message_lower:
            extracted_info["time"] = "10:00"
        elif "afternoon" in message_lower:
            extracted_info["time"] = "15:00"
        elif "evening" in message_lower:
            extracted_info["time"] = "18:00"
        elif "3pm" in message_lower or "3 pm" in message_lower:
            extracted_info["time"] = "15:00"
        elif "10am" in message_lower or "10 am" in message_lower:
            extracted_info["time"] = "10:00"
        
        # Extract meeting type
        if "call" in message_lower:
            extracted_info["meeting_type"] = "Call"
        elif "meeting" in message_lower:
            extracted_info["meeting_type"] = "Meeting"
        elif "consultation" in message_lower:
            extracted_info["meeting_type"] = "Consultation"
        
        return extracted_info
    
    def _check_availability(self, date: str) -> List[str]:
        """Check calendar availability"""
        try:
            calendar_manager = get_calendar_manager()
            available_slots = calendar_manager.get_availability(date)
            return available_slots
        except Exception as e:
            print(f"❌ Error checking availability: {e}")
            # Fallback slots
            return ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
    
    def _format_date(self, date_str: str) -> str:
        """Format date for display"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%A, %B %d, %Y')
        except:
            return date_str
    
    async def process_message(self, message: str, user_id: str = "default") -> str:
        """Process a user message using rule-based logic with state management"""
        try:
            print(f"🔄 Processing message with fallback agent: {message}")
        
            # Simple state management using class attributes
            if not hasattr(self, 'user_states'):
                self.user_states = {}
        
            if user_id not in self.user_states:
                self.user_states[user_id] = {
                    'step': 'initial',
                    'pending_booking': None,
                    'available_slots': [],
                    'selected_date': None
                }
        
            user_state = self.user_states[user_id]
        
            # Understand intent
            intent = self._understand_intent(message)
            print(f"🎯 Detected intent: {intent}")
            print(f"📊 User state: {user_state}")
        
            now_ist = datetime.now(self.timezone)
            current_time = now_ist.strftime('%I:%M %p IST on %A, %B %d, %Y')
        
            if intent == "time_selection" and user_state['step'] == 'awaiting_time':
                # User selected a time slot
                selected_time = self._extract_time_from_message(message)
                if selected_time and selected_time in user_state['available_slots']:
                    # Prepare booking details
                    user_state['pending_booking'] = {
                        'date': user_state['selected_date'],
                        'time': selected_time,
                        'duration': 60,
                        'meeting_type': 'Call'
                    }
                    user_state['step'] = 'confirming_booking'
                
                    formatted_date = self._format_date(user_state['selected_date'])
                
                    return f"""
Perfect! I'll book **{selected_time}** on **{formatted_date}** for you.

📅 **Booking Details:**
• **Date:** {formatted_date}
• **Time:** {selected_time} IST
• **Duration:** 60 minutes
• **Type:** Call

Would you like me to confirm and book this appointment? Reply with "yes" to proceed.
                    """
                else:
                    return f"Sorry, **{selected_time}** is not available. Please choose from the available slots I showed earlier."
        
            elif intent == "confirmation" and user_state['step'] == 'confirming_booking':
                # User confirmed the booking - actually create the event
                booking_details = user_state['pending_booking']
            
                try:
                    # Create the calendar event
                    calendar_manager = get_calendar_manager()
                
                    datetime_str = f"{booking_details['date']} {booking_details['time']}"
                    booking_datetime_naive = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
                    booking_datetime = self.timezone.localize(booking_datetime_naive)
                
                    event_id = calendar_manager.create_event(
                        title=booking_details['meeting_type'],
                        start_datetime=booking_datetime,
                        duration_minutes=booking_details['duration'],
                        description="Booked via TailorTalk AI Assistant"
                    )
                
                    formatted_date = self._format_date(booking_details['date'])
                    formatted_time = booking_datetime.strftime('%I:%M %p')
                
                    # Reset user state
                    user_state['step'] = 'initial'
                    user_state['pending_booking'] = None
                    user_state['available_slots'] = []
                    user_state['selected_date'] = None
                
                    return f"""
✅ **Appointment Successfully Booked!**

📅 **Date:** {formatted_date}
🕐 **Time:** {formatted_time} IST
⏱️ **Duration:** {booking_details['duration']} minutes
🆔 **Event ID:** {event_id}

Your appointment has been added to your Google Calendar. You should receive a calendar notification before the meeting.

Is there anything else I can help you with?
                    """
                
                except Exception as e:
                    print(f"❌ Booking error: {e}")
                    return f"❌ I encountered an error while booking your appointment: {str(e)}. Please try again."
        
            elif intent == "general_question":
                # Handle greetings and general questions
                message_lower = message.lower()
                if any(greeting in message_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
                    user_state['step'] = 'initial'  # Reset state
                    return f"""
Hello! 👋 I'm your TailorTalk AI booking assistant.

**Current time:** {current_time}

I can help you with:
📅 **Schedule appointments** - "Book a meeting for tomorrow afternoon"
🔍 **Check availability** - "What's my availability for today?"
📞 **Manage your calendar** - Real-time Google Calendar integration

**Quick examples to try:**
• "I want to schedule a call for tomorrow at 3 PM"
• "Book a meeting for tomorrow morning"
• "What's my availability for today?"

What would you like to schedule today?
                    """
                else:
                    return f"""
I'm your AI booking assistant! **Current time:** {current_time}

I can help you:
• **Book appointments**: "Schedule a call for tomorrow afternoon"
• **Check availability**: "What's my availability for today?"
• **Manage calendar**: Real-time Google Calendar integration

How can I help you today?
                    """
        
            elif intent == "availability_check":
                # Extract date for availability check
                extracted_info = self._extract_booking_info(message)
            
                # Default to today if no date specified
                if not extracted_info["date"]:
                    extracted_info["date"] = now_ist.date().strftime('%Y-%m-%d')
            
                date_to_check = extracted_info["date"]
                formatted_date = self._format_date(date_to_check)
            
                # Check availability
                available_slots = self._check_availability(date_to_check)
            
                # Update user state
                user_state['available_slots'] = available_slots
                user_state['selected_date'] = date_to_check
                user_state['step'] = 'showing_availability'
            
                if available_slots:
                    slots_text = ", ".join(available_slots)
                    return f"""
📅 **Availability for {formatted_date}:**

✅ **Available slots:** {slots_text}
🕐 **Total slots:** {len(available_slots)}
🌍 **Timezone:** IST (India Standard Time)

Would you like to book any of these slots? Just say the time like:
• "10:00"
• "3 PM"
• "15:00"
                    """
                else:
                    return f"❌ No available slots found for {formatted_date}. Would you like to try a different date?"
        
            elif intent == "booking_request":
                # Handle booking requests
                extracted_info = self._extract_booking_info(message)
            
                # Default to tomorrow if no date specified
                if not extracted_info["date"]:
                    tomorrow = (now_ist.date() + timedelta(days=1)).strftime('%Y-%m-%d')
                    extracted_info["date"] = tomorrow
            
                date_to_check = extracted_info["date"]
                formatted_date = self._format_date(date_to_check)
            
                # Check availability
                available_slots = self._check_availability(date_to_check)
            
                # Update user state
                user_state['available_slots'] = available_slots
                user_state['selected_date'] = date_to_check
            
                if extracted_info["time"] and extracted_info["time"] in available_slots:
                    # Specific time requested and available - prepare for confirmation
                    user_state['pending_booking'] = {
                        'date': date_to_check,
                        'time': extracted_info["time"],
                        'duration': extracted_info["duration"],
                        'meeting_type': extracted_info["meeting_type"]
                    }
                    user_state['step'] = 'confirming_booking'
                
                    return f"""
Great! **{extracted_info["time"]}** on **{formatted_date}** is available.

📅 **Booking Details:**
• **Date:** {formatted_date}
• **Time:** {extracted_info["time"]} IST
• **Duration:** {extracted_info["duration"]} minutes
• **Type:** {extracted_info["meeting_type"]}

Would you like me to book this appointment? Reply with "yes" to confirm.
                    """
                elif extracted_info["time"]:
                    # Specific time requested but not available
                    user_state['step'] = 'awaiting_time'
                    slots_text = ", ".join(available_slots[:5])
                    return f"""
Sorry, **{extracted_info["time"]}** is not available on **{formatted_date}**.

📅 **Available alternatives:** {slots_text}

Which time works for you? Just say the time like "10:00" or "3 PM".
                    """
                else:
                    # No specific time requested
                    user_state['step'] = 'awaiting_time'
                    if available_slots:
                        slots_text = ", ".join(available_slots[:5])
                        if len(available_slots) > 5:
                            slots_text += f" (and {len(available_slots)-5} more)"
                    
                        return f"""
I found these available slots on **{formatted_date}:**

🕐 **Available times:** {slots_text}

Which time works for you? Just say the time like:
• "10:00"
• "3 PM"
• "15:00"
                    """
        
            else:
                return "I'm here to help you book appointments. What would you like to schedule?"
            
        except Exception as e:
            print(f"❌ Error in fallback agent: {e}")
            return f"I apologize, but I encountered an error while processing your request. Please try again. Error: {str(e)}"

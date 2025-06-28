"""
Enhanced booking agent with precise appointment scheduling
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import pytz
from backend.precise_appointment_scheduler import precise_scheduler

logger = logging.getLogger(__name__)

class EnhancedBookingAgent:
    """Enhanced booking agent with precise date/time handling"""
    
    def __init__(self, timezone_str: str = 'Asia/Kolkata'):
        self.timezone = pytz.timezone(timezone_str)
        self.scheduler = precise_scheduler
        self.user_sessions = {}
        
    async def process_message(self, message: str, user_id: str = "default_user") -> str:
        """Process user message with enhanced appointment scheduling"""
        try:
            logger.info(f"Processing message from {user_id}: '{message}'")
            
            # Initialize user session if needed
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {
                    'conversation_history': [],
                    'current_context': {},
                    'last_action': None
                }
            
            session = self.user_sessions[user_id]
            
            # Add message to history
            session['conversation_history'].append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now(self.timezone).isoformat()
            })
            
            # Detect intent and process
            intent = self._detect_intent(message, session)
            
            if intent == 'appointment_booking':
                response = await self._handle_appointment_booking(message, user_id, session)
            elif intent == 'time_selection':
                response = await self._handle_time_selection(message, user_id, session)
            elif intent == 'date_selection':
                response = await self._handle_date_selection(message, user_id, session)
            elif intent == 'confirmation':
                response = await self._handle_confirmation(message, user_id, session)
            elif intent == 'availability_check':
                response = await self._handle_availability_check(message, user_id, session)
            elif intent == 'greeting':
                response = self._handle_greeting()
            elif intent == 'help':
                response = self._handle_help()
            else:
                response = self._handle_general_query(message)
            
            # Add response to history
            session['conversation_history'].append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now(self.timezone).isoformat()
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"❌ I'm experiencing technical difficulties. Please try again.\n\nError: {str(e)}"
    
    def _detect_intent(self, message: str, session: Dict) -> str:
        """Detect user intent from message and context"""
        message_lower = message.lower()
        
        # Check conversation context first
        last_action = session.get('last_action')
        
        if last_action == 'awaiting_time_selection':
            # User is selecting a time
            if any(pattern in message_lower for pattern in [':', 'am', 'pm', 'morning', 'afternoon', 'evening']):
                return 'time_selection'
        
        elif last_action == 'awaiting_date_selection':
            # User is selecting a date
            if any(pattern in message_lower for pattern in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'july', 'august', 'tomorrow']):
                return 'date_selection'
        
        elif last_action == 'awaiting_confirmation':
            # User is confirming booking
            if any(word in message_lower for word in ['yes', 'confirm', 'book', 'ok', 'sure', 'go ahead']):
                return 'confirmation'
        
        # Intent detection based on keywords
        booking_keywords = ['book', 'schedule', 'appointment', 'meeting', 'reserve', 'arrange']
        if any(keyword in message_lower for keyword in booking_keywords):
            return 'appointment_booking'
        
        availability_keywords = ['available', 'availability', 'free', 'slots', 'when', 'show me']
        if any(keyword in message_lower for keyword in availability_keywords):
            return 'availability_check'
        
        greeting_keywords = ['hello', 'hi', 'hey', 'good morning', 'good afternoon']
        if any(keyword in message_lower for keyword in greeting_keywords):
            return 'greeting'
        
        help_keywords = ['help', 'how', 'what can', 'commands', 'guide']
        if any(keyword in message_lower for keyword in help_keywords):
            return 'help'
        
        return 'general_query'
    
    async def _handle_appointment_booking(self, message: str, user_id: str, session: Dict) -> str:
        """Handle appointment booking requests"""
        try:
            # Use the precise scheduler
            result = await self.scheduler.schedule_appointment(message, user_id)
            
            # Update session context
            session['current_context'] = result
            session['last_action'] = result.get('next_action', 'completed')
            
            return result['message']
            
        except Exception as e:
            logger.error(f"Error handling appointment booking: {e}")
            return f"❌ Error processing your booking request: {str(e)}\n\nPlease try again with a format like: 'Book appointment on 5th July at 3:30pm'"
    
    async def _handle_time_selection(self, message: str, user_id: str, session: Dict) -> str:
        """Handle time selection from user"""
        try:
            # Extract time from message
            from backend.advanced_date_parser import advanced_parser
            parse_result = advanced_parser.parse_appointment_request(message)
            
            if parse_result['time']:
                # Get date from context
                context = session.get('current_context', {})
                appointment_details = context.get('appointment_details', {})
                date_str = appointment_details.get('date')
                
                if date_str:
                    # Try to book the appointment
                    full_request = f"book appointment on {date_str} at {parse_result['time']}"
                    result = await self.scheduler.schedule_appointment(full_request, user_id)
                    
                    session['current_context'] = result
                    session['last_action'] = result.get('next_action', 'completed')
                    
                    return result['message']
                else:
                    return "❌ I lost track of the date. Please start over with: 'Book appointment on [date] at [time]'"
            else:
                return "❌ I couldn't understand the time. Please specify a time like '3:30pm', '15:00', or 'afternoon'"
                
        except Exception as e:
            logger.error(f"Error handling time selection: {e}")
            return f"❌ Error processing time selection: {str(e)}"
    
    async def _handle_date_selection(self, message: str, user_id: str, session: Dict) -> str:
        """Handle date selection from user"""
        try:
            # Extract date from message
            from backend.advanced_date_parser import advanced_parser
            parse_result = advanced_parser.parse_appointment_request(message)
            
            if parse_result['date']:
                # Get time from context
                context = session.get('current_context', {})
                appointment_details = context.get('appointment_details', {})
                time_str = appointment_details.get('time')
                
                if time_str:
                    # Try to book the appointment
                    full_request = f"book appointment on {parse_result['date']} at {time_str}"
                    result = await self.scheduler.schedule_appointment(full_request, user_id)
                    
                    session['current_context'] = result
                    session['last_action'] = result.get('next_action', 'completed')
                    
                    return result['message']
                else:
                    return "❌ I lost track of the time. Please start over with: 'Book appointment on [date] at [time]'"
            else:
                return "❌ I couldn't understand the date. Please specify a date like '5th July', 'tomorrow', or 'next Monday'"
                
        except Exception as e:
            logger.error(f"Error handling date selection: {e}")
            return f"❌ Error processing date selection: {str(e)}"
    
    async def _handle_confirmation(self, message: str, user_id: str, session: Dict) -> str:
        """Handle booking confirmation"""
        try:
            context = session.get('current_context', {})
            appointment_details = context.get('appointment_details', {})
            
            if appointment_details.get('date') and appointment_details.get('time'):
                # Proceed with booking
                date_str = appointment_details['date']
                time_str = appointment_details['time']
                full_request = f"book appointment on {date_str} at {time_str}"
                
                result = await self.scheduler.schedule_appointment(full_request, user_id)
                
                session['current_context'] = result
                session['last_action'] = 'completed'
                
                return result['message']
            else:
                return "❌ Missing appointment details. Please start over with: 'Book appointment on [date] at [time]'"
                
        except Exception as e:
            logger.error(f"Error handling confirmation: {e}")
            return f"❌ Error confirming appointment: {str(e)}"
    
    async def _handle_availability_check(self, message: str, user_id: str, session: Dict) -> str:
        """Handle availability check requests"""
        try:
            # Parse for date
            from backend.advanced_date_parser import advanced_parser
            parse_result = advanced_parser.parse_appointment_request(message)
            
            if parse_result['date']:
                # Show availability for specific date
                result = await self.scheduler.schedule_appointment(f"show availability for {parse_result['date']}", user_id)
                return result['message']
            else:
                # Show general availability
                from backend.enhanced_calendar import get_enhanced_calendar_manager
                calendar_manager = get_enhanced_calendar_manager()
                
                today = datetime.now(self.timezone).date()
                tomorrow = today + timedelta(days=1)
                
                tomorrow_slots = calendar_manager.get_availability(tomorrow.strftime('%Y-%m-%d'))
                
                if tomorrow_slots:
                    formatted_date = tomorrow.strftime('%A, %B %d, %Y')
                    formatted_times = [f"• {slot}" for slot in tomorrow_slots[:5]]
                    
                    return f"📅 **Availability for {formatted_date}:**\n\n" + \
                           "\n".join(formatted_times) + \
                           f"\n\n📋 Total slots: {len(tomorrow_slots)}\n\n" + \
                           "To book, say: 'Book appointment tomorrow at [time]'"
                else:
                    return "❌ No availability found for tomorrow. Try asking for a specific date like 'Show availability for 5th July'"
                    
        except Exception as e:
            logger.error(f"Error handling availability check: {e}")
            return f"❌ Error checking availability: {str(e)}"
    
    def _handle_greeting(self) -> str:
        """Handle greeting messages"""
        current_time = datetime.now(self.timezone).strftime('%I:%M %p on %A, %B %d, %Y')
        
        return f"👋 Hello! I'm TailorTalk, your AI appointment booking assistant.\n\n" \
               f"🕐 Current time: {current_time}\n\n" \
               f"I can help you:\n" \
               f"• **Book appointments** - 'Book appointment on 5th July at 3:30pm'\n" \
               f"• **Check availability** - 'Show me available times for tomorrow'\n" \
               f"• **Schedule meetings** - 'Schedule meeting for next Monday morning'\n\n" \
               f"How can I help you today?"
    
    def _handle_help(self) -> str:
        """Handle help requests"""
        return f"🆘 **TailorTalk Help Guide**\n\n" \
               f"**📅 Booking Appointments:**\n" \
               f"• 'Book appointment on 5th July at 3:30pm'\n" \
               f"• 'Schedule meeting for August 4th at 15:00'\n" \
               f"• 'Book for tomorrow at 2 PM'\n\n" \
               f"**🕐 Supported Time Formats:**\n" \
               f"• 12-hour: '3:30pm', '11:45am'\n" \
               f"• 24-hour: '15:00', '09:30'\n" \
               f"• Relative: 'morning', 'afternoon', 'evening'\n\n" \
               f"**📆 Supported Date Formats:**\n" \
               f"• Specific: '5th July', 'August 4th', 'July 5th'\n" \
               f"• Relative: 'tomorrow', 'next Monday', 'next week'\n" \
               f"• Numeric: '2025-07-05', '5/7/2025'\n\n" \
               f"**❓ Need help?** Just ask me anything!"
    
    def _handle_general_query(self, message: str) -> str:
        """Handle general queries"""
        return f"I'm here to help you book appointments and manage your calendar.\n\n" \
               f"**Your message:** '{message}'\n\n" \
               f"**To book an appointment, try:**\n" \
               f"• 'Book appointment on 5th July at 3:30pm'\n" \
               f"• 'Schedule meeting for tomorrow at 2 PM'\n" \
               f"• 'Show me availability for next week'\n\n" \
               f"**Need help?** Just say 'help' for more options!"

# Global enhanced agent instance
enhanced_booking_agent = EnhancedBookingAgent()

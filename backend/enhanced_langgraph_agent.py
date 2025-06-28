"""
Enhanced LangGraph agent with advanced natural language processing
"""

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
from typing import TypedDict, List, Optional, Dict, Any
import re
from datetime import datetime, timedelta
import json
import os
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the enhanced state structure
class EnhancedConversationState(TypedDict):
    messages: List[dict]
    user_intent: Optional[str]
    extracted_info: dict
    current_step: str
    available_slots: List[str]
    selected_slot: Optional[str]
    booking_confirmed: bool
    user_preferences: dict
    conversation_context: dict
    error_count: int
    suggestions: List[str]

class EnhancedBookingAgent:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("❌ OpenAI API key not found in environment variables")
        
        # Get timezone
        self.timezone_str = os.getenv('TIMEZONE', 'Asia/Kolkata')
        self.timezone = pytz.timezone(self.timezone_str)
        
        # Initialize date/time parser
        try:
            from backend.date_time_parser import DateTimeParser
            self.datetime_parser = DateTimeParser(self.timezone_str)
            print("✅ Enhanced datetime parser loaded")
        except ImportError:
            self.datetime_parser = None
            print("⚠️ Enhanced datetime parser not available")
        
        print(f"🤖 Initializing Enhanced BookingAgent with timezone: {self.timezone_str}")
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            api_key=api_key
        )
        self.graph = self._create_graph()
        
        # User session storage (in production, use a proper database)
        self.user_sessions = {}
        
        print("✅ Enhanced BookingAgent initialized successfully!")
    
    def _create_graph(self):
        """Create the enhanced LangGraph workflow"""
        workflow = StateGraph(EnhancedConversationState)
        
        # Add nodes
        workflow.add_node("understand_intent", self._understand_intent)
        workflow.add_node("extract_datetime", self._extract_datetime)
        workflow.add_node("validate_datetime", self._validate_datetime)
        workflow.add_node("check_availability", self._check_availability)
        workflow.add_node("suggest_alternatives", self._suggest_alternatives)
        workflow.add_node("confirm_booking", self._confirm_booking)
        workflow.add_node("create_booking", self._create_booking)
        workflow.add_node("handle_modification", self._handle_modification)
        workflow.add_node("handle_cancellation", self._handle_cancellation)
        workflow.add_node("provide_help", self._provide_help)
        workflow.add_node("general_response", self._general_response)
        
        # Set entry point
        workflow.set_entry_point("understand_intent")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "understand_intent",
            self._route_after_intent,
            {
                "extract_datetime": "extract_datetime",
                "modify_booking": "handle_modification",
                "cancel_booking": "handle_cancellation",
                "help": "provide_help",
                "general": "general_response",
            }
        )
        
        workflow.add_edge("extract_datetime", "validate_datetime")
        
        workflow.add_conditional_edges(
            "validate_datetime",
            self._route_after_validation,
            {
                "check_availability": "check_availability",
                "suggest_alternatives": "suggest_alternatives",
                "ask_clarification": "provide_help",
            }
        )
        
        workflow.add_conditional_edges(
            "check_availability",
            self._route_after_availability,
            {
                "confirm": "confirm_booking",
                "suggest": "suggest_alternatives",
                "continue": END,
            }
        )
        
        workflow.add_edge("suggest_alternatives", END)
        workflow.add_edge("confirm_booking", "create_booking")
        workflow.add_edge("create_booking", END)
        workflow.add_edge("handle_modification", END)
        workflow.add_edge("handle_cancellation", END)
        workflow.add_edge("provide_help", END)
        workflow.add_edge("general_response", END)
        
        return workflow.compile()
    
    async def process_message(self, message: str, user_id: str = "default_user") -> str:
        """Process a user message through the enhanced workflow"""
        try:
            # Initialize or get user session
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {
                    "messages": [],
                    "user_intent": None,
                    "extracted_info": {},
                    "current_step": "start",
                    "available_slots": [],
                    "selected_slot": None,
                    "booking_confirmed": False,
                    "user_preferences": {},
                    "conversation_context": {},
                    "error_count": 0,
                    "suggestions": []
                }
            
            # Add user message to session
            self.user_sessions[user_id]["messages"].append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now(self.timezone).isoformat()
            })
            
            # Process through the graph
            result = await self.graph.ainvoke(self.user_sessions[user_id])
            
            # Extract response from the last assistant message
            assistant_messages = [msg for msg in result.get("messages", []) if msg.get("role") == "assistant"]
            if assistant_messages:
                response = assistant_messages[-1]["content"]
            else:
                response = self._generate_fallback_response(message)
            
            # Update session
            self.user_sessions[user_id] = result
            
            return response
            
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            return self._generate_fallback_response(message)
    
    def _understand_intent(self, state: EnhancedConversationState) -> EnhancedConversationState:
        """Enhanced intent understanding with context"""
        last_message = state["messages"][-1]["content"].lower()
        
        # Enhanced intent detection
        intents = {
            "booking_request": [
                "book", "schedule", "appointment", "meeting", "call", "reserve",
                "set up", "arrange", "plan", "tomorrow", "next week", "today"
            ],
            "modify_booking": [
                "change", "modify", "update", "reschedule", "move", "shift",
                "different time", "another day"
            ],
            "cancel_booking": [
                "cancel", "delete", "remove", "abort", "call off"
            ],
            "availability_check": [
                "available", "free", "availability", "open", "slots", "when"
            ],
            "confirmation": [
                "yes", "confirm", "book it", "that works", "sounds good",
                "perfect", "ok", "okay", "sure", "go ahead"
            ],
            "help": [
                "help", "how", "what can", "commands", "options", "guide"
            ]
        }
        
        # Score each intent
        intent_scores = {}
        for intent, keywords in intents.items():
            score = sum(1 for keyword in keywords if keyword in last_message)
            if score > 0:
                intent_scores[intent] = score
        
        # Get the highest scoring intent
        if intent_scores:
            detected_intent = max(intent_scores, key=intent_scores.get)
        else:
            detected_intent = "general_question"
        
        # Consider conversation context
        if state.get("current_step") == "awaiting_confirmation":
            if any(word in last_message for word in ["yes", "confirm", "ok", "sure"]):
                detected_intent = "confirmation"
        
        print(f"🎯 Detected intent: {detected_intent} (scores: {intent_scores})")
        state["user_intent"] = detected_intent
        state["current_step"] = "intent_understood"
        
        return state
    
    def _extract_datetime(self, state: EnhancedConversationState) -> EnhancedConversationState:
        """Extract date and time using enhanced parser"""
        last_message = state["messages"][-1]["content"]
        
        # Use the enhanced datetime parser if available
        if self.datetime_parser:
            parsed_result = self.datetime_parser.parse_datetime(last_message)
            print(f"📋 Enhanced parsing result: {parsed_result}")
            
            # Update extracted info
            if parsed_result['date']:
                state["extracted_info"]["date"] = parsed_result['date']
            if parsed_result['time']:
                state["extracted_info"]["time"] = parsed_result['time']
            
            state["extracted_info"]["confidence"] = parsed_result['confidence']
            state["extracted_info"]["parsed_components"] = parsed_result['parsed_components']
            
            # If no date/time found, get suggestions
            if not parsed_result['date'] and not parsed_result['time']:
                state["suggestions"] = self.datetime_parser.get_suggestions(last_message)
        else:
            # Fallback to basic parsing
            state["extracted_info"] = self._basic_datetime_extraction(last_message)
        
        state["current_step"] = "datetime_extracted"
        return state
    
    def _basic_datetime_extraction(self, text: str) -> dict:
        """Basic fallback datetime extraction"""
        extracted = {"confidence": 0.3}
        
        # Simple patterns
        if "tomorrow" in text.lower():
            tomorrow = (datetime.now(self.timezone) + timedelta(days=1)).date()
            extracted["date"] = tomorrow.strftime('%Y-%m-%d')
            extracted["confidence"] = 0.8
        
        # Basic time patterns
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)',
            r'(\d{1,2})\s*(am|pm)',
            r'(\d{1,2}):(\d{2})'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text.lower())
            if match:
                if len(match.groups()) == 3:  # 12-hour format
                    hour = int(match.group(1))
                    minute = int(match.group(2)) if match.group(2) else 0
                    period = match.group(3)
                    if period == 'pm' and hour != 12:
                        hour += 12
                    elif period == 'am' and hour == 12:
                        hour = 0
                    extracted["time"] = f"{hour:02d}:{minute:02d}"
                    extracted["confidence"] = 0.7
                break
        
        return extracted
    
    def _validate_datetime(self, state: EnhancedConversationState) -> EnhancedConversationState:
        """Validate extracted date and time"""
        extracted_info = state["extracted_info"]
        now = datetime.now(self.timezone)
        
        validation_issues = []
        
        # Validate date
        if extracted_info.get("date"):
            try:
                date_obj = datetime.strptime(extracted_info["date"], '%Y-%m-%d').date()
                if date_obj < now.date():
                    validation_issues.append("Date cannot be in the past")
                elif date_obj > now.date() + timedelta(days=365):
                    validation_issues.append("Date is too far in the future (max 1 year)")
            except ValueError:
                validation_issues.append("Invalid date format")
        else:
            # Default to tomorrow if no date specified
            tomorrow = (now + timedelta(days=1)).date()
            extracted_info["date"] = tomorrow.strftime('%Y-%m-%d')
            print(f"📅 No date specified, defaulting to tomorrow: {extracted_info['date']}")
        
        # Validate time
        if extracted_info.get("time"):
            try:
                time_obj = datetime.strptime(extracted_info["time"], '%H:%M').time()
                # Check if time is within business hours (can be configured)
                if time_obj.hour < 9 or time_obj.hour >= 18:
                    validation_issues.append("Time should be between 9 AM and 6 PM")
            except ValueError:
                validation_issues.append("Invalid time format")
        
        # Store validation results
        state["extracted_info"]["validation_issues"] = validation_issues
        state["current_step"] = "datetime_validated"
        
        return state
    
    def _check_availability(self, state: EnhancedConversationState) -> EnhancedConversationState:
        """Check calendar availability with enhanced logic"""
        try:
            # Import here to avoid circular imports
            from backend.enhanced_calendar import get_enhanced_calendar_manager
            calendar_manager = get_enhanced_calendar_manager()
            
            extracted_info = state["extracted_info"]
            date_to_check = extracted_info.get("date")
            requested_time = extracted_info.get("time")
            
            print(f"🔍 Checking availability for: {date_to_check} at {requested_time}")
            
            # Get available slots
            available_slots = calendar_manager.get_availability(date_to_check)
            state["available_slots"] = available_slots
            
            # Check if requested time is available
            if requested_time and requested_time in available_slots:
                state["selected_slot"] = requested_time
                state["current_step"] = "slot_available"
            elif requested_time:
                state["current_step"] = "slot_unavailable"
            else:
                state["current_step"] = "showing_options"
            
        except Exception as e:
            print(f"❌ Error checking availability: {e}")
            state["available_slots"] = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
            state["current_step"] = "availability_error"
        
        return state
    
    def _suggest_alternatives(self, state: EnhancedConversationState) -> EnhancedConversationState:
        """Suggest alternative times with intelligent recommendations"""
        available_slots = state["available_slots"]
        extracted_info = state["extracted_info"]
        requested_time = extracted_info.get("time")
        date = extracted_info.get("date")
        
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
        except:
            formatted_date = date
        
        if available_slots:
            # Intelligent suggestions based on requested time
            suggestions = []
            
            if requested_time:
                # Find closest available times
                try:
                    requested_hour = int(requested_time.split(':')[0])
                    closest_slots = sorted(available_slots, 
                                         key=lambda x: abs(int(x.split(':')[0]) - requested_hour))
                    suggestions = closest_slots[:3]
                except:
                    suggestions = available_slots[:3]
            else:
                # Suggest popular times
                popular_times = ["10:00", "14:00", "15:00", "16:00"]
                suggestions = [slot for slot in popular_times if slot in available_slots]
                if len(suggestions) < 3:
                    suggestions.extend([slot for slot in available_slots if slot not in suggestions][:3-len(suggestions)])
            
            if requested_time and requested_time not in available_slots:
                response = f"""
I'm sorry, but **{requested_time}** is not available on **{formatted_date}**.

📅 **Here are the closest available times:**
{chr(10).join([f"• **{slot}** ({datetime.strptime(slot, '%H:%M').strftime('%I:%M %p')})" for slot in suggestions])}

📋 **All available slots:** {', '.join(available_slots)}

Which time would work better for you? Just say the time like "10:00" or "2 PM".
                """
            else:
                response = f"""
📅 **Available times for {formatted_date}:**

🕐 **Recommended slots:**
{chr(10).join([f"• **{slot}** ({datetime.strptime(slot, '%H:%M').strftime('%I:%M %p')})" for slot in suggestions])}

📋 **All available:** {', '.join(available_slots)}

Which time works best for you?
                """
        else:
            response = f"""
❌ Unfortunately, there are no available slots on **{formatted_date}**.

💡 **Would you like to try:**
• **Tomorrow:** {(datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%A, %B %d')}
• **Next week:** {(datetime.strptime(date, '%Y-%m-%d') + timedelta(days=7)).strftime('%A, %B %d')}
• **A different day this week**

Just let me know what works for you!
            """
        
        state["messages"].append({"role": "assistant", "content": response})
        state["current_step"] = "alternatives_suggested"
        
        return state
    
    def _confirm_booking(self, state: EnhancedConversationState) -> EnhancedConversationState:
        """Confirm booking details with enhanced information"""
        extracted_info = state["extracted_info"]
        selected_time = state.get("selected_slot") or extracted_info.get("time")
        
        try:
            date_obj = datetime.strptime(extracted_info.get('date', ''), '%Y-%m-%d')
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
            
            # Convert time to 12-hour format for display
            time_obj = datetime.strptime(selected_time, '%H:%M')
            formatted_time = time_obj.strftime('%I:%M %p')
            
        except:
            formatted_date = extracted_info.get('date', 'Not set')
            formatted_time = selected_time or 'Not set'
        
        # Get meeting type and duration from context or defaults
        meeting_type = extracted_info.get('meeting_type', 'Meeting')
        duration = extracted_info.get('duration', 60)
        
        response = f"""
Perfect! Let me confirm your appointment details:

📅 **Booking Confirmation**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        response += f"""
• **Meeting Type:** {meeting_type}
• **Duration:** {duration} minutes
• **Date:** {formatted_date}
• **Time:** {formatted_time}

Is this correct?
"""
        
        state["messages"].append({"role": "assistant", "content": response})
        state["current_step"] = "awaiting_confirmation"
        
        return state
    
    def _create_booking(self, state: EnhancedConversationState) -> EnhancedConversationState:
        """Create the booking in the calendar"""
        extracted_info = state["extracted_info"]
        selected_time = state.get("selected_slot") or extracted_info.get("time")
        date = extracted_info.get("date")
        
        try:
            # Import here to avoid circular imports
            from backend.enhanced_calendar import get_enhanced_calendar_manager
            calendar_manager = get_enhanced_calendar_manager()
            
            # Create the event
            event_id = calendar_manager.create_event(date, selected_time)
            
            response = f"""
🎉 Great! Your booking has been created successfully!

📅 **Event Details**
• **Date:** {date}
• **Time:** {selected_time}
• **Event ID:** {event_id}

You're all set!
"""
            state["booking_confirmed"] = True
            state["current_step"] = "booking_created"
            
        except Exception as e:
            print(f"❌ Error creating booking: {e}")
            response = "❌ There was an error creating your booking. Please try again later."
            state["current_step"] = "booking_error"
        
        state["messages"].append({"role": "assistant", "content": response})
        return state
    
    def _handle_modification(self, state: EnhancedConversationState) -> EnhancedConversationState:
        """Handle booking modification requests"""
        # Placeholder logic
        response = "🛠️ Okay, let's modify your booking. What changes would you like to make?"
        state["messages"].append({"role": "assistant", "content": response})
        state["current_step"] = "awaiting_modification_details"
        return state
    
    def _handle_cancellation(self, state: EnhancedConversationState) -> EnhancedConversationState:
        """Handle booking cancellation requests"""
        # Placeholder logic
        response = "❌ Sure, let's cancel your booking. Can you please confirm the date and time of the booking you want to cancel?"
        state["messages"].append({"role": "assistant", "content": response})
        state["current_step"] = "awaiting_cancellation_confirmation"
        return state
    
    def _provide_help(self, state: EnhancedConversationState) -> EnhancedConversationState:
        """Provide help and guidance to the user"""
        help_message = """
✨ **Available Commands:**
• **Book a meeting:** "Book a meeting tomorrow at 2 PM"
• **Modify a booking:** "Change my booking to next Monday"
• **Cancel a booking:** "Cancel my appointment for Friday"
• **Check availability:** "What slots are available this week?"
• **Help:** "Help" or "How do I book a meeting?"

I'm here to assist you with scheduling and managing your appointments. Just let me know what you need!
"""
        state["messages"].append({"role": "assistant", "content": help_message})
        state["current_step"] = "help_provided"
        return state
    
    def _general_response(self, state: EnhancedConversationState) -> EnhancedConversationState:
        """Provide a general response using the LLM"""
        last_message = state["messages"][-1]["content"]
        
        try:
            # Use LLM to generate a response
            messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in state["messages"]
            ]
            messages.append({"role": "user", "content": last_message})
            
            llm_response = self.llm.invoke(messages)
            response = llm_response.content
            
            state["messages"].append({"role": "assistant", "content": response})
            state["current_step"] = "general_response_provided"
            
        except Exception as e:
            print(f"❌ Error generating general response: {e}")
            response = "I'm sorry, I didn't understand that. Can you please rephrase your question?"
            state["messages"].append({"role": "assistant", "content": response})
            state["current_step"] = "general_response_error"
        
        return state
    
    def _route_after_intent(self, state: EnhancedConversationState) -> str:
        """Route the conversation flow based on the detected intent"""
        intent = state["user_intent"]
        
        if intent == "booking_request":
            return "extract_datetime"
        elif intent == "modify_booking":
            return "handle_modification"
        elif intent == "cancel_booking":
            return "handle_cancellation"
        elif intent == "help":
            return "provide_help"
        else:
            return "general_response"
    
    def _route_after_validation(self, state: EnhancedConversationState) -> str:
        """Route after datetime validation"""
        if state["extracted_info"].get("validation_issues"):
            return "suggest_alternatives"
        else:
            return "check_availability"
    
    def _route_after_availability(self, state: EnhancedConversationState) -> str:
        """Route after checking availability"""
        if state["current_step"] == "slot_available":
            return "confirm_booking"
        elif state["current_step"] == "slot_unavailable" or state["current_step"] == "showing_options":
            return "suggest_alternatives"
        else:
            return "continue"
    
    def _generate_fallback_response(self, message: str) -> str:
        """Generate a fallback response when something goes wrong"""
        return f"I'm having trouble processing your request: '{message}'. Please try again or contact support."

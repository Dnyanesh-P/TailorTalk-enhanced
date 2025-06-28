from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
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

class BookingAgent:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("❌ OpenAI API key not found in environment variables")
        
        # Get timezone
        self.timezone_str = os.getenv('TIMEZONE', 'Asia/Kolkata')
        self.timezone = pytz.timezone(self.timezone_str)
        
        print(f"🤖 Initializing BookingAgent with timezone: {self.timezone_str}")
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            api_key=api_key
        )
        self.graph = self._create_graph()
        print("✅ BookingAgent initialized successfully!")
    
    def _create_graph(self):
        """Create the LangGraph workflow"""
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("understand_intent", self._understand_intent)
        workflow.add_node("extract_info", self._extract_booking_info)
        workflow.add_node("check_availability", self._check_availability)
        workflow.add_node("suggest_slots", self._suggest_slots)
        workflow.add_node("confirm_booking", self._confirm_booking)
        workflow.add_node("book_appointment", self._book_appointment)
        workflow.add_node("general_response", self._general_response)
        
        # Set entry point
        workflow.set_entry_point("understand_intent")
        
        # Add edges
        workflow.add_conditional_edges(
            "understand_intent",
            self._route_after_intent,
            {
                "extract_info": "extract_info",
                "general_response": "general_response",
            }
        )
        
        workflow.add_edge("extract_info", "check_availability")
        workflow.add_edge("check_availability", "suggest_slots")
        workflow.add_conditional_edges(
            "suggest_slots",
            self._route_after_suggestion,
            {
                "confirm": "confirm_booking",
                "continue": END,
            }
        )
        workflow.add_edge("confirm_booking", "book_appointment")
        workflow.add_edge("book_appointment", END)
        workflow.add_edge("general_response", END)
        
        return workflow.compile()
    
    def _understand_intent(self, state: ConversationState) -> ConversationState:
        """Understand user intent from the message"""
        last_message = state["messages"][-1]["content"].lower()
        
        # Direct keyword matching for better intent detection
        booking_keywords = ["book", "schedule", "appointment", "meeting", "call", "tomorrow", "next week", "3pm", "afternoon", "morning"]
        confirmation_keywords = ["yes", "confirm", "book it", "that works", "sounds good", "perfect"]
        
        if any(keyword in last_message for keyword in confirmation_keywords):
            intent = "confirmation"
        elif any(keyword in last_message for keyword in booking_keywords):
            intent = "booking_request"
        elif "availability" in last_message or "free time" in last_message or "available" in last_message:
            intent = "availability_check"
        else:
            intent = "general_question"
        
        print(f"🎯 Detected intent: {intent} from message: {last_message}")
        state["user_intent"] = intent
        state["current_step"] = "intent_understood"
        return state
    
    def _extract_booking_info(self, state: ConversationState) -> ConversationState:
        """Extract booking information from user message"""
        last_message = state["messages"][-1]["content"]
        
        now_ist = datetime.now(self.timezone)
        today = now_ist.date()
        tomorrow = today + timedelta(days=1)
        
        prompt = f"""
        Current date and time in India: {now_ist.strftime('%Y-%m-%d %H:%M %Z')} ({now_ist.strftime('%A')})
        Tomorrow will be: {tomorrow.strftime('%Y-%m-%d')} ({tomorrow.strftime('%A')})
        
        Extract booking information from: "{last_message}"
        
        Rules:
        - If user says "tomorrow", use {tomorrow.strftime('%Y-%m-%d')}
        - If user says "today", use {today.strftime('%Y-%m-%d')}
        - Convert relative times like "afternoon" to specific hours (14:00-17:00 range)
        - Convert "morning" to 09:00-12:00 range
        - Convert "evening" to 17:00-20:00 range
        - If user mentions a specific time like "3pm" or "15:00", use that
        
        Return JSON:
        {{
            "date": "YYYY-MM-DD or null",
            "time": "HH:MM or null", 
            "duration": "minutes or 60",
            "meeting_type": "type or Meeting"
        }}
        
        Examples:
        - "book tomorrow afternoon" → {{"date": "{tomorrow.strftime('%Y-%m-%d')}", "time": "15:00", "duration": 60, "meeting_type": "Meeting"}}
        - "schedule call at 3pm tomorrow" → {{"date": "{tomorrow.strftime('%Y-%m-%d')}", "time": "15:00", "duration": 60, "meeting_type": "Call"}}
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            # Clean the response to extract JSON
            content = response.content.strip()
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
            
            extracted_info = json.loads(content)
            state["extracted_info"].update(extracted_info)
            print(f"📋 Extracted info: {extracted_info}")
        except Exception as e:
            print(f"❌ Error extracting info: {e}")
            # Fallback extraction
            state["extracted_info"] = {
                "date": tomorrow.strftime('%Y-%m-%d') if "tomorrow" in last_message.lower() else None,
                "time": "15:00" if "afternoon" in last_message.lower() else None,
                "duration": 60,
                "meeting_type": "Meeting"
            }
        
        state["current_step"] = "info_extracted"
        return state
    
    def _check_availability(self, state: ConversationState) -> ConversationState:
        """Check calendar availability"""
        try:
            calendar_manager = get_calendar_manager()
            extracted_info = state["extracted_info"]
            
            if "date" in extracted_info and extracted_info["date"]:
                date_to_check = extracted_info["date"]
            else:
                # Default to tomorrow
                today = datetime.now(self.timezone).date()
                date_to_check = (today + timedelta(days=1)).strftime('%Y-%m-%d')
                state["extracted_info"]["date"] = date_to_check
            
            print(f"🔍 Checking availability for: {date_to_check}")
            available_slots = calendar_manager.get_availability(date_to_check)
            state["available_slots"] = available_slots
            
        except Exception as e:
            print(f"❌ Error checking availability: {e}")
            # Fallback slots
            state["available_slots"] = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
        
        state["current_step"] = "availability_checked"
        return state
    
    def _suggest_slots(self, state: ConversationState) -> ConversationState:
        """Suggest available time slots"""
        available_slots = state["available_slots"]
        date = state["extracted_info"].get("date", "")
        requested_time = state["extracted_info"].get("time")
        
        # Parse date for better formatting
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
        except:
            formatted_date = date
        
        if available_slots:
            # If user requested a specific time, check if it's available
            if requested_time and requested_time in available_slots:
                response = f"Great! {requested_time} on {formatted_date} is available. Shall I book this appointment for you?"
                state["selected_slot"] = requested_time
                state["extracted_info"]["time"] = requested_time
            else:
                # Show available slots
                if len(available_slots) > 5:
                    slots_text = ", ".join(available_slots[:5]) + f" (and {len(available_slots)-5} more)"
                else:
                    slots_text = ", ".join(available_slots)
                
                if requested_time:
                    response = f"Sorry, {requested_time} is not available on {formatted_date}. Here are the available slots: {slots_text}. Which time works for you? (All times in IST)"
                else:
                    response = f"I found these available slots on {formatted_date}: {slots_text}. Which time works for you? (All times in IST)"
        else:
            response = f"No available slots found for {formatted_date}. Would you like to try a different date?"
        
        state["messages"].append({"role": "assistant", "content": response})
        return state
    
    def _confirm_booking(self, state: ConversationState) -> ConversationState:
        """Confirm booking details"""
        extracted_info = state["extracted_info"]
        
        # Parse date for better formatting
        try:
            date_obj = datetime.strptime(extracted_info.get('date', ''), '%Y-%m-%d')
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
        except:
            formatted_date = extracted_info.get('date', 'Not set')
        
        response = f"""
Perfect! Let me confirm your appointment details:

📅 **Date:** {formatted_date}
🕐 **Time:** {extracted_info.get('time', 'Not set')} IST
⏱️ **Duration:** {extracted_info.get('duration', 60)} minutes
📝 **Type:** {extracted_info.get('meeting_type', 'Meeting')}

Shall I go ahead and book this appointment for you?
        """
        state["messages"].append({"role": "assistant", "content": response})
        return state
    
    def _book_appointment(self, state: ConversationState) -> ConversationState:
        """Book the appointment"""
        try:
            calendar_manager = get_calendar_manager()
            extracted_info = state["extracted_info"]
            
            date_str = extracted_info["date"]
            time_str = extracted_info["time"]
            datetime_str = f"{date_str} {time_str}"
            
            booking_datetime_naive = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
            booking_datetime = self.timezone.localize(booking_datetime_naive)
            
            # Parse date for better formatting
            formatted_date = booking_datetime.strftime('%A, %B %d, %Y')
            formatted_time = booking_datetime.strftime('%I:%M %p')
            
            event_id = calendar_manager.create_event(
                title=extracted_info.get("meeting_type", "Meeting"),
                start_datetime=booking_datetime,
                duration_minutes=extracted_info.get("duration", 60),
                description="Booked via TailorTalk AI Assistant"
            )
            
            response = f"""
✅ **Appointment Successfully Booked!**

📅 **Date:** {formatted_date}
🕐 **Time:** {formatted_time} IST
⏱️ **Duration:** {extracted_info.get('duration', 60)} minutes
🆔 **Event ID:** {event_id}

Your appointment has been added to your Google Calendar. You should receive a calendar notification before the meeting.

Is there anything else I can help you with?
            """
            state["booking_confirmed"] = True
            
        except Exception as e:
            print(f"❌ Booking error: {e}")
            response = f"❌ I encountered an error while booking your appointment: {str(e)}. Please try again or contact support."
        
        state["messages"].append({"role": "assistant", "content": response})
        return state
    
    def _general_response(self, state: ConversationState) -> ConversationState:
        """Handle general conversation"""
        last_message = state["messages"][-1]["content"].lower()
        now_ist = datetime.now(self.timezone)
        current_time = now_ist.strftime('%I:%M %p IST on %A, %B %d, %Y')
        
        # Check for greetings
        if any(greeting in last_message for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
            response = f"""
Hello! 👋 I'm your TailorTalk AI booking assistant.

**Current time:** {current_time}

I can help you with:
📅 **Schedule appointments** - "Book a meeting for tomorrow afternoon"
🔍 **Check availability** - "Do you have any free time this Friday?"
📞 **Manage your calendar** - Real-time Google Calendar integration

**Quick examples to try:**
• "I want to schedule a call for tomorrow at 3 PM"
• "Book a meeting for next Monday morning"
• "Do you have any free slots this week?"

What would you like to schedule today?
            """
        else:
            response = f"""
I'm your AI booking assistant, and I'm here to help you manage your appointments!

**Current time:** {current_time}

I specialize in:
✨ **Smart scheduling** with natural language
📅 **Real-time calendar access** via Google Calendar
🤖 **Intelligent availability checking**

Try saying something like:
• "Book a call for tomorrow afternoon"
• "Schedule a meeting for next week"
• "Check my availability for Friday"

How can I help you today?
            """
        
        state["messages"].append({"role": "assistant", "content": response})
        return state
    
    def _route_after_intent(self, state: ConversationState) -> str:
        """Route based on intent"""
        intent = state["user_intent"]
        print(f"🔀 Routing intent: {intent}")
        if intent in ["booking_request", "availability_check", "confirmation", "time_selection"]:
            return "extract_info"
        return "general_response"
    
    def _route_after_suggestion(self, state: ConversationState) -> str:
        """Route after suggesting slots"""
        # For now, always continue to end
        # In a more complex implementation, you could check if user selected a time
        return "continue"
    
    async def process_message(self, message: str, user_id: str = "default") -> str:
        """Process a user message"""
        initial_state = {
            "messages": [{"role": "user", "content": message}],
            "user_intent": None,
            "extracted_info": {},
            "current_step": "start",
            "available_slots": [],
            "selected_slot": None,
            "booking_confirmed": False
        }
        
        try:
            print(f"🔄 Processing message: {message}")
            result = self.graph.invoke(initial_state)
            
            # Get the last assistant message
            assistant_messages = [msg for msg in result["messages"] if msg["role"] == "assistant"]
            if assistant_messages:
                final_response = assistant_messages[-1]["content"]
                print(f"✅ Generated response: {final_response[:100]}...")
                return final_response
            else:
                return "I'm here to help you book appointments. What would you like to schedule?"
                
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            return f"I apologize, but I encountered an error while processing your request. Please try again. Error: {str(e)}"

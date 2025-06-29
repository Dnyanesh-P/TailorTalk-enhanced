"""
Debug script to test Google Calendar integration
"""

import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

load_dotenv()

def test_calendar_integration():
    """Test the calendar integration with detailed debugging"""
    print("🔍 Testing Google Calendar Integration")
    print("=" * 50)
    
    try:
        from backend.google_calendar import get_calendar_manager
        
        calendar_manager = get_calendar_manager()
        print("✅ Calendar manager initialized")
        
        # Test today's availability
        timezone = pytz.timezone(os.getenv('TIMEZONE', 'Asia/Kolkata'))
        today = datetime.now(timezone).date().strftime('%Y-%m-%d')
        tomorrow = (datetime.now(timezone) + timedelta(days=1)).date().strftime('%Y-%m-%d')
        
        print(f"\n📅 Testing availability for today ({today}):")
        today_slots = calendar_manager.get_availability(today)
        print(f"Available slots: {today_slots}")
        
        print(f"\n📅 Testing availability for tomorrow ({tomorrow}):")
        tomorrow_slots = calendar_manager.get_availability(tomorrow)
        print(f"Available slots: {tomorrow_slots}")
        
        # Test direct calendar access
        print(f"\n🔍 Testing direct calendar access:")
        target_date = datetime.strptime(today, '%Y-%m-%d')
        start_time = timezone.localize(target_date.replace(hour=0, minute=0, second=0))
        end_time = timezone.localize(target_date.replace(hour=23, minute=59, second=59))
        
        events_result = calendar_manager.service.events().list(
            calendarId=os.getenv('CALENDAR_ID', 'primary'),
            timeMin=start_time.isoformat(),
            timeMax=end_time.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        print(f"📋 Found {len(events)} events for {today}:")
        
        for event in events:
            title = event.get('summary', 'No title')
            if 'start' in event:
                if 'dateTime' in event['start']:
                    start_dt = event['start']['dateTime']
                    print(f"   📝 {title} at {start_dt}")
                elif 'date' in event['start']:
                    start_date = event['start']['date']
                    print(f"   📅 {title} on {start_date} (all-day)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing calendar: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_agent():
    """Test the AI agent"""
    print("\n🤖 Testing AI Agent")
    print("=" * 30)
    
    try:
        from backend.langgraph_agent import BookingAgent
        
        agent = BookingAgent()
        print("✅ AI Agent initialized")
        
        # Test message processing
        test_messages = [
            "Hello",
            "I want to book a call for tomorrow afternoon",
            "Schedule a meeting for 3 PM tomorrow"
        ]
        
        for message in test_messages:
            print(f"\n📨 Testing message: '{message}'")
            try:
                import asyncio
                response = asyncio.run(agent.process_message(message))
                print(f"🤖 Response: {response[:100]}...")
            except Exception as e:
                print(f"❌ Error processing message: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing AI agent: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 TailorTalk Debug Script")
    print("=" * 60)
    
    calendar_ok = test_calendar_integration()
    ai_ok = test_ai_agent()
    
    print(f"\n📊 RESULTS:")
    print(f"📅 Calendar Integration: {'✅ Working' if calendar_ok else '❌ Failed'}")
    print(f"🤖 AI Agent: {'✅ Working' if ai_ok else '❌ Failed'}")
    
    if calendar_ok and ai_ok:
        print("\n🎉 All systems working! Your app should function correctly.")
    else:
        print("\n⚠️ Some issues detected. Check the error messages above.")

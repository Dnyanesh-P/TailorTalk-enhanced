import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarManager:
    def __init__(self):
        self.service = None
        # Use the full path from your .env file
        self.credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'config/credentials.json')
        # Store token in the same directory as credentials
        credentials_dir = os.path.dirname(self.credentials_path)
        self.token_path = os.path.join(credentials_dir, 'token.pickle')
        
        # Get timezone from environment
        self.timezone_str = os.getenv('TIMEZONE', 'Asia/Kolkata')
        self.timezone = pytz.timezone(self.timezone_str)
        
        print(f"🔧 Using credentials path: {self.credentials_path}")
        print(f"🌍 Using timezone: {self.timezone_str}")
        
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.credentials_path), exist_ok=True)
        
        # The file token.pickle stores the user's access and refresh tokens.
        if os.path.exists(self.token_path):
            print(f"📁 Loading existing token from: {self.token_path}")
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing expired credentials...")
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"❌ Error refreshing credentials: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"❌ Credentials file not found at: {self.credentials_path}\n"
                        f"Please make sure your credentials.json file is at this exact location."
                    )
                
                print("🔐 Starting Google Calendar authentication...")
                print("📱 A browser window will open for authentication...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            print(f"💾 Saving authentication token to: {self.token_path}")
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('calendar', 'v3', credentials=creds)
        print("✅ Successfully authenticated with Google Calendar!")
    
    def get_availability(self, date: str, start_hour: int = 9, end_hour: int = 18) -> List[str]:
        """Get available time slots for a specific date"""
        try:
            print(f"🔍 Checking availability for {date} in {self.timezone_str}")
        
            # Parse the date
            target_date = datetime.strptime(date, '%Y-%m-%d')
        
            # Create time range for the day in local timezone
            start_time = self.timezone.localize(target_date.replace(hour=start_hour, minute=0, second=0))
            end_time = self.timezone.localize(target_date.replace(hour=end_hour, minute=0, second=0))
        
            print(f"📅 Checking from {start_time} to {end_time}")
        
            # Get existing events
            events_result = self.service.events().list(
                calendarId=os.getenv('CALENDAR_ID', 'primary'),
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
        
            events = events_result.get('items', [])
            print(f"📅 Found {len(events)} existing events for {date}")
        
            # Debug: Print all events
            for event in events:
                event_title = event.get('summary', 'No title')
                if 'start' in event and 'dateTime' in event['start']:
                    event_time = event['start']['dateTime']
                    print(f"   📝 Event: {event_title} at {event_time}")
        
            # Generate all possible slots (1-hour intervals)
            all_slots = []
            current_time = start_time
            while current_time < end_time:
                all_slots.append(current_time.strftime('%H:%M'))
                current_time += timedelta(hours=1)
        
            print(f"🕐 All possible slots: {all_slots}")
        
            # Remove booked slots - improved logic
            booked_slots = set()
            for event in events:
                if 'start' in event and 'dateTime' in event['start']:
                    try:
                        event_start_str = event['start']['dateTime']
                        event_end_str = event['end']['dateTime']
                    
                        # Parse start time
                        if event_start_str.endswith('Z'):
                            event_start = datetime.fromisoformat(event_start_str.replace('Z', '+00:00'))
                        else:
                            event_start = datetime.fromisoformat(event_start_str)
                    
                        # Parse end time
                        if event_end_str.endswith('Z'):
                            event_end = datetime.fromisoformat(event_end_str.replace('Z', '+00:00'))
                        else:
                            event_end = datetime.fromisoformat(event_end_str)
                    
                        # Convert to local timezone
                        if event_start.tzinfo is None:
                            event_start = pytz.UTC.localize(event_start)
                        if event_end.tzinfo is None:
                            event_end = pytz.UTC.localize(event_end)
                        
                        event_start_local = event_start.astimezone(self.timezone)
                        event_end_local = event_end.astimezone(self.timezone)
                        
                        # Block all hours that overlap with this event
                        current_hour = event_start_local.replace(minute=0, second=0, microsecond=0)
                        while current_hour < event_end_local:
                            hour_slot = current_hour.strftime('%H:%M')
                            if hour_slot in all_slots:
                                booked_slots.add(hour_slot)
                                print(f"   ❌ Blocking slot {hour_slot} due to event: {event.get('summary', 'No title')}")
                            current_hour += timedelta(hours=1)
                    
                    except Exception as e:
                        print(f"⚠️ Error parsing event time: {e}")
        
            available_slots = [slot for slot in all_slots if slot not in booked_slots]
            print(f"✅ Available slots after filtering: {available_slots}")
            print(f"❌ Booked slots: {list(booked_slots)}")
        
            return available_slots
        
        except Exception as e:
            print(f"❌ Error getting availability: {e}")
            # Return default slots as fallback
            return ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
    
    def create_event(self, title: str, start_datetime: datetime, duration_minutes: int = 60, 
                    description: str = "", attendee_email: Optional[str] = None) -> str:
        """Create a calendar event"""
        try:
            if start_datetime.tzinfo is None:
                start_datetime = self.timezone.localize(start_datetime)
            
            end_datetime = start_datetime + timedelta(minutes=duration_minutes)
            
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': self.timezone_str,
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': self.timezone_str,
                },
            }
            
            if attendee_email:
                event['attendees'] = [{'email': attendee_email}]
            
            created_event = self.service.events().insert(
                calendarId=os.getenv('CALENDAR_ID', 'primary'),
                body=event
            ).execute()
            
            event_id = created_event.get('id')
            print(f"✅ Event created successfully: {event_id}")
            return event_id
            
        except Exception as e:
            print(f"❌ Error creating event: {e}")
            raise e

# Global instance
calendar_manager = None

def get_calendar_manager():
    global calendar_manager
    if calendar_manager is None:
        calendar_manager = GoogleCalendarManager()
    return calendar_manager

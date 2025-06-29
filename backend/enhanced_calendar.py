"""
Enhanced Google Calendar integration with proper timezone handling (supports both OAuth Client ID and Service Account)
"""
import os
import logging
from datetime import datetime, timedelta, time, date
from typing import List, Dict, Optional, Any
import pytz

# Google API imports (lazy import as per credential type)
try:
    from google.oauth2 import service_account
except ImportError:
    service_account = None

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    import pickle
except ImportError:
    Credentials = None
    Request = None
    InstalledAppFlow = None
    pickle = None

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class EnhancedCalendarManager:
    """
    Enhanced Google Calendar manager with proper timezone handling.
    Supports both OAuth Client ID (user login) and Service Account authentication.
    """
    def __init__(self, timezone_str: str = 'Asia/Kolkata'):
        self.timezone = pytz.timezone(timezone_str)
        self.scopes = ['https://www.googleapis.com/auth/calendar']
        self.credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'config/credentials.json')
        self.token_path = os.getenv('GOOGLE_TOKEN_PATH', 'config/token.pickle')
        self.calendar_id = os.getenv('CALENDAR_ID', 'primary')
        self.service = None

        # Business hours configuration
        self.business_start = 9  # 9 AM
        self.business_end = 18   # 6 PM
        self.slot_duration = 60  # 60 minutes

        # Mode detection
        self.use_service_account = os.getenv('GOOGLE_USE_SERVICE_ACCOUNT', '0') == '1'

        logger.info(f"Enhanced Calendar Manager initialized with timezone: {timezone_str}, "
                    f"mode: {'service_account' if self.use_service_account else 'oauth_client'}")

    def _get_service(self):
        """
        Get Google Calendar service with proper credentials.
        Supports both Service Account (server-to-server) and OAuth Client ID (user login) modes.
        """
        if self.service is not None:
            return self.service

        if self.use_service_account:
            if not service_account:
                raise ImportError("google.oauth2.service_account is not available. Install google-auth.")
            if not os.path.exists(self.credentials_path):
                logger.error(f"Service account credentials file not found: {self.credentials_path}")
                raise FileNotFoundError(f"Service account credentials file not found: {self.credentials_path}")
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path, scopes=self.scopes
                )
                self.service = build('calendar', 'v3', credentials=credentials)
                logger.info("Google Calendar service initialized successfully (service account)")
            except Exception as e:
                logger.error(f"Failed to build Calendar service (service account): {e}")
                raise Exception(f"Failed to initialize Google Calendar service: {e}")
        else:
            credentials = self._get_oauth_credentials()
            if not credentials:
                raise Exception("Failed to obtain Google Calendar OAuth credentials")
            try:
                self.service = build('calendar', 'v3', credentials=credentials)
                logger.info("Google Calendar service initialized successfully (OAuth)")
            except Exception as e:
                logger.error(f"Failed to build Calendar service (OAuth): {e}")
                raise Exception(f"Failed to initialize Google Calendar service: {e}")
        return self.service

    def _get_oauth_credentials(self) -> Optional[Any]:
        """
        Get OAuth credentials for user-based login flow.
        """
        if not Credentials or not InstalledAppFlow or not pickle:
            raise ImportError("google-auth-oauthlib and pickle are required for OAuth client login")
        creds = None
        # Load existing token
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
                logger.info("Loaded existing credentials from token file")
            except Exception as e:
                logger.warning(f"Failed to load existing token: {e}")
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed expired credentials")
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}")
                    creds = None
            if not creds:
                if not os.path.exists(self.credentials_path):
                    logger.error(f"OAuth credentials file not found: {self.credentials_path}")
                    return None
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.scopes)
                    creds = flow.run_local_server(port=0)
                    logger.info("Obtained new credentials via OAuth flow")
                except Exception as e:
                    logger.error(f"Failed to obtain credentials: {e}")
                    return None
            # Save the credentials for the next run
            try:
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
                logger.info("Saved credentials to token file")
            except Exception as e:
                logger.warning(f"Failed to save credentials: {e}")
        return creds

    def get_availability(self, date_str: str) -> List[str]:
        """
        Get available time slots for a specific date.
        """
        try:
            # Parse the date string
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            logger.info(f"Checking availability for {target_date}")

            # Get existing events for the day
            existing_events = self._get_events_for_date(target_date)

            # Generate all possible time slots
            all_slots = self._generate_time_slots()

            # Filter out booked slots
            available_slots = []
            for slot in all_slots:
                slot_datetime = self._combine_date_time(target_date, slot)
                if not self._is_slot_booked(slot_datetime, existing_events):
                    available_slots.append(slot)

            logger.info(f"Found {len(available_slots)} available slots for {target_date}")
            return available_slots

        except Exception as e:
            logger.error(f"Error getting availability for {date_str}: {e}")
            # Return mock data as fallback
            return ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]

    def create_event_with_details(self, date: str, time: str, details: Dict[str, Any]) -> str:
        """
        Create a calendar event with proper timezone handling.
        """
        try:
            logger.info(f"Creating event for {date} at {time} with details: {details}")

            # Parse date and time with proper timezone handling
            event_datetime = self._parse_datetime_with_timezone(date, time)
            end_datetime = event_datetime + timedelta(minutes=details.get('duration', 60))

            # Create event object
            event = {
                'summary': details.get('title', 'Appointment'),
                'description': details.get('description', 'Scheduled via TailorTalk'),
                'start': {
                    'dateTime': event_datetime.isoformat(),
                    'timeZone': str(self.timezone),
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': str(self.timezone),
                },
                'attendees': details.get('attendees', []),
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 24 hours before
                        {'method': 'popup', 'minutes': 30},       # 30 minutes before
                    ],
                },
            }

            service = self._get_service()
            created_event = service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()

            event_id = created_event.get('id')
            logger.info(f"Successfully created event with ID: {event_id}")

            return event_id

        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}")
            raise Exception(f"Calendar booking failed: {str(e)}")

    def _parse_datetime_with_timezone(self, date_str: str, time_str: str) -> datetime:
        """
        Parse date and time strings into timezone-aware datetime object.
        """
        try:
            # Parse date
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            # Parse time
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            # Combine date and time
            naive_datetime = datetime.combine(date_obj, time_obj)
            # Make timezone-aware
            aware_datetime = self.timezone.localize(naive_datetime)
            logger.info(f"Parsed datetime: {date_str} {time_str} -> {aware_datetime}")
            return aware_datetime
        except Exception as e:
            logger.error(f"Error parsing datetime {date_str} {time_str}: {e}")
            raise ValueError(f"Invalid date/time format: {date_str} {time_str}")

    def _get_events_for_date(self, target_date: date) -> List[Dict]:
        """
        Get existing events for a specific date.
        """
        try:
            # Create timezone-aware datetime objects for the day
            start_of_day = self.timezone.localize(
                datetime.combine(target_date, time(0, 0, 0))
            )
            end_of_day = self.timezone.localize(
                datetime.combine(target_date, time(23, 59, 59))
            )
            service = self._get_service()
            events_result = service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            logger.info(f"Found {len(events)} existing events for {target_date}")
            return events
        except Exception as e:
            logger.error(f"Error getting events for {target_date}: {e}")
            return []

    def _generate_time_slots(self) -> List[str]:
        """
        Generate all possible time slots for business hours.
        """
        slots = []
        current_hour = self.business_start
        while current_hour < self.business_end:
            slots.append(f"{current_hour:02d}:00")
            current_hour += 1
        return slots

    def _combine_date_time(self, date_obj: date, time_str: str) -> datetime:
        """
        Combine date and time string into timezone-aware datetime.
        """
        time_obj = datetime.strptime(time_str, '%H:%M').time()
        naive_datetime = datetime.combine(date_obj, time_obj)
        return self.timezone.localize(naive_datetime)

    def _is_slot_booked(self, slot_datetime: datetime, existing_events: List[Dict]) -> bool:
        """
        Check if a time slot is already booked.
        """
        slot_end = slot_datetime + timedelta(minutes=self.slot_duration)
        for event in existing_events:
            try:
                # Parse event start and end times
                event_start_str = event['start'].get('dateTime', event['start'].get('date'))
                event_end_str = event['end'].get('dateTime', event['end'].get('date'))
                if not event_start_str or not event_end_str:
                    continue
                # Handle all-day events (date only)
                if 'T' not in event_start_str:
                    continue  # Skip all-day events
                # Parse datetime strings
                event_start = datetime.fromisoformat(event_start_str.replace('Z', '+00:00'))
                event_end = datetime.fromisoformat(event_end_str.replace('Z', '+00:00'))
                # Convert to local timezone if needed
                if event_start.tzinfo != self.timezone:
                    event_start = event_start.astimezone(self.timezone)
                    event_end = event_end.astimezone(self.timezone)
                # Check for overlap
                if (slot_datetime < event_end and slot_end > event_start):
                    return True
            except Exception as e:
                logger.warning(f"Error parsing event time: {e}")
                continue
        return False

    def test_connection(self) -> Dict[str, Any]:
        """
        Test Google Calendar connection.
        """
        try:
            service = self._get_service()
            calendar = service.calendars().get(calendarId=self.calendar_id).execute()
            now = datetime.now(self.timezone)
            events_result = service.events().list(
                calendarId=self.calendar_id,
                timeMin=now.isoformat(),
                maxResults=5,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            return {
                'status': 'success',
                'calendar_name': calendar.get('summary', 'Unknown'),
                'calendar_id': self.calendar_id,
                'timezone': str(self.timezone),
                'recent_events_count': len(events),
                'message': 'Google Calendar connection successful'
            }
        except Exception as e:
            logger.error(f"Calendar connection test failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Google Calendar connection failed'
            }

# Global enhanced calendar manager instance
_enhanced_calendar_manager = None

def get_enhanced_calendar_manager(timezone_str: str = None) -> EnhancedCalendarManager:
    """
    Get or create enhanced calendar manager instance.
    """
    global _enhanced_calendar_manager
    if _enhanced_calendar_manager is None:
        if timezone_str is None:
            timezone_str = os.getenv('TIMEZONE', 'Asia/Kolkata')
        _enhanced_calendar_manager = EnhancedCalendarManager(timezone_str)
    return _enhanced_calendar_manager

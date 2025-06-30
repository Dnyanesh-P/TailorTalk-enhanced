"""
Enhanced Google Calendar integration with service account authentication
Adapted for Render deployment using GOOGLE_CREDENTIALS_JSON environment variable
"""
import os
import json
import logging
from datetime import datetime, timedelta, time, date
from typing import List, Dict, Optional, Any
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class EnhancedCalendarManager:
    """Enhanced Google Calendar manager with service account authentication"""

    def __init__(self, timezone_str: str = 'Asia/Kolkata'):
        self.timezone = pytz.timezone(timezone_str)
        self.scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events'
        ]
        self.credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        self.calendar_id = os.getenv('CALENDAR_ID', 'primary')
        self.service = None
        self.business_start = 9
        self.business_end = 18
        self.slot_duration = 60

        logger.info(f"Enhanced Calendar Manager initialized with service account auth")
        logger.info(f"Timezone: {timezone_str}")
        logger.info(f"Calendar ID: {self.calendar_id}")

    def _get_service_account_credentials(self) -> Optional[service_account.Credentials]:
        try:
            if not self.credentials_json:
                logger.error("GOOGLE_CREDENTIALS_JSON environment variable not found")
                return None

            try:
                credentials_info = json.loads(self.credentials_json)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in GOOGLE_CREDENTIALS_JSON: {e}")
                return None

            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=self.scopes
            )

            logger.info("✅ Service account credentials loaded successfully")
            logger.info(f"Service account email: {credentials_info.get('client_email', 'Unknown')}")

            return credentials

        except Exception as e:
            logger.error(f"Failed to load service account credentials: {e}")
            return None

    def _get_service(self):
        if self.service is None:
            credentials = self._get_service_account_credentials()
            if not credentials:
                raise Exception("Failed to obtain service account credentials")

            try:
                self.service = build('calendar', 'v3', credentials=credentials)
                logger.info("✅ Google Calendar service initialized with service account")
            except Exception as e:
                logger.error(f"Failed to build Calendar service: {e}")
                raise Exception(f"Failed to initialize Google Calendar service: {e}")

        return self.service

    def create_event_with_details(self, date: str, time: str, details: Dict[str, Any]) -> str:
        try:
            logger.info(f"Attempting to create event: {date} {time} {details}")

            event_datetime = self._parse_datetime_with_timezone(date, time)
            end_datetime = event_datetime + timedelta(minutes=details.get('duration', 60))

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
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
            }

            service = self._get_service()
            created_event = service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()

            logger.info(f"Google Calendar API response: {created_event}")
            event_id = created_event.get('id')
            logger.info(f"✅ Successfully created event with ID: {event_id}")

            return event_id

        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}", exc_info=True)
            raise Exception(f"Calendar booking failed: {str(e)}")

    # ... (rest of the class remains unchanged) ...

# Global instance
_enhanced_calendar_manager = None

def get_enhanced_calendar_manager(timezone_str: str = None) -> EnhancedCalendarManager:
    global _enhanced_calendar_manager

    if _enhanced_calendar_manager is None:
        if timezone_str is None:
            timezone_str = os.getenv('TIMEZONE', 'Asia/Kolkata')
        _enhanced_calendar_manager = EnhancedCalendarManager(timezone_str)

    return _enhanced_calendar_manager


def get_enhanced_calendar_manager(timezone_str: str = None) -> EnhancedCalendarManager:
    """Get or create enhanced calendar manager instance"""
    global _enhanced_calendar_manager
    
    if _enhanced_calendar_manager is None:
        if timezone_str is None:
            timezone_str = os.getenv('TIMEZONE', 'Asia/Kolkata')
        _enhanced_calendar_manager = EnhancedCalendarManager(timezone_str)
    
    return _enhanced_calendar_manager


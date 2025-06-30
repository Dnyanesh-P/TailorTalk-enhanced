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

    def get_availability(self, date_str: str) -> List[str]:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            logger.info(f"Checking availability for {target_date}")

            existing_events = self._get_events_for_date(target_date)

            all_slots = self._generate_time_slots()

            available_slots = []
            for slot in all_slots:
                slot_datetime = self._combine_date_time(target_date, slot)
                if not self._is_slot_booked(slot_datetime, existing_events):
                    available_slots.append(slot)

            logger.info(f"Found {len(available_slots)} available slots for {target_date}")
            return available_slots

        except Exception as e:
            logger.error(f"Error getting availability for {date_str}: {e}")
            return ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]

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

    def create_event(self, title: str, start_datetime: datetime, duration_minutes: int = 60, description: str = "") -> str:
        details = {
            'title': title,
            'description': description,
            'duration': duration_minutes
        }

        date_str = start_datetime.strftime('%Y-%m-%d')
        time_str = start_datetime.strftime('%H:%M')

        return self.create_event_with_details(date_str, time_str, details)

    def _parse_datetime_with_timezone(self, date_str: str, time_str: str) -> datetime:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            naive_datetime = datetime.combine(date_obj, time_obj)
            aware_datetime = self.timezone.localize(naive_datetime)

            logger.info(f"Parsed datetime: {date_str} {time_str} -> {aware_datetime}")
            return aware_datetime

        except Exception as e:
            logger.error(f"Error parsing datetime {date_str} {time_str}: {e}")
            raise ValueError(f"Invalid date/time format: {date_str} {time_str}")

    def _get_events_for_date(self, target_date: date) -> List[Dict]:
        try:
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
        slots = []
        current_hour = self.business_start

        while current_hour < self.business_end:
            slots.append(f"{current_hour:02d}:00")
            current_hour += 1

        return slots

    def _combine_date_time(self, date_obj: date, time_str: str) -> datetime:
        time_obj = datetime.strptime(time_str, '%H:%M').time()
        naive_datetime = datetime.combine(date_obj, time_obj)
        return self.timezone.localize(naive_datetime)

    def _is_slot_booked(self, slot_datetime: datetime, existing_events: List[Dict]) -> bool:
        slot_end = slot_datetime + timedelta(minutes=self.slot_duration)

        for event in existing_events:
            try:
                event_start_str = event['start'].get('dateTime', event['start'].get('date'))
                event_end_str = event['end'].get('dateTime', event['end'].get('date'))

                if not event_start_str or not event_end_str:
                    continue

                if 'T' not in event_start_str:
                    continue

                event_start = datetime.fromisoformat(event_start_str.replace('Z', '+00:00'))
                event_end = datetime.fromisoformat(event_end_str.replace('Z', '+00:00'))

                if event_start.tzinfo != self.timezone:
                    event_start = event_start.astimezone(self.timezone)
                    event_end = event_end.astimezone(self.timezone)

                if (slot_datetime < event_end and slot_end > event_start):
                    return True

            except Exception as e:
                logger.warning(f"Error parsing event time: {e}")
                continue

        return False

    def test_connection(self) -> Dict[str, Any]:
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

            credentials = self._get_service_account_credentials()
            service_account_email = "Unknown"
            if credentials and hasattr(credentials, 'service_account_email'):
                service_account_email = credentials.service_account_email
            elif self.credentials_json:
                try:
                    creds_info = json.loads(self.credentials_json)
                    service_account_email = creds_info.get('client_email', 'Unknown')
                except:
                    pass

            return {
                'status': 'success',
                'calendar_name': calendar.get('summary', 'Unknown'),
                'calendar_id': self.calendar_id,
                'timezone': str(self.timezone),
                'recent_events_count': len(events),
                'service_account_email': service_account_email,
                'authentication_method': 'service_account',
                'message': 'Google Calendar connection successful with service account'
            }

        except Exception as e:
            logger.error(f"Calendar connection test failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'authentication_method': 'service_account',
                'message': 'Google Calendar connection failed'
            }

_enhanced_calendar_manager = None

def get_enhanced_calendar_manager(timezone_str: str = None) -> EnhancedCalendarManager:
    global _enhanced_calendar_manager

    if _enhanced_calendar_manager is None:
        if timezone_str is None:
            timezone_str = os.getenv('TIMEZONE', 'Asia/Kolkata')
        _enhanced_calendar_manager = EnhancedCalendarManager(timezone_str)

    return _enhanced_calendar_manager

"""
Multi-User Calendar Manager for TailorTalk Enhanced
Handles calendar operations for multiple authenticated users
"""
import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any
import pytz
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from backend.google_auth_manager import google_auth_manager
from backend.timezone_manager import timezone_manager

logger = logging.getLogger(__name__)

class MultiUserCalendarManager:
    """Manages calendar operations for multiple users"""
    
    def __init__(self):
        self.calendar_services: Dict[str, Any] = {}
        self.user_calendars: Dict[str, List[Dict[str, Any]]] = {}
        
        # Default business hours
        self.default_business_hours = {
            'start': time(9, 0),  # 9:00 AM
            'end': time(18, 0),   # 6:00 PM
            'days': [0, 1, 2, 3, 4]  # Monday to Friday
        }
        
        logger.info("Multi-user Calendar Manager initialized")
    
    def _get_calendar_service(self, user_id: str):
        """Get or create calendar service for user"""
        if user_id not in self.calendar_services:
            credentials = google_auth_manager.get_user_credentials(user_id)
            
            if not credentials or not credentials.valid:
                raise ValueError(f"Invalid credentials for user: {user_id}")
            
            service = build('calendar', 'v3', credentials=credentials)
            self.calendar_services[user_id] = service
        
        return self.calendar_services[user_id]
    
    def get_user_calendars(self, user_id: str) -> List[Dict[str, Any]]:
        """Get list of calendars for user"""
        try:
            service = self._get_calendar_service(user_id)
            
            calendar_list = service.calendarList().list().execute()
            calendars = []
            
            for calendar_item in calendar_list.get('items', []):
                calendars.append({
                    'id': calendar_item['id'],
                    'summary': calendar_item.get('summary', ''),
                    'description': calendar_item.get('description', ''),
                    'primary': calendar_item.get('primary', False),
                    'access_role': calendar_item.get('accessRole', ''),
                    'background_color': calendar_item.get('backgroundColor', ''),
                    'foreground_color': calendar_item.get('foregroundColor', '')
                })
            
            self.user_calendars[user_id] = calendars
            logger.info(f"Retrieved {len(calendars)} calendars for user: {user_id}")
            
            return calendars
            
        except HttpError as e:
            logger.error(f"HTTP error getting calendars for user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting calendars for user {user_id}: {e}")
            raise
    
    def get_primary_calendar_id(self, user_id: str) -> str:
        """Get primary calendar ID for user"""
        try:
            calendars = self.get_user_calendars(user_id)
            
            # Find primary calendar
            for calendar in calendars:
                if calendar.get('primary', False):
                    return calendar['id']
            
            # If no primary calendar found, return first calendar
            if calendars:
                return calendars[0]['id']
            
            # Fallback to user's email (default primary calendar)
            user_info = google_auth_manager.get_user_info(user_id)
            return user_info.get('email', 'primary')
            
        except Exception as e:
            logger.error(f"Error getting primary calendar for user {user_id}: {e}")
            return 'primary'
    
    def get_user_events(self, user_id: str, start_date: datetime, end_date: datetime, 
                       calendar_id: str = None) -> List[Dict[str, Any]]:
        """Get events for user within date range"""
        try:
            service = self._get_calendar_service(user_id)
            
            if not calendar_id:
                calendar_id = self.get_primary_calendar_id(user_id)
            
            # Convert to RFC3339 format
            time_min = start_date.isoformat()
            time_max = end_date.isoformat()
            
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = []
            for event in events_result.get('items', []):
                # Parse event details
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                events.append({
                    'id': event['id'],
                    'summary': event.get('summary', 'No Title'),
                    'description': event.get('description', ''),
                    'start': start,
                    'end': end,
                    'location': event.get('location', ''),
                    'attendees': event.get('attendees', []),
                    'status': event.get('status', ''),
                    'html_link': event.get('htmlLink', '')
                })
            
            logger.info(f"Retrieved {len(events)} events for user {user_id}")
            return events
            
        except HttpError as e:
            logger.error(f"HTTP error getting events for user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting events for user {user_id}: {e}")
            raise
    
    def get_user_availability(self, user_id: str, date_str: str, 
                            duration_minutes: int = 60) -> List[str]:
        """Get available time slots for user on specific date"""
        try:
            # Parse date
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Create datetime range for the day
            start_datetime = datetime.combine(target_date, time.min)
            end_datetime = datetime.combine(target_date, time.max)
            
            # Localize to user's timezone
            user_tz = timezone_manager.get_current_timezone()
            start_datetime = user_tz.localize(start_datetime)
            end_datetime = user_tz.localize(end_datetime)
            
            # Get existing events
            existing_events = self.get_user_events(user_id, start_datetime, end_datetime)
            
            # Generate available slots
            available_slots = self._generate_available_slots(
                target_date, existing_events, duration_minutes
            )
            
            logger.info(f"Found {len(available_slots)} available slots for user {user_id} on {date_str}")
            return available_slots
            
        except Exception as e:
            logger.error(f"Error getting availability for user {user_id}: {e}")
            return []
    
    def _generate_available_slots(self, target_date: datetime.date, 
                                existing_events: List[Dict[str, Any]], 
                                duration_minutes: int) -> List[str]:
        """Generate available time slots"""
        try:
            available_slots = []
            
            # Business hours
            business_start = self.default_business_hours['start']
            business_end = self.default_business_hours['end']
            
            # Check if target date is a business day
            if target_date.weekday() not in self.default_business_hours['days']:
                return available_slots
            
            # Create time slots
            current_time = datetime.combine(target_date, business_start)
            end_time = datetime.combine(target_date, business_end)
            
            slot_duration = timedelta(minutes=duration_minutes)
            
            while current_time + slot_duration <= end_time:
                slot_end = current_time + slot_duration
                
                # Check if slot conflicts with existing events
                is_available = True
                for event in existing_events:
                    event_start = self._parse_event_datetime(event['start'])
                    event_end = self._parse_event_datetime(event['end'])
                    
                    # Check for overlap
                    if (current_time < event_end and slot_end > event_start):
                        is_available = False
                        break
                
                if is_available:
                    available_slots.append(current_time.strftime('%H:%M'))
                
                # Move to next slot (30-minute intervals)
                current_time += timedelta(minutes=30)
            
            return available_slots
            
        except Exception as e:
            logger.error(f"Error generating available slots: {e}")
            return []
    
    def _parse_event_datetime(self, datetime_str: str) -> datetime:
        """Parse event datetime string to datetime object"""
        try:
            # Handle both date and datetime formats
            if 'T' in datetime_str:
                # DateTime format
                if datetime_str.endswith('Z'):
                    # UTC format
                    dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                else:
                    # Local timezone format
                    dt = datetime.fromisoformat(datetime_str)
            else:
                # Date only format
                date_obj = datetime.strptime(datetime_str, '%Y-%m-%d').date()
                dt = datetime.combine(date_obj, time.min)
                dt = timezone_manager.get_current_timezone().localize(dt)
            
            return dt
            
        except Exception as e:
            logger.error(f"Error parsing datetime {datetime_str}: {e}")
            return datetime.now()
    
    def create_user_event(self, user_id: str, date_str: str, time_str: str, 
                         event_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create calendar event for user"""
        try:
            service = self._get_calendar_service(user_id)
            calendar_id = self.get_primary_calendar_id(user_id)
            
            # Parse date and time
            event_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            event_time = datetime.strptime(time_str, '%H:%M').time()
            
            # Create start datetime
            start_datetime = datetime.combine(event_date, event_time)
            start_datetime = timezone_manager.get_current_timezone().localize(start_datetime)
            
            # Calculate end datetime
            duration = timedelta(minutes=event_details.get('duration', 60))
            end_datetime = start_datetime + duration
            
            # Create event object
            event = {
                'summary': event_details.get('title', 'TailorTalk Appointment'),
                'description': event_details.get('description', ''),
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': str(timezone_manager.get_current_timezone())
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': str(timezone_manager.get_current_timezone())
                },
                'attendees': event_details.get('attendees', []),
                'reminders': {
                    'useDefault': True
                }
            }
            
            # Add location if provided
            if event_details.get('location'):
                event['location'] = event_details['location']
            
            # Create the event
            created_event = service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()
            
            logger.info(f"Created event for user {user_id}: {created_event['id']}")
            
            return {
                'event_id': created_event['id'],
                'event_link': created_event.get('htmlLink', ''),
                'calendar_id': calendar_id,
                'start_time': start_datetime.isoformat(),
                'end_time': end_datetime.isoformat()
            }
            
        except HttpError as e:
            logger.error(f"HTTP error creating event for user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating event for user {user_id}: {e}")
            raise
    
    def update_user_event(self, user_id: str, event_id: str, 
                         updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing calendar event"""
        try:
            service = self._get_calendar_service(user_id)
            calendar_id = self.get_primary_calendar_id(user_id)
            
            # Get existing event
            existing_event = service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Apply updates
            for key, value in updates.items():
                if key in ['summary', 'description', 'location']:
                    existing_event[key] = value
                elif key == 'start_time':
                    existing_event['start']['dateTime'] = value
                elif key == 'end_time':
                    existing_event['end']['dateTime'] = value
            
            # Update the event
            updated_event = service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=existing_event
            ).execute()
            
            logger.info(f"Updated event {event_id} for user {user_id}")
            
            return {
                'event_id': updated_event['id'],
                'event_link': updated_event.get('htmlLink', ''),
                'updated_at': datetime.now().isoformat()
            }
            
        except HttpError as e:
            logger.error(f"HTTP error updating event {event_id} for user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating event {event_id} for user {user_id}: {e}")
            raise
    
    def delete_user_event(self, user_id: str, event_id: str) -> bool:
        """Delete calendar event"""
        try:
            service = self._get_calendar_service(user_id)
            calendar_id = self.get_primary_calendar_id(user_id)
            
            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"Deleted event {event_id} for user {user_id}")
            return True
            
        except HttpError as e:
            logger.error(f"HTTP error deleting event {event_id} for user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting event {event_id} for user {user_id}: {e}")
            return False
    
    def get_user_upcoming_events(self, user_id: str, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming events for user"""
        try:
            now = datetime.now(timezone_manager.get_current_timezone())
            future_date = now + timedelta(days=days_ahead)
            
            events = self.get_user_events(user_id, now, future_date)
            
            # Sort by start time
            events.sort(key=lambda x: x['start'])
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting upcoming events for user {user_id}: {e}")
            return []
    
    def get_user_calendar_info(self, user_id: str) -> Dict[str, Any]:
        """Get calendar information for user"""
        try:
            calendars = self.get_user_calendars(user_id)
            primary_calendar_id = self.get_primary_calendar_id(user_id)
            
            # Get recent events count
            now = datetime.now(timezone_manager.get_current_timezone())
            week_ago = now - timedelta(days=7)
            recent_events = self.get_user_events(user_id, week_ago, now)
            
            return {
                'total_calendars': len(calendars),
                'primary_calendar_id': primary_calendar_id,
                'calendars': calendars,
                'recent_events_count': len(recent_events),
                'timezone': str(timezone_manager.get_current_timezone())
            }
            
        except Exception as e:
            logger.error(f"Error getting calendar info for user {user_id}: {e}")
            return {}

# Global multi-user calendar manager
multi_user_calendar_manager = MultiUserCalendarManager()

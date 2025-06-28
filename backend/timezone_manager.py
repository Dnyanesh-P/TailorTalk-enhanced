"""
Advanced timezone management for TailorTalk
"""
import pytz
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class TimezoneManager:
    """Advanced timezone handling and conversion"""
    
    def __init__(self, default_timezone: str = 'Asia/Kolkata'):
        self.default_timezone = pytz.timezone(default_timezone)
        self.current_timezone = self.default_timezone
        
        # Common timezone mappings
        self.timezone_aliases = {
            'ist': 'Asia/Kolkata',
            'pst': 'America/Los_Angeles',
            'est': 'America/New_York',
            'gmt': 'GMT',
            'utc': 'UTC',
            'cst': 'America/Chicago',
            'mst': 'America/Denver',
            'jst': 'Asia/Tokyo',
            'cet': 'Europe/Paris',
            'aest': 'Australia/Sydney'
        }
    
    def set_timezone(self, timezone_str: str):
        """Set the current timezone"""
        try:
            self.current_timezone = self.parse_timezone(timezone_str)
            logger.info(f"Timezone set to: {self.current_timezone}")
        except Exception as e:
            logger.error(f"Failed to set timezone {timezone_str}: {e}")
            self.current_timezone = self.default_timezone
    
    def get_current_timezone(self) -> pytz.BaseTzInfo:
        """Get the current timezone"""
        return self.current_timezone
    
    def parse_timezone(self, timezone_input: str) -> pytz.BaseTzInfo:
        """Parse timezone from various input formats"""
        if not timezone_input:
            return self.default_timezone
        
        timezone_input = timezone_input.lower().strip()
        
        # Check aliases first
        if timezone_input in self.timezone_aliases:
            timezone_input = self.timezone_aliases[timezone_input]
        
        try:
            return pytz.timezone(timezone_input)
        except pytz.exceptions.UnknownTimeZoneError:
            logger.warning(f"Unknown timezone: {timezone_input}, using default")
            return self.default_timezone
    
    def convert_time(self, dt: datetime, from_tz: str, to_tz: str) -> datetime:
        """Convert datetime between timezones"""
        try:
            from_timezone = self.parse_timezone(from_tz)
            to_timezone = self.parse_timezone(to_tz)
            
            # Localize if naive
            if dt.tzinfo is None:
                dt = from_timezone.localize(dt)
            
            # Convert to target timezone
            return dt.astimezone(to_timezone)
            
        except Exception as e:
            logger.error(f"Timezone conversion error: {e}")
            return dt
    
    def get_business_hours(self, timezone_str: str) -> Tuple[int, int]:
        """Get business hours for a timezone (9 AM to 6 PM local time)"""
        return (9, 18)  # Can be customized per timezone
    
    def is_business_hours(self, dt: datetime, timezone_str: str) -> bool:
        """Check if datetime is within business hours"""
        try:
            tz = self.parse_timezone(timezone_str)
            local_dt = dt.astimezone(tz)
            start_hour, end_hour = self.get_business_hours(timezone_str)
            
            # Check if it's a weekday and within business hours
            is_weekday = local_dt.weekday() < 5  # Monday = 0, Sunday = 6
            is_business_time = start_hour <= local_dt.hour < end_hour
            
            return is_weekday and is_business_time
            
        except Exception as e:
            logger.error(f"Business hours check error: {e}")
            return True  # Default to allowing the time
    
    def suggest_business_time(self, dt: datetime, timezone_str: str) -> datetime:
        """Suggest next available business time"""
        try:
            tz = self.parse_timezone(timezone_str)
            local_dt = dt.astimezone(tz)
            start_hour, end_hour = self.get_business_hours(timezone_str)
            
            # If it's already business hours, return as is
            if self.is_business_hours(dt, timezone_str):
                return dt
            
            # If it's too early, move to start of business day
            if local_dt.hour < start_hour:
                suggested_dt = local_dt.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            # If it's too late or weekend, move to next business day
            else:
                days_ahead = 1
                if local_dt.weekday() >= 4:  # Friday or later
                    days_ahead = 7 - local_dt.weekday()  # Move to Monday
                
                suggested_dt = (local_dt + timedelta(days=days_ahead)).replace(
                    hour=start_hour, minute=0, second=0, microsecond=0
                )
            
            return suggested_dt.astimezone(dt.tzinfo)
            
        except Exception as e:
            logger.error(f"Business time suggestion error: {e}")
            return dt
    
    def format_time_for_user(self, dt: datetime, user_timezone: str) -> str:
        """Format datetime for user display"""
        try:
            user_tz = self.parse_timezone(user_timezone)
            user_dt = dt.astimezone(user_tz)
            
            return user_dt.strftime('%A, %B %d, %Y at %I:%M %p %Z')
            
        except Exception as e:
            logger.error(f"Time formatting error: {e}")
            return dt.strftime('%Y-%m-%d %H:%M')
    
    def get_timezone_info(self, timezone_str: str) -> Dict[str, str]:
        """Get timezone information"""
        try:
            tz = self.parse_timezone(timezone_str)
            now = datetime.now(tz)
            
            return {
                'timezone': str(tz),
                'current_time': now.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'utc_offset': now.strftime('%z'),
                'is_dst': bool(now.dst())
            }
            
        except Exception as e:
            logger.error(f"Timezone info error: {e}")
            return {
                'timezone': timezone_str,
                'current_time': 'Unknown',
                'utc_offset': 'Unknown',
                'is_dst': False
            }

# Global timezone manager
timezone_manager = TimezoneManager()

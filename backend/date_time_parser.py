"""
Advanced date and time parsing for natural language inputs
"""

import re
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Tuple, List
import pytz
from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta
import calendar

class DateTimeParser:
    def __init__(self, timezone_str: str = 'Asia/Kolkata'):
        self.timezone = pytz.timezone(timezone_str)
        self.now = datetime.now(self.timezone)
        
        # Common date patterns
        self.date_patterns = {
            # Relative dates
            r'\btoday\b': self._get_today,
            r'\btomorrow\b': self._get_tomorrow,
            r'\byesterday\b': self._get_yesterday,
            r'\bnext week\b': self._get_next_week,
            r'\bthis week\b': self._get_this_week,
            r'\bnext month\b': self._get_next_month,
            r'\bthis month\b': self._get_this_month,
            
            # Specific weekdays
            r'\bnext (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b': self._get_next_weekday,
            r'\bthis (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b': self._get_this_weekday,
            r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b': self._get_upcoming_weekday,
            
            # Specific dates
            r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})\b': self._parse_date_format,
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?\b': self._parse_month_day,
            r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b': self._parse_day_month,
            
            # Relative with numbers
            r'\bin\s+(\d+)\s+days?\b': self._get_in_days,
            r'\bin\s+(\d+)\s+weeks?\b': self._get_in_weeks,
            r'\bin\s+a\s+week\b': lambda: self._get_in_days(7),
            r'\bin\s+(\d+)\s+months?\b': self._get_in_months,
        }
        
        # Time patterns
        self.time_patterns = {
            # 12-hour format
            r'\b(\d{1,2}):(\d{2})\s*(am|pm)\b': self._parse_12_hour,
            r'\b(\d{1,2})\s*(am|pm)\b': self._parse_12_hour_simple,
            
            # 24-hour format
            r'\b(\d{1,2}):(\d{2})\b': self._parse_24_hour,
            r'\b(\d{1,2})(\d{2})\s*hours?\b': self._parse_military_time,
            
            # Relative times
            r'\bmorning\b': lambda: '09:00',
            r'\bafternoon\b': lambda: '15:00',
            r'\bevening\b': lambda: '18:00',
            r'\bnight\b': lambda: '20:00',
            r'\bmidnight\b': lambda: '00:00',
            r'\bnoon\b': lambda: '12:00',
            
            # Specific time phrases
            r'\bhalf past (\d{1,2})\b': self._parse_half_past,
            r'\bquarter past (\d{1,2})\b': self._parse_quarter_past,
            r'\bquarter to (\d{1,2})\b': self._parse_quarter_to,
        }
        
        # Month mapping
        self.months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
            'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9,
            'oct': 10, 'nov': 11, 'dec': 12
        }
        
        # Weekday mapping
        self.weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6,
            'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3,
            'fri': 4, 'sat': 5, 'sun': 6
        }
    
    def parse_datetime(self, text: str) -> Dict[str, Optional[str]]:
        """
        Parse natural language text to extract date and time information
        
        Returns:
            Dict with 'date', 'time', 'confidence', and 'original_text' keys
        """
        text_lower = text.lower().strip()
        result = {
            'date': None,
            'time': None,
            'confidence': 0.0,
            'original_text': text,
            'parsed_components': []
        }
        
        # Try to parse date
        date_result = self._extract_date(text_lower)
        if date_result:
            result['date'] = date_result['date']
            result['confidence'] += date_result['confidence']
            result['parsed_components'].append(f"Date: {date_result['matched_text']}")
        
        # Try to parse time
        time_result = self._extract_time(text_lower)
        if time_result:
            result['time'] = time_result['time']
            result['confidence'] += time_result['confidence']
            result['parsed_components'].append(f"Time: {time_result['matched_text']}")
        
        # Normalize confidence
        if result['parsed_components']:
            result['confidence'] = min(result['confidence'] / len(result['parsed_components']), 1.0)
        
        return result
    
    def _extract_date(self, text: str) -> Optional[Dict]:
        """Extract date from text using various patterns"""
        for pattern, handler in self.date_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if callable(handler):
                        if len(match.groups()) > 0:
                            date_obj = handler(*match.groups())
                        else:
                            date_obj = handler()
                    else:
                        date_obj = handler
                    
                    if isinstance(date_obj, date):
                        return {
                            'date': date_obj.strftime('%Y-%m-%d'),
                            'confidence': 0.9,
                            'matched_text': match.group(0)
                        }
                except Exception as e:
                    print(f"Error parsing date with pattern {pattern}: {e}")
                    continue
        
        # Try dateutil parser as fallback
        try:
            parsed_date = dateutil_parser.parse(text, fuzzy=True, default=self.now)
            if parsed_date.date() != self.now.date():  # Only if it's different from today
                return {
                    'date': parsed_date.date().strftime('%Y-%m-%d'),
                    'confidence': 0.7,
                    'matched_text': 'fuzzy parsing'
                }
        except:
            pass
        
        return None
    
    def _extract_time(self, text: str) -> Optional[Dict]:
        """Extract time from text using various patterns"""
        for pattern, handler in self.time_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if callable(handler):
                        if len(match.groups()) > 0:
                            time_str = handler(*match.groups())
                        else:
                            time_str = handler()
                    else:
                        time_str = handler
                    
                    # Validate time format
                    if self._is_valid_time(time_str):
                        return {
                            'time': time_str,
                            'confidence': 0.9,
                            'matched_text': match.group(0)
                        }
                except Exception as e:
                    print(f"Error parsing time with pattern {pattern}: {e}")
                    continue
        
        return None
    
    def _is_valid_time(self, time_str: str) -> bool:
        """Validate time string format"""
        try:
            time_parts = time_str.split(':')
            if len(time_parts) != 2:
                return False
            hour, minute = int(time_parts[0]), int(time_parts[1])
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except:
            return False
    
    # Date parsing methods
    def _get_today(self) -> date:
        return self.now.date()
    
    def _get_tomorrow(self) -> date:
        return self.now.date() + timedelta(days=1)
    
    def _get_yesterday(self) -> date:
        return self.now.date() - timedelta(days=1)
    
    def _get_next_week(self) -> date:
        return self.now.date() + timedelta(weeks=1)
    
    def _get_this_week(self) -> date:
        # Return next Monday of this week
        days_ahead = 0 - self.now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return self.now.date() + timedelta(days=days_ahead)
    
    def _get_next_month(self) -> date:
        return self.now.date() + relativedelta(months=1)
    
    def _get_this_month(self) -> date:
        return self.now.date()
    
    def _get_next_weekday(self, weekday_name: str) -> date:
        weekday_num = self.weekdays.get(weekday_name.lower())
        if weekday_num is None:
            return self.now.date()
        
        days_ahead = weekday_num - self.now.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return self.now.date() + timedelta(days=days_ahead)
    
    def _get_this_weekday(self, weekday_name: str) -> date:
        weekday_num = self.weekdays.get(weekday_name.lower())
        if weekday_num is None:
            return self.now.date()
        
        days_ahead = weekday_num - self.now.weekday()
        if days_ahead < 0:  # If it's already passed this week, get next week
            days_ahead += 7
        return self.now.date() + timedelta(days=days_ahead)
    
    def _get_upcoming_weekday(self, weekday_name: str) -> date:
        return self._get_next_weekday(weekday_name)
    
    def _parse_date_format(self, month: str, day: str, year: str) -> date:
        """Parse MM/DD/YYYY or DD/MM/YYYY format"""
        month_num, day_num = int(month), int(day)
        year_num = int(year)
        
        # Handle 2-digit years
        if year_num < 100:
            year_num += 2000 if year_num < 50 else 1900
        
        # Try both MM/DD and DD/MM formats
        try:
            return date(year_num, month_num, day_num)
        except ValueError:
            try:
                return date(year_num, day_num, month_num)
            except ValueError:
                return self.now.date()
    
    def _parse_month_day(self, month_name: str, day: str) -> date:
        """Parse 'January 15th' format"""
        month_num = self.months.get(month_name.lower())
        if month_num is None:
            return self.now.date()
        
        day_num = int(day)
        year = self.now.year
        
        # If the date has passed this year, assume next year
        try:
            target_date = date(year, month_num, day_num)
            if target_date < self.now.date():
                target_date = date(year + 1, month_num, day_num)
            return target_date
        except ValueError:
            return self.now.date()
    
    def _parse_day_month(self, day: str, month_name: str) -> date:
        """Parse '15th January' format"""
        return self._parse_month_day(month_name, day)
    
    def _get_in_days(self, days: str) -> date:
        """Get date N days from now"""
        return self.now.date() + timedelta(days=int(days))
    
    def _get_in_weeks(self, weeks: str) -> date:
        """Get date N weeks from now"""
        return self.now.date() + timedelta(weeks=int(weeks))
    
    def _get_in_months(self, months: str) -> date:
        """Get date N months from now"""
        return self.now.date() + relativedelta(months=int(months))
    
    # Time parsing methods
    def _parse_12_hour(self, hour: str, minute: str = '00', period: str = 'am') -> str:
        """Parse 12-hour format time"""
        hour_num = int(hour)
        minute_num = int(minute) if minute != '00' else 0
        
        if period.lower() == 'pm' and hour_num != 12:
            hour_num += 12
        elif period.lower() == 'am' and hour_num == 12:
            hour_num = 0
        
        return f"{hour_num:02d}:{minute_num:02d}"
    
    def _parse_12_hour_simple(self, hour: str, period: str) -> str:
        """Parse simple 12-hour format (e.g., '3pm')"""
        return self._parse_12_hour(hour, '00', period)
    
    def _parse_24_hour(self, hour: str, minute: str) -> str:
        """Parse 24-hour format time"""
        hour_num = int(hour)
        minute_num = int(minute)
        
        if 0 <= hour_num <= 23 and 0 <= minute_num <= 59:
            return f"{hour_num:02d}:{minute_num:02d}"
        return "09:00"  # Default fallback
    
    def _parse_military_time(self, hour: str, minute: str) -> str:
        """Parse military time format (e.g., '1430 hours')"""
        time_str = hour + minute
        if len(time_str) == 4:
            hour_part = time_str[:2]
            minute_part = time_str[2:]
            return self._parse_24_hour(hour_part, minute_part)
        return "09:00"
    
    def _parse_half_past(self, hour: str) -> str:
        """Parse 'half past X' format"""
        hour_num = int(hour)
        return f"{hour_num:02d}:30"
    
    def _parse_quarter_past(self, hour: str) -> str:
        """Parse 'quarter past X' format"""
        hour_num = int(hour)
        return f"{hour_num:02d}:15"
    
    def _parse_quarter_to(self, hour: str) -> str:
        """Parse 'quarter to X' format"""
        hour_num = int(hour) - 1
        if hour_num < 0:
            hour_num = 23
        return f"{hour_num:02d}:45"
    
    def get_suggestions(self, text: str) -> List[str]:
        """Get suggestions for ambiguous date/time inputs"""
        suggestions = []
        text_lower = text.lower()
        
        # If no clear date/time found, provide suggestions
        if not self._extract_date(text_lower) and not self._extract_time(text_lower):
            suggestions.extend([
                "Try specifying a date like 'tomorrow', 'next Monday', or 'July 15th'",
                "Include a time like '3:30 PM', '15:30', or 'afternoon'",
                "Use formats like 'book tomorrow at 3 PM' or 'schedule for next week at 2:30'"
            ])
        
        return suggestions

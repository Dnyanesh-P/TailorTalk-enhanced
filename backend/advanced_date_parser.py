"""
Advanced date and time parser with high accuracy for appointment scheduling
"""
import re
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Tuple, List, Union
import pytz
from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta
import calendar
import logging

logger = logging.getLogger(__name__)

class AdvancedDateTimeParser:
    """High-precision date and time parser for appointment scheduling"""
    
    def __init__(self, timezone_str: str = 'Asia/Kolkata'):
        self.timezone = pytz.timezone(timezone_str)
        self.now = datetime.now(self.timezone)
        
        # Month mappings with variations
        self.months = {
            # Full names
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12,
            # Short forms
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
            # Common variations
            'sept': 9, 'augus': 8  # Handle typos like "4th Augus"
        }
        
        # Weekday mappings
        self.weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6,
            'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
        }
        
        # Ordinal number patterns
        self.ordinal_pattern = r'(\d{1,2})(?:st|nd|rd|th)?'
        
        # Comprehensive date patterns (order matters - most specific first)
        self.date_patterns = [
            # Specific dates with ordinals: "5th July", "4th August"
            (r'\b' + self.ordinal_pattern + r'\s+(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|augus)\b', 
             self._parse_day_month),
            
            # Month day format: "July 5th", "August 4th"
            (r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|augus)\s+' + self.ordinal_pattern + r'\b',
             self._parse_month_day),
            
            # Numeric dates: "5/7", "4/8", "05/07"
            (r'\b(\d{1,2})[\/\-](\d{1,2})(?:[\/\-](\d{2,4}))?\b', self._parse_numeric_date),
            
            # ISO format: "2025-07-05"
            (r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b', self._parse_iso_date),
            
            # Relative dates
            (r'\btoday\b', lambda: self.now.date()),
            (r'\btomorrow\b', lambda: (self.now + timedelta(days=1)).date()),
            (r'\byesterday\b', lambda: (self.now - timedelta(days=1)).date()),
            (r'\bnext week\b', lambda: (self.now + timedelta(weeks=1)).date()),
            (r'\bin (\d+) days?\b', self._parse_in_days),
            (r'\bin (\d+) weeks?\b', self._parse_in_weeks),
            
            # Weekdays
            (r'\bnext (monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\b', 
             self._parse_next_weekday),
            (r'\bthis (monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\b',
             self._parse_this_weekday),
            (r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\b',
             self._parse_upcoming_weekday),
        ]
        
        # Time patterns (order matters - most specific first)
        self.time_patterns = [
            # 12-hour format with minutes: "3:30pm", "11:45am"
            (r'\b(\d{1,2}):(\d{2})\s*(am|pm)\b', self._parse_12_hour_with_minutes),
            
            # 12-hour format simple: "3pm", "11am"
            (r'\b(\d{1,2})\s*(am|pm)\b', self._parse_12_hour_simple),
            
            # 24-hour format: "15:00", "03:30"
            (r'\b(\d{1,2}):(\d{2})\b', self._parse_24_hour),
            
            # Military time: "1500", "0330"
            (r'\b(\d{4})\s*(?:hours?|hrs?)?\b', self._parse_military_time),
            
            # Relative times
            (r'\bmorning\b', lambda: '09:00'),
            (r'\bafternoon\b', lambda: '15:00'),
            (r'\bevening\b', lambda: '18:00'),
            (r'\bnight\b', lambda: '20:00'),
            (r'\bmidnight\b', lambda: '00:00'),
            (r'\bnoon\b', lambda: '12:00'),
            
            # Specific time phrases
            (r'\bhalf past (\d{1,2})\b', self._parse_half_past),
            (r'\bquarter past (\d{1,2})\b', self._parse_quarter_past),
            (r'\bquarter to (\d{1,2})\b', self._parse_quarter_to),
        ]
    
    def parse_appointment_request(self, text: str) -> Dict[str, any]:
        """
        Parse appointment request with high accuracy
        
        Args:
            text: Natural language appointment request
            
        Returns:
            Dict with parsed date, time, confidence, and details
        """
        text_lower = text.lower().strip()
        
        result = {
            'original_text': text,
            'date': None,
            'time': None,
            'confidence': 0.0,
            'parsing_details': [],
            'errors': [],
            'suggestions': []
        }
        
        logger.info(f"Parsing appointment request: '{text}'")
        
        # Parse date
        date_result = self._extract_date_precise(text_lower)
        if date_result:
            result['date'] = date_result['date']
            result['confidence'] += date_result['confidence']
            result['parsing_details'].append(f"Date: {date_result['matched_text']} -> {date_result['date']}")
            logger.info(f"Parsed date: {date_result['date']} from '{date_result['matched_text']}'")
        else:
            result['errors'].append("Could not parse date from the request")
            result['suggestions'].append("Try formats like '5th July', 'July 5th', or '2025-07-05'")
        
        # Parse time
        time_result = self._extract_time_precise(text_lower)
        if time_result:
            result['time'] = time_result['time']
            result['confidence'] += time_result['confidence']
            result['parsing_details'].append(f"Time: {time_result['matched_text']} -> {time_result['time']}")
            logger.info(f"Parsed time: {time_result['time']} from '{time_result['matched_text']}'")
        else:
            # If no time specified, suggest common times
            result['suggestions'].append("No time specified. Try adding a time like '3:30pm', '15:00', or 'afternoon'")
        
        # Normalize confidence (0.0 to 1.0)
        components_found = len([x for x in [result['date'], result['time']] if x])
        if components_found > 0:
            result['confidence'] = min(result['confidence'] / components_found, 1.0)
        
        # Validate parsed results
        validation_result = self._validate_parsed_datetime(result['date'], result['time'])
        result['errors'].extend(validation_result['errors'])
        result['suggestions'].extend(validation_result['suggestions'])
        
        logger.info(f"Final parsing result: Date={result['date']}, Time={result['time']}, Confidence={result['confidence']:.2f}")
        
        return result
    
    def _extract_date_precise(self, text: str) -> Optional[Dict]:
        """Extract date with high precision"""
        for pattern, handler in self.date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if callable(handler):
                        if match.groups():
                            parsed_date = handler(*match.groups())
                        else:
                            parsed_date = handler()
                    else:
                        parsed_date = handler
                    
                    if isinstance(parsed_date, date):
                        return {
                            'date': parsed_date.strftime('%Y-%m-%d'),
                            'confidence': 0.9,
                            'matched_text': match.group(0),
                            'pattern': pattern
                        }
                except Exception as e:
                    logger.warning(f"Error parsing date with pattern {pattern}: {e}")
                    continue
        
        # Fallback to dateutil parser
        try:
            # Remove common words that might confuse dateutil
            clean_text = re.sub(r'\b(book|appointment|meeting|schedule|on|at|for)\b', '', text, flags=re.IGNORECASE)
            parsed_date = dateutil_parser.parse(clean_text, fuzzy=True, default=self.now)
            
            # Only use if it's different from current date (to avoid false positives)
            if parsed_date.date() != self.now.date():
                return {
                    'date': parsed_date.date().strftime('%Y-%m-%d'),
                    'confidence': 0.6,
                    'matched_text': 'fuzzy parsing',
                    'pattern': 'dateutil_fallback'
                }
        except Exception as e:
            logger.debug(f"Dateutil parsing failed: {e}")
        
        return None
    
    def _extract_time_precise(self, text: str) -> Optional[Dict]:
        """Extract time with high precision"""
        for pattern, handler in self.time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if callable(handler):
                        if match.groups():
                            parsed_time = handler(*match.groups())
                        else:
                            parsed_time = handler()
                    else:
                        parsed_time = handler
                    
                    if self._is_valid_time(parsed_time):
                        return {
                            'time': parsed_time,
                            'confidence': 0.9,
                            'matched_text': match.group(0),
                            'pattern': pattern
                        }
                except Exception as e:
                    logger.warning(f"Error parsing time with pattern {pattern}: {e}")
                    continue
        
        return None
    
    def _parse_day_month(self, day: str, month: str) -> date:
        """Parse 'day month' format like '5th July'"""
        day_num = int(re.sub(r'[^\d]', '', day))
        month_num = self.months.get(month.lower())
        
        if not month_num:
            raise ValueError(f"Unknown month: {month}")
        
        # Determine year - if the date has passed this year, use next year
        current_year = self.now.year
        try:
            target_date = date(current_year, month_num, day_num)
            if target_date < self.now.date():
                target_date = date(current_year + 1, month_num, day_num)
            return target_date
        except ValueError:
            # Invalid date (e.g., Feb 30), try next year
            return date(current_year + 1, month_num, day_num)
    
    def _parse_month_day(self, month: str, day: str) -> date:
        """Parse 'month day' format like 'July 5th'"""
        return self._parse_day_month(day, month)
    
    def _parse_numeric_date(self, part1: str, part2: str, year: str = None) -> date:
        """Parse numeric date formats"""
        day_num, month_num = int(part1), int(part2)
        year_num = int(year) if year else self.now.year
        
        # Handle 2-digit years
        if year and len(year) == 2:
            year_num = 2000 + int(year) if int(year) < 50 else 1900 + int(year)
        
        # Try both DD/MM and MM/DD formats
        try:
            # Try DD/MM first (more common internationally)
            if month_num <= 12:
                target_date = date(year_num, month_num, day_num)
                if not year and target_date < self.now.date():
                    target_date = date(year_num + 1, month_num, day_num)
                return target_date
        except ValueError:
            pass
        
        try:
            # Try MM/DD format
            if day_num <= 12:
                target_date = date(year_num, day_num, month_num)
                if not year and target_date < self.now.date():
                    target_date = date(year_num + 1, day_num, month_num)
                return target_date
        except ValueError:
            pass
        
        raise ValueError(f"Invalid date: {part1}/{part2}")
    
    def _parse_iso_date(self, year: str, month: str, day: str) -> date:
        """Parse ISO date format"""
        return date(int(year), int(month), int(day))
    
    def _parse_in_days(self, days: str) -> date:
        """Parse 'in X days' format"""
        return (self.now + timedelta(days=int(days))).date()
    
    def _parse_in_weeks(self, weeks: str) -> date:
        """Parse 'in X weeks' format"""
        return (self.now + timedelta(weeks=int(weeks))).date()
    
    def _parse_next_weekday(self, weekday: str) -> date:
        """Parse 'next weekday' format"""
        weekday_num = self.weekdays.get(weekday.lower())
        if weekday_num is None:
            raise ValueError(f"Unknown weekday: {weekday}")
        
        days_ahead = weekday_num - self.now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        
        return (self.now + timedelta(days=days_ahead)).date()
    
    def _parse_this_weekday(self, weekday: str) -> date:
        """Parse 'this weekday' format"""
        weekday_num = self.weekdays.get(weekday.lower())
        if weekday_num is None:
            raise ValueError(f"Unknown weekday: {weekday}")
        
        days_ahead = weekday_num - self.now.weekday()
        if days_ahead < 0:
            days_ahead += 7
        
        return (self.now + timedelta(days=days_ahead)).date()
    
    def _parse_upcoming_weekday(self, weekday: str) -> date:
        """Parse upcoming weekday"""
        return self._parse_next_weekday(weekday)
    
    def _parse_12_hour_with_minutes(self, hour: str, minute: str, period: str) -> str:
        """Parse 12-hour format with minutes"""
        hour_num = int(hour)
        minute_num = int(minute)
        
        if period.lower() == 'pm' and hour_num != 12:
            hour_num += 12
        elif period.lower() == 'am' and hour_num == 12:
            hour_num = 0
        
        return f"{hour_num:02d}:{minute_num:02d}"
    
    def _parse_12_hour_simple(self, hour: str, period: str) -> str:
        """Parse simple 12-hour format"""
        return self._parse_12_hour_with_minutes(hour, '00', period)
    
    def _parse_24_hour(self, hour: str, minute: str) -> str:
        """Parse 24-hour format"""
        hour_num = int(hour)
        minute_num = int(minute)
        
        if 0 <= hour_num <= 23 and 0 <= minute_num <= 59:
            return f"{hour_num:02d}:{minute_num:02d}"
        
        raise ValueError(f"Invalid time: {hour}:{minute}")
    
    def _parse_military_time(self, time_str: str) -> str:
        """Parse military time format"""
        if len(time_str) == 4:
            hour = time_str[:2]
            minute = time_str[2:]
            return self._parse_24_hour(hour, minute)
        
        raise ValueError(f"Invalid military time: {time_str}")
    
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
    
    def _is_valid_time(self, time_str: str) -> bool:
        """Validate time string"""
        try:
            parts = time_str.split(':')
            if len(parts) != 2:
                return False
            hour, minute = int(parts[0]), int(parts[1])
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except:
            return False
    
    def _validate_parsed_datetime(self, date_str: Optional[str], time_str: Optional[str]) -> Dict[str, List[str]]:
        """Validate parsed date and time"""
        errors = []
        suggestions = []
        
        if date_str:
            try:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # Check if date is in the past
                if parsed_date < self.now.date():
                    errors.append(f"Date {parsed_date.strftime('%B %d, %Y')} is in the past")
                    suggestions.append("Please specify a future date")
                
                # Check if date is too far in the future
                if parsed_date > self.now.date() + timedelta(days=365):
                    errors.append("Date is more than a year in the future")
                    suggestions.append("Please specify a date within the next year")
                
                # Check if it's a weekend (optional warning)
                if parsed_date.weekday() >= 5:
                    suggestions.append(f"Note: {parsed_date.strftime('%A')} is a weekend")
                    
            except ValueError:
                errors.append(f"Invalid date format: {date_str}")
        
        if time_str:
            try:
                time_parts = time_str.split(':')
                hour, minute = int(time_parts[0]), int(time_parts[1])
                
                # Check business hours (9 AM to 6 PM)
                if hour < 9 or hour >= 18:
                    suggestions.append("Note: Time is outside typical business hours (9 AM - 6 PM)")
                    
            except (ValueError, IndexError):
                errors.append(f"Invalid time format: {time_str}")
        
        return {'errors': errors, 'suggestions': suggestions}

# Global parser instance
advanced_parser = AdvancedDateTimeParser()

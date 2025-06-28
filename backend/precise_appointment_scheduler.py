"""
Precise appointment scheduler with accurate date/time handling
"""
import logging
from datetime import datetime, timedelta, date, time
from typing import Dict, List, Optional, Any, Tuple
import pytz
from backend.advanced_date_parser import advanced_parser
from backend.enhanced_calendar import get_enhanced_calendar_manager

logger = logging.getLogger(__name__)

class PreciseAppointmentScheduler:
    """High-precision appointment scheduler"""
    
    def __init__(self, timezone_str: str = 'Asia/Kolkata'):
        self.timezone = pytz.timezone(timezone_str)
        self.parser = advanced_parser
        
    async def schedule_appointment(self, user_request: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Schedule appointment with precise date/time interpretation
        
        Args:
            user_request: Natural language appointment request
            user_id: User identifier
            
        Returns:
            Detailed scheduling result
        """
        logger.info(f"Processing appointment request for {user_id}: '{user_request}'")
        
        # Parse the request
        parse_result = self.parser.parse_appointment_request(user_request)
        
        result = {
            'success': False,
            'message': '',
            'appointment_details': {},
            'parsing_result': parse_result,
            'available_slots': [],
            'errors': [],
            'suggestions': [],
            'next_action': 'clarify'
        }
        
        # Check if we have parsing errors
        if parse_result['errors']:
            result['errors'].extend(parse_result['errors'])
            result['suggestions'].extend(parse_result['suggestions'])
            result['message'] = self._generate_parsing_error_message(parse_result)
            return result
        
        # Extract parsed components
        requested_date = parse_result['date']
        requested_time = parse_result['time']
        
        logger.info(f"Parsed components - Date: {requested_date}, Time: {requested_time}")
        
        # Handle different scenarios
        if requested_date and requested_time:
            # Both date and time specified - try to book exact slot
            return await self._handle_exact_datetime_request(requested_date, requested_time, user_request, result)
        
        elif requested_date and not requested_time:
            # Only date specified - show available times for that date
            return await self._handle_date_only_request(requested_date, user_request, result)
        
        elif not requested_date and requested_time:
            # Only time specified - find next available date for that time
            return await self._handle_time_only_request(requested_time, user_request, result)
        
        else:
            # Neither date nor time clearly specified
            result['message'] = self._generate_clarification_message(user_request)
            result['suggestions'] = [
                "Try: 'Book appointment on 5th July at 3:30pm'",
                "Or: 'Schedule meeting for July 5th'",
                "Or: 'Book for tomorrow at 2pm'"
            ]
            return result
    
    async def _handle_exact_datetime_request(self, date_str: str, time_str: str, original_request: str, result: Dict) -> Dict[str, Any]:
        """Handle request with both date and time specified"""
        try:
            # Get calendar manager
            calendar_manager = get_enhanced_calendar_manager()
            
            # Check if the exact slot is available
            available_slots = calendar_manager.get_availability(date_str)
            
            if time_str in available_slots:
                # Slot is available - book it
                try:
                    event_id = calendar_manager.create_event_with_details(
                        date=date_str,
                        time=time_str,
                        details={
                            'title': 'Appointment',
                            'description': f'Scheduled via TailorTalk: {original_request}',
                            'duration': 60
                        }
                    )
                    
                    # Format the confirmation
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    time_obj = datetime.strptime(time_str, '%H:%M').time()
                    formatted_date = date_obj.strftime('%A, %B %d, %Y')
                    formatted_time = time_obj.strftime('%I:%M %p')
                    
                    result.update({
                        'success': True,
                        'message': f"✅ **Appointment Confirmed!**\n\n📅 **Date:** {formatted_date}\n🕐 **Time:** {formatted_time}\n📝 **Event ID:** {event_id}\n\nYour appointment has been successfully booked!",
                        'appointment_details': {
                            'date': date_str,
                            'time': time_str,
                            'formatted_date': formatted_date,
                            'formatted_time': formatted_time,
                            'event_id': event_id,
                            'duration': 60
                        },
                        'next_action': 'confirmed'
                    })
                    
                    logger.info(f"Appointment booked successfully: {date_str} at {time_str}")
                    
                except Exception as e:
                    logger.error(f"Failed to create calendar event: {e}")
                    result.update({
                        'success': False,
                        'message': f"❌ Failed to book appointment due to calendar error: {str(e)}",
                        'errors': [f"Calendar booking failed: {str(e)}"],
                        'suggestions': ["Please try again or contact support if the issue persists"]
                    })
            else:
                # Slot not available - suggest alternatives
                result = await self._suggest_alternatives_for_unavailable_slot(
                    date_str, time_str, available_slots, result
                )
                
        except Exception as e:
            logger.error(f"Error handling exact datetime request: {e}")
            result.update({
                'success': False,
                'message': f"❌ Error processing your request: {str(e)}",
                'errors': [str(e)],
                'suggestions': ["Please try again with a different date/time"]
            })
        
        return result
    
    async def _handle_date_only_request(self, date_str: str, original_request: str, result: Dict) -> Dict[str, Any]:
        """Handle request with only date specified"""
        try:
            # Get calendar manager
            calendar_manager = get_enhanced_calendar_manager()
            
            # Get available slots for the date
            available_slots = calendar_manager.get_availability(date_str)
            
            if available_slots:
                # Format the date nicely
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                formatted_date = date_obj.strftime('%A, %B %d, %Y')
                
                # Format available times
                formatted_times = []
                for slot in available_slots[:8]:  # Show max 8 slots
                    time_obj = datetime.strptime(slot, '%H:%M').time()
                    formatted_times.append(f"• **{slot}** ({time_obj.strftime('%I:%M %p')})")
                
                result.update({
                    'success': False,  # Not booked yet, waiting for time selection
                    'message': f"📅 **Available times for {formatted_date}:**\n\n" + 
                              "\n".join(formatted_times) + 
                              f"\n\n📋 **Total available slots:** {len(available_slots)}\n\n" +
                              "Which time works best for you? Just say the time like '10:00' or '3 PM'.",
                    'available_slots': available_slots,
                    'appointment_details': {
                        'date': date_str,
                        'formatted_date': formatted_date
                    },
                    'next_action': 'select_time'
                })
                
                logger.info(f"Showed {len(available_slots)} available slots for {date_str}")
            else:
                # No slots available - suggest alternative dates
                result = await self._suggest_alternative_dates(date_str, result)
                
        except Exception as e:
            logger.error(f"Error handling date-only request: {e}")
            result.update({
                'success': False,
                'message': f"❌ Error checking availability: {str(e)}",
                'errors': [str(e)]
            })
        
        return result
    
    async def _handle_time_only_request(self, time_str: str, original_request: str, result: Dict) -> Dict[str, Any]:
        """Handle request with only time specified"""
        try:
            # Get calendar manager
            calendar_manager = get_enhanced_calendar_manager()
            
            # Check next 7 days for this time slot
            available_dates = []
            today = datetime.now(self.timezone).date()
            
            for i in range(1, 8):  # Check next 7 days
                check_date = today + timedelta(days=i)
                check_date_str = check_date.strftime('%Y-%m-%d')
                
                # Skip weekends for business appointments
                if check_date.weekday() < 5:  # Monday = 0, Friday = 4
                    available_slots = calendar_manager.get_availability(check_date_str)
                    if time_str in available_slots:
                        available_dates.append({
                            'date': check_date_str,
                            'formatted_date': check_date.strftime('%A, %B %d'),
                            'day_name': check_date.strftime('%A')
                        })
            
            if available_dates:
                time_obj = datetime.strptime(time_str, '%H:%M').time()
                formatted_time = time_obj.strftime('%I:%M %p')
                
                date_options = []
                for date_info in available_dates[:5]:  # Show max 5 options
                    date_options.append(f"• **{date_info['formatted_date']}** ({date_info['day_name']})")
                
                result.update({
                    'success': False,  # Not booked yet, waiting for date selection
                    'message': f"🕐 **Available dates for {formatted_time}:**\n\n" +
                              "\n".join(date_options) +
                              "\n\nWhich date works for you?",
                    'available_slots': available_dates,
                    'appointment_details': {
                        'time': time_str,
                        'formatted_time': formatted_time
                    },
                    'next_action': 'select_date'
                })
            else:
                result.update({
                    'success': False,
                    'message': f"❌ No availability found for {time_str} in the next week.\n\n" +
                              "Would you like to try a different time or see all available slots?",
                    'suggestions': [
                        "Try a different time like '10:00 AM' or '2:00 PM'",
                        "Ask to see all available times: 'Show me all available slots'"
                    ]
                })
                
        except Exception as e:
            logger.error(f"Error handling time-only request: {e}")
            result.update({
                'success': False,
                'message': f"❌ Error processing time request: {str(e)}",
                'errors': [str(e)]
            })
        
        return result
    
    async def _suggest_alternatives_for_unavailable_slot(self, date_str: str, time_str: str, available_slots: List[str], result: Dict) -> Dict[str, Any]:
        """Suggest alternatives when requested slot is unavailable"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
            formatted_time = time_obj.strftime('%I:%M %p')
            
            if available_slots:
                # Find closest available times
                requested_minutes = time_obj.hour * 60 + time_obj.minute
                closest_slots = sorted(available_slots, key=lambda x: abs(
                    (datetime.strptime(x, '%H:%M').time().hour * 60 + 
                     datetime.strptime(x, '%H:%M').time().minute) - requested_minutes
                ))
                
                # Format suggestions
                suggestions = []
                for slot in closest_slots[:3]:
                    slot_time = datetime.strptime(slot, '%H:%M').time()
                    suggestions.append(f"• **{slot}** ({slot_time.strftime('%I:%M %p')})")
                
                result.update({
                    'success': False,
                    'message': f"❌ **{formatted_time}** is not available on **{formatted_date}**.\n\n" +
                              f"🕐 **Closest available times:**\n" + "\n".join(suggestions) +
                              f"\n\n📋 **All available slots:** {', '.join(available_slots)}\n\n" +
                              "Which time would work better for you?",
                    'available_slots': available_slots,
                    'appointment_details': {
                        'requested_date': date_str,
                        'requested_time': time_str,
                        'formatted_date': formatted_date,
                        'formatted_time': formatted_time
                    },
                    'next_action': 'select_alternative_time'
                })
            else:
                # No slots available on this date
                result = await self._suggest_alternative_dates(date_str, result)
                
        except Exception as e:
            logger.error(f"Error suggesting alternatives: {e}")
            result.update({
                'success': False,
                'message': f"❌ Error finding alternatives: {str(e)}",
                'errors': [str(e)]
            })
        
        return result
    
    async def _suggest_alternative_dates(self, requested_date_str: str, result: Dict) -> Dict[str, Any]:
        """Suggest alternative dates when requested date has no availability"""
        try:
            calendar_manager = get_enhanced_calendar_manager()
            requested_date = datetime.strptime(requested_date_str, '%Y-%m-%d').date()
            
            # Check next 10 days for availability
            alternative_dates = []
            for i in range(1, 11):
                check_date = requested_date + timedelta(days=i)
                # Skip weekends
                if check_date.weekday() < 5:
                    check_date_str = check_date.strftime('%Y-%m-%d')
                    available_slots = calendar_manager.get_availability(check_date_str)
                    if available_slots:
                        alternative_dates.append({
                            'date': check_date_str,
                            'formatted_date': check_date.strftime('%A, %B %d'),
                            'slots_count': len(available_slots)
                        })
                        
                        if len(alternative_dates) >= 3:  # Show max 3 alternatives
                            break
            
            formatted_requested_date = requested_date.strftime('%A, %B %d, %Y')
            
            if alternative_dates:
                date_suggestions = []
                for alt_date in alternative_dates:
                    date_suggestions.append(f"• **{alt_date['formatted_date']}** ({alt_date['slots_count']} slots available)")
                
                result.update({
                    'success': False,
                    'message': f"❌ No available slots on **{formatted_requested_date}**.\n\n" +
                              f"📅 **Alternative dates:**\n" + "\n".join(date_suggestions) +
                              "\n\nWhich date would work for you?",
                    'available_slots': alternative_dates,
                    'appointment_details': {
                        'requested_date': requested_date_str,
                        'formatted_requested_date': formatted_requested_date
                    },
                    'next_action': 'select_alternative_date'
                })
            else:
                result.update({
                    'success': False,
                    'message': f"❌ No available slots found on **{formatted_requested_date}** or in the following week.\n\n" +
                              "Would you like to:\n" +
                              "• Try a different week\n" +
                              "• See all available dates\n" +
                              "• Schedule for a different time period",
                    'suggestions': [
                        "Try: 'Show me availability for next week'",
                        "Or: 'What dates are available in August?'"
                    ]
                })
                
        except Exception as e:
            logger.error(f"Error suggesting alternative dates: {e}")
            result.update({
                'success': False,
                'message': f"❌ Error finding alternative dates: {str(e)}",
                'errors': [str(e)]
            })
        
        return result
    
    def _generate_parsing_error_message(self, parse_result: Dict) -> str:
        """Generate user-friendly message for parsing errors"""
        errors = parse_result['errors']
        suggestions = parse_result['suggestions']
        
        message = "❌ I couldn't understand the date/time in your request.\n\n"
        
        if errors:
            message += "**Issues found:**\n"
            for error in errors:
                message += f"• {error}\n"
            message += "\n"
        
        if suggestions:
            message += "**Try these formats:**\n"
            for suggestion in suggestions:
                message += f"• {suggestion}\n"
        
        message += "\n**Examples:**\n"
        message += "• 'Book appointment on 5th July at 3:30pm'\n"
        message += "• 'Schedule meeting for August 4th at 15:00'\n"
        message += "• 'Book for tomorrow at 2 PM'"
        
        return message
    
    def _generate_clarification_message(self, original_request: str) -> str:
        """Generate message asking for clarification"""
        return f"I'd like to help you schedule an appointment, but I need more specific details.\n\n" \
               f"**Your request:** '{original_request}'\n\n" \
               f"**Please specify:**\n" \
               f"• **Date:** When would you like to meet?\n" \
               f"• **Time:** What time works for you?\n\n" \
               f"**Example:** 'Book appointment on 5th July at 3:30pm'"

# Global scheduler instance
precise_scheduler = PreciseAppointmentScheduler()

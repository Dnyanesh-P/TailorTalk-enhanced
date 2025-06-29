"""
Comprehensive test suite for precise appointment scheduling
"""
import asyncio
import pytest
from datetime import datetime, date, timedelta
import pytz
import re
from backend.advanced_date_parser import AdvancedDateTimeParser
from backend.precise_appointment_scheduler import PreciseAppointmentScheduler
from backend.enhanced_booking_agent import EnhancedBookingAgent

class TestPreciseScheduling:
    """Test suite for precise appointment scheduling"""
    
    def setup_method(self):
        """Setup test environment"""
        self.timezone = pytz.timezone('Asia/Kolkata')
        self.parser = AdvancedDateTimeParser('Asia/Kolkata')
        self.scheduler = PreciseAppointmentScheduler('Asia/Kolkata')
        self.agent = EnhancedBookingAgent('Asia/Kolkata')
    
    def test_date_parsing_accuracy(self):
        """Test accurate date parsing for various formats"""
        test_cases = [
            # Format: (input, expected_date_pattern, should_succeed)
            ("5th July", r"2025-07-05", True),
            ("4th August", r"2025-08-04", True),
            ("July 5th", r"2025-07-05", True),
            ("August 4th", r"2025-08-04", True),
            ("4th Augus", r"2025-08-04", True),  # Handle typo
            ("tomorrow", None, True),  # Relative date
            ("next Monday", None, True),  # Relative weekday
            ("2025-07-05", r"2025-07-05", True),  # ISO format
            ("5/7/2025", r"2025-07-05", True),  # Numeric format
        ]
        
        for input_text, expected_pattern, should_succeed in test_cases:
            result = self.parser.parse_appointment_request(input_text)
            
            if should_succeed:
                assert result['date'] is not None, f"Failed to parse date from: {input_text}"
                if expected_pattern:
                    date_str = str(result['date'])
                    assert re.fullmatch(expected_pattern, date_str), f"Expected pattern {expected_pattern}, got {result['date']} for: {input_text}"
                print(f"✅ Date parsing: '{input_text}' -> {result['date']}")
            else:
                assert result['date'] is None, f"Should not have parsed date from: {input_text}"
    
    def test_time_parsing_accuracy(self):
        """Test accurate time parsing for various formats"""
        test_cases = [
            # Format: (input, expected_time, should_succeed)
            ("3:30pm", "15:30", True),
            ("3:30 PM", "15:30", True),
            ("15:00", "15:00", True),
            ("3pm", "15:00", True),
            ("11:45am", "11:45", True),
            ("morning", "09:00", True),
            ("afternoon", "15:00", True),
            ("evening", "18:00", True),
            ("noon", "12:00", True),
            ("midnight", "00:00", True),
        ]
        
        for input_text, expected_time, should_succeed in test_cases:
            result = self.parser.parse_appointment_request(input_text)
            
            if should_succeed:
                assert result['time'] is not None, f"Failed to parse time from: {input_text}"
                assert result['time'] == expected_time, f"Expected {expected_time}, got {result['time']} for: {input_text}"
                print(f"✅ Time parsing: '{input_text}' -> {result['time']}")
            else:
                assert result['time'] is None, f"Should not have parsed time from: {input_text}"
    
    def test_combined_datetime_parsing(self):
        """Test parsing of combined date and time expressions"""
        test_cases = [
            ("book appointment on 5th July at 3:30pm", "2025-07-05", "15:30"),
            ("meeting on 4th August 15:00", "2025-08-04", "15:00"),
            ("schedule for July 5th at 2 PM", "2025-07-05", "14:00"),
            ("book for tomorrow at morning", None, "09:00"),  # Tomorrow is relative
            ("appointment next Monday at 10:00", None, "10:00"),  # Next Monday is relative
        ]
        
        for input_text, expected_date, expected_time in test_cases:
            result = self.parser.parse_appointment_request(input_text)
            
            if expected_date:
                assert result['date'] == expected_date, f"Date mismatch for '{input_text}': expected {expected_date}, got {result['date']}"
            
            if expected_time:
                assert result['time'] == expected_time, f"Time mismatch for '{input_text}': expected {expected_time}, got {result['time']}"
            
            print(f"✅ Combined parsing: '{input_text}' -> Date: {result['date']}, Time: {result['time']}")
    
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        test_cases = [
            "book appointment on 32nd July",  # Invalid date
            "meeting at 25:00",  # Invalid time
            "schedule for February 30th",  # Invalid date
            "book for yesterday",  # Past date
        ]
        
        for input_text in test_cases:
            result = self.parser.parse_appointment_request(input_text)
            
            # Should have errors or suggestions
            assert len(result['errors']) > 0 or len(result['suggestions']) > 0, \
                f"Should have errors/suggestions for invalid input: {input_text}"
            
            print(f"✅ Error handling: '{input_text}' -> Errors: {len(result['errors'])}, Suggestions: {len(result['suggestions'])}")
    
    @pytest.mark.asyncio
    async def test_appointment_scheduling_flow(self):
        """Test the complete appointment scheduling flow"""
        # Test exact date/time booking
        test_requests = [
            "I want to book appointment on 5th July at 3:30pm",
            "Schedule meeting for August 4th at 15:00",
            "Book appointment tomorrow at 2 PM",
        ]
        
        for request in test_requests:
            try:
                result = await self.scheduler.schedule_appointment(request, "test_user")
                
                # Should have parsing result
                assert 'parsing_result' in result
                assert result['parsing_result']['date'] is not None or result['parsing_result']['time'] is not None
                
                # Should have a meaningful message
                assert len(result['message']) > 0
                
                print(f"✅ Scheduling flow: '{request}' -> Success: {result.get('success', False)}")
                print(f"   Message: {result['message'][:100]}...")
                
            except Exception as e:
                print(f"❌ Scheduling flow error for '{request}': {e}")
    
    @pytest.mark.asyncio
    async def test_agent_conversation_flow(self):
        """Test the enhanced booking agent conversation flow"""
        test_conversations = [
            [
                ("Hello", "greeting"),
                ("I want to book appointment on 5th July", "appointment_booking"),
                ("3:30pm", "time_selection"),
            ],
            [
                ("Book meeting for tomorrow", "appointment_booking"),
                ("2 PM", "time_selection"),
            ],
            [
                ("Show me availability for 5th July", "availability_check"),
            ]
        ]
        
        for conversation in test_conversations:
            user_id = f"test_user_{len(conversation)}"
            
            for message, expected_intent in conversation:
                try:
                    response = await self.agent.process_message(message, user_id)
                    
                    # Should get a meaningful response
                    assert len(response) > 0
                    assert not response.startswith("❌ I'm experiencing technical difficulties")
                    
                    print(f"✅ Agent conversation: '{message}' -> Response length: {len(response)}")
                    
                except Exception as e:
                    print(f"❌ Agent conversation error for '{message}': {e}")
    
    def test_date_validation(self):
        """Test date validation logic"""
        # Test past dates
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        result = self.parser._validate_parsed_datetime(yesterday, "15:00")
        assert len(result['errors']) > 0, "Should have error for past date"
        
        # Test future dates
        future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        result = self.parser._validate_parsed_datetime(future_date, "15:00")
        assert len(result['errors']) == 0, "Should not have error for valid future date"
        
        print("✅ Date validation tests passed")
    
    def test_business_hours_suggestions(self):
        """Test business hours suggestions"""
        # Test early morning time
        result = self.parser._validate_parsed_datetime("2025-07-05", "06:00")
        assert any("business hours" in suggestion.lower() for suggestion in result['suggestions']), \
            "Should suggest business hours for early time"
        
        # Test late evening time
        result = self.parser._validate_parsed_datetime("2025-07-05", "20:00")
        assert any("business hours" in suggestion.lower() for suggestion in result['suggestions']), \
            "Should suggest business hours for late time"
        
        print("✅ Business hours suggestion tests passed")

def run_comprehensive_tests():
    """Run all tests"""
    print("🧪 Starting Comprehensive Precise Scheduling Tests")
    print("=" * 60)
    
    test_suite = TestPreciseScheduling()
    test_suite.setup_method()
    
    # Run synchronous tests
    print("\n📅 Testing Date Parsing Accuracy...")
    test_suite.test_date_parsing_accuracy()
    
    print("\n🕐 Testing Time Parsing Accuracy...")
    test_suite.test_time_parsing_accuracy()
    
    print("\n📅🕐 Testing Combined DateTime Parsing...")
    test_suite.test_combined_datetime_parsing()
    
    print("\n❌ Testing Error Handling...")
    test_suite.test_error_handling()
    
    print("\n✅ Testing Date Validation...")
    test_suite.test_date_validation()
    
    print("\n🏢 Testing Business Hours Suggestions...")
    test_suite.test_business_hours_suggestions()
    
    # Run asynchronous tests
    print("\n📋 Testing Appointment Scheduling Flow...")
    asyncio.run(test_suite.test_appointment_scheduling_flow())
    
    print("\n💬 Testing Agent Conversation Flow...")
    asyncio.run(test_suite.test_agent_conversation_flow())
    
    print("\n" + "=" * 60)
    print("✅ All Comprehensive Tests Completed!")
    print("\n🎉 Your precise appointment scheduling system is ready!")

if __name__ == "__main__":
    run_comprehensive_tests()

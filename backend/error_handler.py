"""
Comprehensive error handling for TailorTalk
"""
import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime
import pytz
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    OPENAI_API_ERROR = "openai_api_error"
    GOOGLE_CALENDAR_ERROR = "google_calendar_error"
    AUTHENTICATION_ERROR = "authentication_error"
    PARSING_ERROR = "parsing_error"
    VALIDATION_ERROR = "validation_error"
    NETWORK_ERROR = "network_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    UNKNOWN_ERROR = "unknown_error"

class TailorTalkError(Exception):
    """Base exception for TailorTalk application"""
    
    def __init__(self, message: str, error_type: ErrorType, details: Optional[Dict] = None):
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        self.timestamp = datetime.now(pytz.UTC)
        super().__init__(self.message)

class ErrorHandler:
    """Centralized error handling and recovery"""
    
    def __init__(self, timezone_str: str = 'Asia/Kolkata'):
        self.timezone = pytz.timezone(timezone_str)
        self.error_counts = {}
        self.recovery_strategies = {
            ErrorType.OPENAI_API_ERROR: self._handle_openai_error,
            ErrorType.GOOGLE_CALENDAR_ERROR: self._handle_calendar_error,
            ErrorType.AUTHENTICATION_ERROR: self._handle_auth_error,
            ErrorType.PARSING_ERROR: self._handle_parsing_error,
            ErrorType.RATE_LIMIT_ERROR: self._handle_rate_limit_error,
        }
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle errors with appropriate recovery strategies"""
        try:
            # Classify error
            error_type = self._classify_error(error)
            
            # Log error
            self._log_error(error, error_type, context)
            
            # Update error counts
            self._update_error_counts(error_type)
            
            # Apply recovery strategy
            recovery_result = self._apply_recovery_strategy(error, error_type, context)
            
            return {
                'success': recovery_result.get('success', False),
                'message': recovery_result.get('message', 'An error occurred'),
                'error_type': error_type.value,
                'timestamp': datetime.now(self.timezone).isoformat(),
                'recovery_applied': recovery_result.get('recovery_applied', False),
                'user_message': recovery_result.get('user_message', 'Please try again later')
            }
            
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
            return {
                'success': False,
                'message': 'Critical error in error handling system',
                'error_type': ErrorType.UNKNOWN_ERROR.value,
                'timestamp': datetime.now(self.timezone).isoformat(),
                'user_message': 'System temporarily unavailable'
            }
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error type based on exception details"""
        error_str = str(error).lower()
        
        # OpenAI API errors
        if any(keyword in error_str for keyword in ['openai', 'api key', 'rate limit exceeded', 'quota']):
            if 'rate limit' in error_str or 'quota' in error_str:
                return ErrorType.RATE_LIMIT_ERROR
            return ErrorType.OPENAI_API_ERROR
        
        # Google Calendar errors
        if any(keyword in error_str for keyword in ['calendar', 'google', 'oauth', 'credentials']):
            if 'auth' in error_str or 'credential' in error_str:
                return ErrorType.AUTHENTICATION_ERROR
            return ErrorType.GOOGLE_CALENDAR_ERROR
        
        # Network errors
        if any(keyword in error_str for keyword in ['connection', 'network', 'timeout', 'unreachable']):
            return ErrorType.NETWORK_ERROR
        
        # Parsing errors
        if any(keyword in error_str for keyword in ['parse', 'format', 'invalid date', 'invalid time']):
            return ErrorType.PARSING_ERROR
        
        return ErrorType.UNKNOWN_ERROR
    
    def _log_error(self, error: Exception, error_type: ErrorType, context: Dict[str, Any]):
        """Log error with context"""
        logger.error(f"Error Type: {error_type.value}")
        logger.error(f"Error Message: {str(error)}")
        logger.error(f"Context: {context}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _update_error_counts(self, error_type: ErrorType):
        """Update error counts for monitoring"""
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
    
    def _apply_recovery_strategy(self, error: Exception, error_type: ErrorType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply appropriate recovery strategy"""
        if error_type in self.recovery_strategies:
            return self.recovery_strategies[error_type](error, context)
        else:
            return self._handle_unknown_error(error, context)
    
    def _handle_openai_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle OpenAI API errors"""
        error_str = str(error).lower()
        
        if 'api key' in error_str:
            return {
                'success': False,
                'message': 'OpenAI API key invalid or missing',
                'recovery_applied': True,
                'user_message': 'AI features temporarily unavailable. Using basic booking system.'
            }
        elif 'rate limit' in error_str or 'quota' in error_str:
            return {
                'success': False,
                'message': 'OpenAI API rate limit exceeded',
                'recovery_applied': True,
                'user_message': 'AI is busy right now. Please try again in a moment.'
            }
        else:
            return {
                'success': False,
                'message': f'OpenAI API error: {str(error)}',
                'recovery_applied': False,
                'user_message': 'AI assistant temporarily unavailable. You can still book appointments manually.'
            }
    
    def _handle_calendar_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Google Calendar errors"""
        return {
            'success': False,
            'message': f'Calendar error: {str(error)}',
            'recovery_applied': True,
            'user_message': 'Calendar temporarily unavailable. Please check your availability manually.'
        }
    
    def _handle_auth_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle authentication errors"""
        return {
            'success': False,
            'message': f'Authentication error: {str(error)}',
            'recovery_applied': True,
            'user_message': 'Please re-authenticate with Google Calendar to continue booking.'
        }
    
    def _handle_parsing_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle parsing errors"""
        return {
            'success': False,
            'message': f'Parsing error: {str(error)}',
            'recovery_applied': True,
            'user_message': 'Could not understand the date/time format. Please try: "tomorrow at 3 PM" or "July 15th at 2:30"'
        }
    
    def _handle_rate_limit_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle rate limit errors"""
        return {
            'success': False,
            'message': f'Rate limit error: {str(error)}',
            'recovery_applied': True,
            'user_message': 'Too many requests. Please wait a moment before trying again.'
        }
    
    def _handle_unknown_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unknown errors"""
        return {
            'success': False,
            'message': f'Unknown error: {str(error)}',
            'recovery_applied': False,
            'user_message': 'Something went wrong. Please try again or contact support.'
        }
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        return {
            'error_counts': {error_type.value: count for error_type, count in self.error_counts.items()},
            'total_errors': sum(self.error_counts.values()),
            'timestamp': datetime.now(self.timezone).isoformat()
        }

# Global error handler instance
error_handler = ErrorHandler()

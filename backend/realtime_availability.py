"""
Real-time availability updates for TailorTalk
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set
import pytz
from backend.enhanced_calendar import get_enhanced_calendar_manager

logger = logging.getLogger(__name__)

class RealTimeAvailabilityManager:
    """Manages real-time availability updates"""
    
    def __init__(self, timezone_str: str = 'Asia/Kolkata'):
        self.timezone = pytz.timezone(timezone_str)
        self.subscribers: Set[str] = set()
        self.last_availability: Dict[str, any] = {}
        self.update_interval = 30  # seconds
        self.is_running = False
        
    async def start_monitoring(self):
        """Start monitoring availability changes"""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info("Starting real-time availability monitoring")
        
        while self.is_running:
            try:
                await self._check_and_update_availability()
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in availability monitoring: {e}")
                await asyncio.sleep(5)  # Short delay before retry
    
    async def stop_monitoring(self):
        """Stop monitoring availability changes"""
        self.is_running = False
        logger.info("Stopped real-time availability monitoring")
    
    async def _check_and_update_availability(self):
        """Check for availability changes and notify subscribers"""
        try:
            calendar_manager = get_enhanced_calendar_manager()
            
            # Check today and next 7 days
            today = datetime.now(self.timezone).date()
            dates_to_check = [today + timedelta(days=i) for i in range(8)]
            
            changes_detected = False
            
            for check_date in dates_to_check:
                date_str = check_date.strftime('%Y-%m-%d')
                
                try:
                    current_availability = calendar_manager.get_availability(date_str)
                    
                    # Compare with last known availability
                    if date_str in self.last_availability:
                        if set(current_availability) != set(self.last_availability[date_str]):
                            changes_detected = True
                            logger.info(f"Availability changed for {date_str}")
                    
                    self.last_availability[date_str] = current_availability
                    
                except Exception as e:
                    logger.warning(f"Failed to check availability for {date_str}: {e}")
            
            if changes_detected:
                await self._notify_subscribers()
                
        except Exception as e:
            logger.error(f"Error checking availability updates: {e}")
    
    async def _notify_subscribers(self):
        """Notify all subscribers of availability changes"""
        if not self.subscribers:
            return
            
        notification = {
            'type': 'availability_update',
            'timestamp': datetime.now(self.timezone).isoformat(),
            'message': 'Availability has been updated',
            'affected_dates': list(self.last_availability.keys())
        }
        
        logger.info(f"Notifying {len(self.subscribers)} subscribers of availability changes")
        
        # In a real implementation, this would send WebSocket messages
        # For now, we'll just log the notification
        logger.info(f"Availability update notification: {notification}")
    
    def subscribe(self, subscriber_id: str):
        """Subscribe to availability updates"""
        self.subscribers.add(subscriber_id)
        logger.info(f"Subscriber {subscriber_id} added. Total subscribers: {len(self.subscribers)}")
    
    def unsubscribe(self, subscriber_id: str):
        """Unsubscribe from availability updates"""
        self.subscribers.discard(subscriber_id)
        logger.info(f"Subscriber {subscriber_id} removed. Total subscribers: {len(self.subscribers)}")
    
    def get_current_availability(self, date_str: str) -> List[str]:
        """Get current availability for a specific date"""
        return self.last_availability.get(date_str, [])
    
    def get_all_availability(self) -> Dict[str, List[str]]:
        """Get all current availability data"""
        return self.last_availability.copy()

# Global instance
realtime_availability_manager = RealTimeAvailabilityManager()

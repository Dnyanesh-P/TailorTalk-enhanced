"""
Enhanced monitoring and metrics for TailorTalk
"""
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
import json
import os
import pytz
import psutil
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_sent_mb: float
    network_recv_mb: float
    process_count: int
    uptime_seconds: float

@dataclass
class ApplicationMetrics:
    """Application-specific metrics"""
    authenticated_users: int
    active_sessions: int
    total_requests: int
    successful_bookings: int
    failed_requests: int
    average_response_time: float
    last_error: Optional[str]
    error_count: int

class MetricsCollector:
    """Collect and store application metrics"""
    
    def __init__(self, timezone_str: str = 'Asia/Kolkata'):
        self.timezone = pytz.timezone(timezone_str)
        self.metrics = defaultdict(list)
        self.counters = defaultdict(int)
        self.timers = {}
        self.recent_events = deque(maxlen=1000)  # Keep last 1000 events
        
        # Performance tracking
        self.response_times = deque(maxlen=100)
        self.error_rates = defaultdict(int)
        
    def record_event(self, event_type: str, details: Dict[str, Any] = None):
        """Record an application event"""
        timestamp = datetime.now(self.timezone)
        event = {
            'type': event_type,
            'timestamp': timestamp.isoformat(),
            'details': details or {}
        }
        
        self.recent_events.append(event)
        self.counters[event_type] += 1
        
        logger.info(f"Event recorded: {event_type}")
    
    def start_timer(self, operation: str) -> str:
        """Start timing an operation"""
        timer_id = f"{operation}_{int(time.time() * 1000)}"
        self.timers[timer_id] = {
            'operation': operation,
            'start_time': time.time(),
            'timestamp': datetime.now(self.timezone)
        }
        return timer_id
    
    def end_timer(self, timer_id: str) -> float:
        """End timing an operation and record the duration"""
        if timer_id not in self.timers:
            return 0.0
        
        timer = self.timers[timer_id]
        duration = time.time() - timer['start_time']
        
        # Record the timing
        self.metrics[f"{timer['operation']}_duration"].append(duration)
        self.response_times.append(duration)
        
        # Clean up
        del self.timers[timer_id]
        
        return duration
    
    def record_error(self, error_type: str, error_message: str):
        """Record an error occurrence"""
        self.error_rates[error_type] += 1
        self.record_event('error', {
            'error_type': error_type,
            'message': error_message
        })
    
    def record_booking_attempt(self, success: bool, details: Dict[str, Any] = None):
        """Record a booking attempt"""
        event_type = 'booking_success' if success else 'booking_failure'
        self.record_event(event_type, details)
    
    def record_api_call(self, endpoint: str, method: str, status_code: int, duration: float):
        """Record API call metrics"""
        self.record_event('api_call', {
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'duration': duration
        })
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics"""
        now = datetime.now(self.timezone)
        
        # Calculate average response time
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        # Get recent events (last hour)
        one_hour_ago = now - timedelta(hours=1)
        recent_events = [
            event for event in self.recent_events
            if datetime.fromisoformat(event['timestamp']) > one_hour_ago
        ]
        
        return {
            'timestamp': now.isoformat(),
            'counters': dict(self.counters),
            'performance': {
                'average_response_time': avg_response_time,
                'total_requests': len(self.response_times),
                'error_rate': sum(self.error_rates.values()) / max(sum(self.counters.values()), 1)
            },
            'recent_activity': {
                'events_last_hour': len(recent_events),
                'recent_events': list(recent_events)[-10:]  # Last 10 events
            },
            'errors': dict(self.error_rates),
            'system_health': self._calculate_health_score()
        }
    
    def _calculate_health_score(self) -> Dict[str, Any]:
        """Calculate system health score"""
        total_events = sum(self.counters.values())
        total_errors = sum(self.error_rates.values())
        
        if total_events == 0:
            error_rate = 0
        else:
            error_rate = total_errors / total_events
        
        # Health score based on error rate and response time
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        health_score = max(0, 100 - (error_rate * 100) - (avg_response_time * 10))
        
        return {
            'score': min(100, max(0, health_score)),
            'error_rate': error_rate,
            'average_response_time': avg_response_time,
            'status': 'healthy' if health_score > 80 else 'degraded' if health_score > 50 else 'unhealthy'
        }
    
    def export_metrics(self, filepath: str):
        """Export metrics to file"""
        try:
            metrics_data = self.get_metrics_summary()
            with open(filepath, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            logger.info(f"Metrics exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")

class PerformanceMonitor:
    """Monitor application performance"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
    
    def monitor_function(self, func_name: str):
        """Decorator to monitor function performance"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                timer_id = self.metrics.start_timer(func_name)
                try:
                    result = func(*args, **kwargs)
                    self.metrics.record_event(f"{func_name}_success")
                    return result
                except Exception as e:
                    self.metrics.record_error(func_name, str(e))
                    raise
                finally:
                    self.metrics.end_timer(timer_id)
            return wrapper
        return decorator
    
    def monitor_api_endpoint(self, endpoint: str):
        """Decorator to monitor API endpoint performance"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    self.metrics.record_api_call(endpoint, 'POST', 200, duration)
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self.metrics.record_api_call(endpoint, 'POST', 500, duration)
                    raise
            return wrapper
        return decorator

class SystemMonitor:
    """Comprehensive system and application monitoring"""
    
    def __init__(self):
        self.start_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        self.metrics_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        
        # Application metrics
        self.app_metrics = ApplicationMetrics(
            authenticated_users=0,
            active_sessions=0,
            total_requests=0,
            successful_bookings=0,
            failed_requests=0,
            average_response_time=0.0,
            last_error=None,
            error_count=0
        )
        
        # Performance tracking
        self.response_times: List[float] = []
        self.max_response_times = 100
        
        logger.info("System monitor initialized")
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system performance metrics"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network stats
            network = psutil.net_io_counters()
            
            # Process count
            process_count = len(psutil.pids())
            
            # Uptime
            uptime = (datetime.now(pytz.timezone('Asia/Kolkata')) - self.start_time).total_seconds()
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_total_mb=memory.total / (1024 * 1024),
                disk_percent=disk.percent,
                disk_used_gb=disk.used / (1024 * 1024 * 1024),
                disk_total_gb=disk.total / (1024 * 1024 * 1024),
                network_sent_mb=network.bytes_sent / (1024 * 1024),
                network_recv_mb=network.bytes_recv / (1024 * 1024),
                process_count=process_count,
                uptime_seconds=uptime
            )
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_total_mb=0.0,
                disk_percent=0.0,
                disk_used_gb=0.0,
                disk_total_gb=0.0,
                network_sent_mb=0.0,
                network_recv_mb=0.0,
                process_count=0,
                uptime_seconds=0.0
            )
    
    def update_app_metrics(self, **kwargs):
        """Update application metrics"""
        for key, value in kwargs.items():
            if hasattr(self.app_metrics, key):
                setattr(self.app_metrics, key, value)
    
    def record_request(self, response_time: float, success: bool = True):
        """Record a request with response time"""
        self.app_metrics.total_requests += 1
        
        if success:
            self.response_times.append(response_time)
            if len(self.response_times) > self.max_response_times:
                self.response_times.pop(0)
            
            # Update average response time
            self.app_metrics.average_response_time = sum(self.response_times) / len(self.response_times)
        else:
            self.app_metrics.failed_requests += 1
    
    def record_booking(self, success: bool = True):
        """Record a booking attempt"""
        if success:
            self.app_metrics.successful_bookings += 1
    
    def record_error(self, error_message: str):
        """Record an error"""
        self.app_metrics.error_count += 1
        self.app_metrics.last_error = error_message
        logger.error(f"Application error recorded: {error_message}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        try:
            system_metrics = self.get_system_metrics()
            current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
            
            # Determine overall health
            health_score = self._calculate_health_score(system_metrics)
            
            if health_score >= 80:
                status = "healthy"
            elif health_score >= 60:
                status = "warning"
            else:
                status = "critical"
            
            return {
                "status": status,
                "health_score": health_score,
                "timestamp": current_time.isoformat(),
                "uptime": str(timedelta(seconds=system_metrics.uptime_seconds)),
                "system": asdict(system_metrics),
                "application": asdict(self.app_metrics),
                "alerts": self._get_alerts(system_metrics),
                "recommendations": self._get_recommendations(system_metrics)
            }
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                "status": "error",
                "health_score": 0,
                "timestamp": datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
                "error": str(e)
            }
    
    def _calculate_health_score(self, metrics: SystemMetrics) -> int:
        """Calculate overall health score (0-100)"""
        score = 100
        
        # CPU usage penalty
        if metrics.cpu_percent > 80:
            score -= 20
        elif metrics.cpu_percent > 60:
            score -= 10
        
        # Memory usage penalty
        if metrics.memory_percent > 90:
            score -= 25
        elif metrics.memory_percent > 75:
            score -= 15
        
        # Disk usage penalty
        if metrics.disk_percent > 95:
            score -= 20
        elif metrics.disk_percent > 85:
            score -= 10
        
        # Error rate penalty
        if self.app_metrics.total_requests > 0:
            error_rate = (self.app_metrics.failed_requests / self.app_metrics.total_requests) * 100
            if error_rate > 10:
                score -= 15
            elif error_rate > 5:
                score -= 10
        
        return max(0, score)
    
    def _get_alerts(self, metrics: SystemMetrics) -> List[str]:
        """Get system alerts"""
        alerts = []
        
        if metrics.cpu_percent > 80:
            alerts.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent > 85:
            alerts.append(f"High memory usage: {metrics.memory_percent:.1f}%")
        
        if metrics.disk_percent > 90:
            alerts.append(f"Low disk space: {metrics.disk_percent:.1f}% used")
        
        if self.app_metrics.error_count > 10:
            alerts.append(f"High error count: {self.app_metrics.error_count} errors")
        
        if self.app_metrics.average_response_time > 5.0:
            alerts.append(f"Slow response time: {self.app_metrics.average_response_time:.2f}s")
        
        return alerts
    
    def _get_recommendations(self, metrics: SystemMetrics) -> List[str]:
        """Get performance recommendations"""
        recommendations = []
        
        if metrics.cpu_percent > 70:
            recommendations.append("Consider scaling up CPU resources")
        
        if metrics.memory_percent > 80:
            recommendations.append("Consider increasing memory allocation")
        
        if metrics.disk_percent > 85:
            recommendations.append("Clean up disk space or expand storage")
        
        if self.app_metrics.average_response_time > 3.0:
            recommendations.append("Optimize application performance")
        
        if self.app_metrics.failed_requests > self.app_metrics.successful_bookings:
            recommendations.append("Investigate and fix recurring errors")
        
        return recommendations
    
    def save_metrics_snapshot(self, filepath: str = "logs/metrics_snapshot.json"):
        """Save current metrics to file"""
        try:
            health_status = self.get_health_status()
            
            with open(filepath, 'w') as f:
                json.dump(health_status, f, indent=2, default=str)
            
            logger.info(f"Metrics snapshot saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving metrics snapshot: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        try:
            current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
            uptime = current_time - self.start_time
            
            return {
                "uptime": str(uptime),
                "total_requests": self.app_metrics.total_requests,
                "successful_bookings": self.app_metrics.successful_bookings,
                "success_rate": (
                    (self.app_metrics.successful_bookings / self.app_metrics.total_requests * 100)
                    if self.app_metrics.total_requests > 0 else 0
                ),
                "average_response_time": self.app_metrics.average_response_time,
                "error_count": self.app_metrics.error_count,
                "authenticated_users": self.app_metrics.authenticated_users,
                "active_sessions": self.app_metrics.active_sessions
            }
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {"error": str(e)}

# Global instances
metrics_collector = MetricsCollector()
performance_monitor = PerformanceMonitor(metrics_collector)
system_monitor = SystemMonitor()

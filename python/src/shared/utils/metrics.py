"""
Metrics collection utilities
"""

import time
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class MetricValue:
    """Individual metric value with timestamp"""
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollectorImpl:
    """
    Simple in-memory metrics collector
    """
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self._lock = Lock()
        
        # Counters: name -> value
        self._counters: Dict[str, float] = defaultdict(float)
        
        # Histograms: name -> list of values
        self._histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        
        # Gauges: name -> current value
        self._gauges: Dict[str, float] = {}
        
        # Tags for metrics
        self._counter_tags: Dict[str, Dict[str, str]] = {}
        self._histogram_tags: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        self._gauge_tags: Dict[str, Dict[str, str]] = {}
    
    def increment_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric"""
        with self._lock:
            self._counters[name] += value
            if tags:
                self._counter_tags[name] = tags
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a value in histogram"""
        with self._lock:
            self._histograms[name].append(MetricValue(
                value=value,
                timestamp=time.time(),
                tags=tags or {}
            ))
            if tags:
                self._histogram_tags[name].append(tags)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge value"""
        with self._lock:
            self._gauges[name] = value
            if tags:
                self._gauge_tags[name] = tags
    
    def get_counter(self, name: str) -> float:
        """Get counter value"""
        with self._lock:
            return self._counters.get(name, 0.0)
    
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics"""
        with self._lock:
            values = [mv.value for mv in self._histograms.get(name, [])]
            
            if not values:
                return {}
            
            values.sort()
            count = len(values)
            
            return {
                "count": count,
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / count,
                "p50": values[int(count * 0.5)] if count > 0 else 0,
                "p90": values[int(count * 0.9)] if count > 0 else 0,
                "p95": values[int(count * 0.95)] if count > 0 else 0,
                "p99": values[int(count * 0.99)] if count > 0 else 0,
            }
    
    def get_gauge(self, name: str) -> Optional[float]:
        """Get gauge value"""
        with self._lock:
            return self._gauges.get(name)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        with self._lock:
            # Get histogram stats
            histogram_stats = {}
            for name in self._histograms:
                histogram_stats[name] = self.get_histogram_stats(name)
            
            return {
                "counters": dict(self._counters),
                "histograms": histogram_stats,
                "gauges": dict(self._gauges),
                "timestamp": time.time()
            }
    
    def reset(self) -> None:
        """Reset all metrics"""
        with self._lock:
            self._counters.clear()
            self._histograms.clear()
            self._gauges.clear()
            self._counter_tags.clear()
            self._histogram_tags.clear()
            self._gauge_tags.clear()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of metrics"""
        with self._lock:
            return {
                "total_counters": len(self._counters),
                "total_histograms": len(self._histograms),
                "total_gauges": len(self._gauges),
                "total_histogram_values": sum(len(h) for h in self._histograms.values()),
                "memory_usage_estimate": self._estimate_memory_usage()
            }
    
    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage in bytes"""
        # Rough estimation
        counter_size = len(self._counters) * 64  # 64 bytes per counter
        gauge_size = len(self._gauges) * 64      # 64 bytes per gauge
        
        histogram_size = 0
        for hist in self._histograms.values():
            histogram_size += len(hist) * 80  # 80 bytes per histogram value
        
        return counter_size + gauge_size + histogram_size


class PerformanceTimer:
    """
    Context manager for timing operations
    """
    
    def __init__(self, metrics_collector: MetricsCollectorImpl, metric_name: str, tags: Optional[Dict[str, str]] = None):
        self.metrics_collector = metrics_collector
        self.metric_name = metric_name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration_ms = (time.time() - self.start_time) * 1000
            self.metrics_collector.record_histogram(
                self.metric_name, 
                duration_ms, 
                self.tags
            )


def time_function(metrics_collector: MetricsCollectorImpl, metric_name: str):
    """
    Decorator to time function execution
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with PerformanceTimer(metrics_collector, metric_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator

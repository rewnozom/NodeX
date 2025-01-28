"""
ai_agent/utils/monitoring.py - System monitoring utilities
"""

import time
import psutil
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

@dataclass
class ResourceUsage:
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_total: int
    disk_used: int
    disk_total: int

@dataclass 
class StateTransition:
    from_state: str
    to_state: str
    timestamp: float
    duration: Optional[float] = None

class Monitor:
    """System resource and state monitoring"""

    def __init__(self, name: str):
        self.name = name
        self.start_time = time.time()
        self.state_history: List[StateTransition] = []
        self.current_state: Optional[str] = None
        self.process = psutil.Process()

    def record_state_change(self, from_state: str, to_state: str):
        """Record a state transition"""
        now = time.time()
        
        # Update duration of previous state
        if self.state_history:
            last_transition = self.state_history[-1]
            if last_transition.duration is None:
                last_transition.duration = now - last_transition.timestamp

        # Add new transition
        self.state_history.append(StateTransition(
            from_state=from_state,
            to_state=to_state, 
            timestamp=now
        ))
        self.current_state = to_state

    def get_resource_usage(self) -> ResourceUsage:
        """Get current resource usage"""
        # CPU
        cpu_percent = self.process.cpu_percent()

        # Memory
        memory = psutil.virtual_memory()
        memory_used = self.process.memory_info().rss
        
        # Disk
        disk = psutil.disk_usage('/')
        
        return ResourceUsage(
            cpu_percent=cpu_percent,
            memory_percent=(memory_used / memory.total) * 100,
            memory_used=memory_used,
            memory_total=memory.total,
            disk_used=disk.used,
            disk_total=disk.total
        )

    def get_state_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics about time spent in each state"""
        stats: Dict[str, Dict[str, float]] = {}
        
        for transition in self.state_history:
            if transition.duration:
                if transition.from_state not in stats:
                    stats[transition.from_state] = {
                        'total_time': 0,
                        'count': 0,
                        'avg_duration': 0
                    }
                
                state_stats = stats[transition.from_state]
                state_stats['total_time'] += transition.duration
                state_stats['count'] += 1
                state_stats['avg_duration'] = (
                    state_stats['total_time'] / state_stats['count']
                )

        return stats

    def get_total_runtime(self) -> float:
        """Get total runtime in seconds"""
        return time.time() - self.start_time

    def get_current_state_duration(self) -> Optional[float]:
        """Get duration of current state"""
        if not self.state_history:
            return None
            
        last_transition = self.state_history[-1]
        return time.time() - last_transition.timestamp

    def reset(self):
        """Reset monitoring state"""
        self.start_time = time.time()
        self.state_history.clear()
        self.current_state = None



"""
ai_agent/utils/monitoring.py - System monitoring and metrics
"""

import asyncio
import psutil
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import deque

@dataclass
class SystemMetrics:
    cpu_percent: float
    memory_used: int
    memory_total: int
    disk_used: int
    disk_total: int
    network_sent: int
    network_recv: int

@dataclass
class AgentMetrics:
    tokens_used: int
    requests_made: int
    avg_response_time: float
    errors: int
    state: str

class MetricsCollector:
    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self.system_metrics = deque(maxlen=history_size)
        self.agent_metrics: Dict[str, deque] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self, interval: float = 1.0):
        """Start metrics collection"""
        self._running = True
        self._task = asyncio.create_task(self._collect_metrics(interval))

    async def stop(self):
        """Stop metrics collection"""
        self._running = False
        if self._task:
            await self._task

    async def _collect_metrics(self, interval: float):
        """Collect system metrics periodically"""
        while self._running:
            try:
                metrics = self._get_system_metrics()
                self.system_metrics.append(metrics)
                await asyncio.sleep(interval)
            except Exception as e:
                print(f"Error collecting metrics: {e}")

    def _get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        return SystemMetrics(
            cpu_percent=psutil.cpu_percent(),
            memory_used=psutil.virtual_memory().used,
            memory_total=psutil.virtual_memory().total,
            disk_used=psutil.disk_usage('/').used,
            disk_total=psutil.disk_usage('/').total,
            network_sent=psutil.net_io_counters().bytes_sent,
            network_recv=psutil.net_io_counters().bytes_recv
        )

    def record_agent_metrics(self, agent_id: str, metrics: AgentMetrics):
        """Record agent-specific metrics"""
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = deque(maxlen=self.history_size)
        self.agent_metrics[agent_id].append(metrics)

    def get_system_metrics(self, 
                        start_time: Optional[float] = None,
                        end_time: Optional[float] = None) -> List[SystemMetrics]:
        """Get system metrics for time range"""
        if not (start_time and end_time):
            return list(self.system_metrics)
            
        return [m for m in self.system_metrics 
                if start_time <= m.timestamp <= end_time]  # type: ignore

    def get_agent_metrics(self,
                       agent_id: str,
                       start_time: Optional[float] = None, 
                       end_time: Optional[float] = None) -> List[AgentMetrics]:
        """Get agent metrics for time range"""
        if agent_id not in self.agent_metrics:
            return []
            
        if not (start_time and end_time):
            return list(self.agent_metrics[agent_id])
            
        return [m for m in self.agent_metrics[agent_id]
                if start_time <= m.timestamp <= end_time]  # type: ignore

class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.checkpoints: Dict[str, float] = {}
        self.measurements: Dict[str, List[float]] = {}

    def checkpoint(self, name: str):
        """Record checkpoint time"""
        self.checkpoints[name] = time.time()

    def measure(self, name: str, start: str, end: str):
        """Measure duration between checkpoints"""
        if start not in self.checkpoints or end not in self.checkpoints:
            return
            
        duration = self.checkpoints[end] - self.checkpoints[start]
        
        if name not in self.measurements:
            self.measurements[name] = []
        self.measurements[name].append(duration)

    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics"""
        stats = {}
        for name, durations in self.measurements.items():
            if durations:
                stats[name] = {
                    'min': min(durations),
                    'max': max(durations),
                    'avg': sum(durations) / len(durations)
                }
        return stats

class ResourceMonitor:
    def __init__(self, process_name: str):
        self.process = self._get_process(process_name)
        self.start_usage = self._get_usage()

    def _get_process(self, name: str) -> Optional[psutil.Process]:
        """Get process by name"""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == name:
                return proc
        return None

    def _get_usage(self) -> Dict[str, float]:
        """Get current resource usage"""
        if not self.process:
            return {}
            
        with self.process.oneshot():
            return {
                'cpu_percent': self.process.cpu_percent(),
                'memory_percent': self.process.memory_percent(),
                'memory_rss': self.process.memory_info().rss,
                'fds': self.process.num_fds(),
                'threads': self.process.num_threads()
            }

    def get_usage_delta(self) -> Dict[str, float]:
        """Get resource usage change"""
        if not self.process:
            return {}
            
        current = self._get_usage()
        return {
            k: current.get(k, 0) - self.start_usage.get(k, 0)
            for k in self.start_usage
        }
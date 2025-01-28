"""
ai_agent/core/agents/state.py - Agent state management
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime

@dataclass
class AgentState:
    """Tracks agent state and metrics"""
    
    current_state: str = "idle"
    last_state: Optional[str] = None
    state_change_time: datetime = field(default_factory=datetime.now)
    total_requests: int = 0
    successful_requests: int = 0
    total_tokens: int = 0
    errors: int = 0
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    task_history: list[str] = field(default_factory=list)
    
    def update_state(self, new_state: str) -> None:
        """Update agent state"""
        self.last_state = self.current_state
        self.current_state = new_state
        self.state_change_time = datetime.now()
        
    def add_task(self, task: str) -> None:
        """Record task in history"""
        self.task_history.append(task)
        self.total_requests += 1
        
    def record_success(self) -> None:
        """Record successful task"""
        self.successful_requests += 1
        
    def record_error(self) -> None:
        """Record task error"""
        self.errors += 1
        
    def add_tokens(self, count: int) -> None:
        """Add to token count"""
        self.total_tokens += count
        
    def update_metric(self, name: str, value: float) -> None:
        """Update performance metric"""
        self.performance_metrics[name] = value
        
    def get_uptime(self) -> float:
        """Get agent uptime in seconds"""
        return (datetime.now() - self.state_change_time).total_seconds()
        
    def get_success_rate(self) -> float:
        """Get task success rate"""
        if self.total_requests == 0:
            return 0
        return self.successful_requests / self.total_requests
        
    def get_state_duration(self) -> float:
        """Get time in current state"""
        return (datetime.now() - self.state_change_time).total_seconds()
        
    def reset(self) -> None:
        """Reset state"""
        self.current_state = "idle"
        self.last_state = None
        self.state_change_time = datetime.now()
        self.total_requests = 0 
        self.successful_requests = 0
        self.total_tokens = 0
        self.errors = 0
        self.performance_metrics.clear()
        self.task_history.clear()
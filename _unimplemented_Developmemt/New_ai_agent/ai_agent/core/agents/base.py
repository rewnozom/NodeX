"""
ai_agent/core/agents/base.py - Base agent class that defines core agent functionality
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from ...utils.rate_limiter import RateLimiter
from ...utils.logging import Logger
from ...utils.monitoring import Monitor
from ...testing.executors.base import TestExecutor

class AgentState(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    ANALYZING = "analyzing"
    IMPLEMENTING = "implementing"
    TESTING = "testing"
    VALIDATING = "validating"
    ERROR = "error"

@dataclass
class AgentConfig:
    name: str
    model_config: Dict[str, Any]
    prompts_dir: str
    memory_dir: str
    knowledge_dir: str
    rate_limiter: Optional[RateLimiter] = None
    test_executor: Optional[TestExecutor] = None

class BaseAgent(ABC):
    """Base agent class that all specialized agents inherit from"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.state = AgentState.IDLE
        self.logger = Logger(self.config.name)
        self.monitor = Monitor(self.config.name)
        self.creation_time = datetime.now()
        self.last_activity = datetime.now()
        self.execution_count = 0
        self._data: Dict[str, Any] = {}
        
        # Initialize tools and executors
        self.test_executor = config.test_executor
        self.rate_limiter = config.rate_limiter

    # Core functionality
    async def initialize(self) -> None:
        """Initialize agent state and resources"""
        try:
            await self._initialize_resources()
            await self._load_prompts()
            if self.rate_limiter:
                await self.rate_limiter.cleanup()
            self.logger.info(f"Agent {self.config.name} initialized")
        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}")
            self.state = AgentState.ERROR
            raise

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing loop for handling tasks"""
        try:
            self.last_activity = datetime.now()
            self.execution_count += 1

            # Pre-processing hooks
            await self._pre_process(input_data)
            
            # Core processing logic
            result = await self._process_implementation(input_data)
            
            # Post-processing hooks
            await self._post_process(result)
            
            return result

        except Exception as e:
            self.logger.error(f"Processing error: {str(e)}")
            self.state = AgentState.ERROR
            raise

    # State management
    def set_state(self, new_state: AgentState) -> None:
        """Update agent state with monitoring"""
        old_state = self.state
        self.state = new_state
        self.monitor.record_state_change(old_state, new_state)
        self.logger.info(f"State changed: {old_state} -> {new_state}")

    # Data storage
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get stored data by key"""
        return self._data.get(key, default)

    def set_data(self, key: str, value: Any) -> None:
        """Store data by key"""
        self._data[key] = value

    # Test execution
    async def execute_test(self, test_code: str, **kwargs) -> Dict[str, Any]:
        """Execute test code using configured executor"""
        if not self.test_executor:
            raise ValueError("No test executor configured")
            
        self.logger.info(f"Executing test: {test_code[:100]}...")
        result = await self.test_executor.execute(test_code, **kwargs)
        return result

    # Abstract methods that must be implemented
    @abstractmethod
    async def _initialize_resources(self) -> None:
        """Initialize agent-specific resources"""
        pass

    @abstractmethod 
    async def _load_prompts(self) -> None:
        """Load agent-specific prompts"""
        pass

    @abstractmethod
    async def _pre_process(self, input_data: Dict[str, Any]) -> None:
        """Pre-process input data"""
        pass

    @abstractmethod
    async def _process_implementation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Core processing implementation"""
        pass

    @abstractmethod
    async def _post_process(self, result: Dict[str, Any]) -> None:
        """Post-process results"""
        pass

    # Cleanup
    async def cleanup(self) -> None:
        """Cleanup agent resources"""
        if self.rate_limiter:
            await self.rate_limiter.cleanup()
        self.logger.info(f"Agent {self.config.name} cleaned up")
"""
ai_agent/testing/executors/base.py - Base test executor interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ExecutionResult:
    success: bool
    output: str
    error: Optional[str] = None
    return_code: int = 0
    execution_time: float = 0.0
    memory_usage: float = 0.0
    
class TestExecutor(ABC):
    """Base class for test execution environments"""
    
    def __init__(self, working_dir: str):
        self.working_dir = working_dir
        self.last_result: Optional[ExecutionResult] = None

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the execution environment"""
        pass

    @abstractmethod
    async def execute(self, code: str, **kwargs) -> ExecutionResult:
        """Execute code in the environment"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup execution environment"""
        pass

    async def validate_environment(self) -> bool:
        """Validate that the execution environment is working"""
        try:
            # Run a simple test
            result = await self.execute("print('test')")
            return result.success and "test" in result.output
        except Exception:
            return False

    def get_last_result(self) -> Optional[ExecutionResult]:
        """Get the last execution result"""
        return self.last_result
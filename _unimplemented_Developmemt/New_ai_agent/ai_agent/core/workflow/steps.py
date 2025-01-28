"""
ai_agent/core/workflow/steps.py - Workflow step implementations
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable, Awaitable
from ..agents.base import BaseAgent

@dataclass
class WorkflowStep:
    name: str
    agent: BaseAgent
    inputs: Dict[str, Any]
    condition: Optional[Callable[..., bool]] = None
    on_success: Optional[Callable[..., Awaitable[None]]] = None
    on_failure: Optional[Callable[..., Awaitable[None]]] = None
    max_retries: int = 3
    timeout: int = 300
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class StepExecutor:
    @staticmethod
    async def execute(step: WorkflowStep) -> bool:
        """Execute workflow step"""
        retries = 0
        while retries <= step.max_retries:
            try:
                if step.condition and not step.condition(step.inputs):
                    return True

                result = await step.agent.process(step.inputs)
                step.output = result

                if step.on_success:
                    await step.on_success(result)
                    
                return True

            except Exception as e:
                retries += 1
                step.error = str(e)
                
                if step.on_failure:
                    await step.on_failure(e)
                    
                if retries > step.max_retries:
                    return False

class StepBuilder:
    """Fluent builder for workflow steps"""
    
    def __init__(self, name: str, agent: BaseAgent):
        self.step = WorkflowStep(
            name=name,
            agent=agent,
            inputs={}
        )

    def with_inputs(self, inputs: Dict[str, Any]) -> 'StepBuilder':
        self.step.inputs = inputs
        return self

    def with_condition(self, condition: Callable[..., bool]) -> 'StepBuilder':
        self.step.condition = condition
        return self

    def with_success_handler(self, handler: Callable[..., Awaitable[None]]) -> 'StepBuilder':
        self.step.on_success = handler
        return self

    def with_failure_handler(self, handler: Callable[..., Awaitable[None]]) -> 'StepBuilder':
        self.step.on_failure = handler
        return self

    def with_retries(self, retries: int) -> 'StepBuilder':
        self.step.max_retries = retries
        return self

    def with_timeout(self, timeout: int) -> 'StepBuilder':
        self.step.timeout = timeout
        return self

    def build(self) -> WorkflowStep:
        return self.step
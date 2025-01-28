"""
ai_agent/core/workflow/manager.py - Workflow management system
"""

import asyncio
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
from ..agents.base import BaseAgent

class WorkflowState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class WorkflowStep:
    name: str
    agent: BaseAgent
    inputs: Dict[str, Any]
    outputs: Optional[Dict[str, Any]] = None
    state: WorkflowState = WorkflowState.PENDING
    error: Optional[str] = None

class WorkflowManager:
    def __init__(self):
        self.steps: List[WorkflowStep] = []
        self.current_step: Optional[WorkflowStep] = None
        self.state = WorkflowState.PENDING
        self._cancel = False

    def add_step(self, name: str, agent: BaseAgent, inputs: Dict[str, Any]) -> None:
        """Add workflow step"""
        self.steps.append(WorkflowStep(
            name=name,
            agent=agent,
            inputs=inputs
        ))

    async def execute(self) -> Dict[str, Any]:
        """Execute workflow"""
        try:
            self.state = WorkflowState.RUNNING
            results = {}

            for step in self.steps:
                if self._cancel:
                    self.state = WorkflowState.CANCELLED
                    break

                self.current_step = step
                step.state = WorkflowState.RUNNING

                try:
                    # Process previous outputs
                    inputs = self._process_inputs(step, results)
                    
                    # Execute step
                    step.outputs = await step.agent.process(inputs)
                    
                    # Store results
                    results[step.name] = step.outputs
                    step.state = WorkflowState.COMPLETED

                except Exception as e:
                    step.state = WorkflowState.FAILED
                    step.error = str(e)
                    self.state = WorkflowState.FAILED
                    raise

            self.state = WorkflowState.COMPLETED
            return results

        except Exception as e:
            self.state = WorkflowState.FAILED
            raise

    def cancel(self) -> None:
        """Cancel workflow execution"""
        self._cancel = True

    def get_status(self) -> Dict[str, Any]:
        """Get workflow status"""
        return {
            "state": self.state.value,
            "current_step": self.current_step.name if self.current_step else None,
            "steps": [
                {
                    "name": step.name,
                    "state": step.state.value,
                    "error": step.error
                }
                for step in self.steps
            ]
        }

    def _process_inputs(self, step: WorkflowStep, results: Dict[str, Any]) -> Dict[str, Any]:
        """Process step inputs"""
        processed = {}
        
        for key, value in step.inputs.items():
            if isinstance(value, str) and value.startswith("$"):
                # Reference to previous output
                ref_step, ref_key = value[1:].split(".")
                if ref_step not in results:
                    raise ValueError(f"Referenced step {ref_step} not found")
                if ref_key not in results[ref_step]:
                    raise ValueError(f"Referenced key {ref_key} not found in step {ref_step}")
                processed[key] = results[ref_step][ref_key]
            else:
                processed[key] = value
                
        return processed

class DevelopmentWorkflow:
    """Standard development workflow"""
    
    def __init__(self, 
                 architect: BaseAgent,
                 developer: BaseAgent,
                 judge: BaseAgent):
        self.workflow = WorkflowManager()
        self.architect = architect
        self.developer = developer
        self.judge = judge

    def setup(self, requirements: List[str], constraints: List[str]) -> None:
        """Setup development workflow"""
        # Architecture design
        self.workflow.add_step(
            name="design",
            agent=self.architect,
            inputs={
                "requirements": requirements,
                "constraints": constraints
            }
        )

        # Implementation
        self.workflow.add_step(
            name="implement",
            agent=self.developer,
            inputs={
                "design": "$design.api_specs",
                "requirements": requirements
            }
        )

        # Validation
        self.workflow.add_step(
            name="validate",
            agent=self.judge,
            inputs={
                "code": "$implement.code",
                "tests": "$implement.tests",
                "requirements": requirements
            }
        )

    async def execute(self) -> Dict[str, Any]:
        """Execute development workflow"""
        return await self.workflow.execute()

    def get_status(self) -> Dict[str, Any]:
        """Get workflow status"""
        return self.workflow.get_status()
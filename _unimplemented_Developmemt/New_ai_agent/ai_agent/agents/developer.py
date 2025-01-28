"""
ai_agent/agents/developer.py - Developer agent implementation
"""

from typing import Dict, Any, List, Optional
from ..core.agents.base import BaseAgent, AgentConfig, AgentState
from ..testing.executors.base import TestExecutor
from dataclasses import dataclass

@dataclass
class Task:
    name: str
    description: str
    requirements: List[str]
    tests: Optional[str] = None
    code: Optional[str] = None

class DeveloperAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.current_task: Optional[Task] = None
        self.test_first = True
        self.auto_fix = True

    async def _initialize_resources(self) -> None:
        """Initialize development resources"""
        pass

    async def _load_prompts(self) -> None:
        """Load development prompts"""
        pass

    async def _pre_process(self, input_data: Dict[str, Any]) -> None:
        """Prepare for development task"""
        self.set_state(AgentState.PLANNING)
        
        # Create task from input
        self.current_task = Task(
            name=input_data.get('name', 'task'),
            description=input_data['description'],
            requirements=input_data.get('requirements', []),
            tests=input_data.get('tests'),
            code=input_data.get('code')
        )

    async def _process_implementation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Implement the development task"""
        if not self.current_task:
            raise ValueError("No task set")

        try:
            # Test-driven development flow
            if self.test_first and not self.current_task.tests:
                self.set_state(AgentState.ANALYZING)
                tests = await self._create_tests()
                self.current_task.tests = tests

            # Implementation
            self.set_state(AgentState.IMPLEMENTING)
            implementation = await self._implement_solution()
            self.current_task.code = implementation

            # Testing
            self.set_state(AgentState.TESTING)
            test_results = await self._run_tests()

            # Auto-fix if needed
            if self.auto_fix and not test_results['success']:
                fixed_implementation = await self._fix_implementation(test_results)
                if fixed_implementation:
                    self.current_task.code = fixed_implementation

            return {
                'task': self.current_task.name,
                'tests': self.current_task.tests,
                'implementation': self.current_task.code,
                'test_results': test_results
            }

        except Exception as e:
            self.set_state(AgentState.ERROR)
            raise

    async def _post_process(self, result: Dict[str, Any]) -> None:
        """Handle development results"""
        if result['test_results']['success']:
            self.set_state(AgentState.VALIDATING)
        else:
            self.set_state(AgentState.ERROR)

    async def _create_tests(self) -> str:
        """Create test cases from requirements"""
        prompt = self._create_test_prompt()
        response = await self._get_model_response(prompt)
        return self._extract_code(response)

    async def _implement_solution(self) -> str:
        """Implement solution"""
        prompt = self._create_implementation_prompt()
        response = await self._get_model_response(prompt)
        return self._extract_code(response)

    async def _run_tests(self) -> Dict[str, Any]:
        """Run tests on implementation"""
        if not self.test_executor:
            raise ValueError("No test executor configured")

        if not (self.current_task and self.current_task.tests and self.current_task.code):
            raise ValueError("Missing tests or implementation")

        # Combine implementation and tests
        full_code = f"{self.current_task.code}\n\n{self.current_task.tests}"
        
        # Execute tests
        result = await self.test_executor.execute(full_code)
        
        return {
            'success': result.success,
            'output': result.output,
            'error': result.error
        }

    async def _fix_implementation(self, test_results: Dict[str, Any]) -> Optional[str]:
        """Fix failed implementation"""
        if not (self.current_task and self.current_task.code):
            return None

        prompt = self._create_fix_prompt(test_results)
        response = await self._get_model_response(prompt)
        fixed_code = self._extract_code(response)

        # Verify fix
        self.current_task.code = fixed_code
        new_results = await self._run_tests()
        
        if new_results['success']:
            return fixed_code
        return None

    def _create_test_prompt(self) -> str:
        """Create prompt for test generation"""
        if not self.current_task:
            raise ValueError("No task set")
            
        return f"""Create pytest test cases for the following requirements:
Requirements:
{self._format_requirements()}

The tests should:
- Cover all requirements
- Include edge cases
- Use pytest fixtures where appropriate
- Follow test isolation principles
- Include clear assertions

Return only the test code without explanation."""

    def _create_implementation_prompt(self) -> str:
        """Create prompt for implementation"""
        if not self.current_task:
            raise ValueError("No task set")
            
        prompt = f"""Implement a solution for the following task:
Description: {self.current_task.description}

Requirements:
{self._format_requirements()}"""

        if self.current_task.tests:
            prompt += f"\n\nTests:\n{self.current_task.tests}"

        prompt += "\n\nReturn only the implementation code without explanation."
        return prompt

    def _create_fix_prompt(self, test_results: Dict[str, Any]) -> str:
        """Create prompt for fixing implementation"""
        if not (self.current_task and self.current_task.code):
            raise ValueError("No task set")
            
        return f"""Fix the following implementation to pass the tests:

Implementation:
{self.current_task.code}

Test Results:
{test_results['error']}

Tests:
{self.current_task.tests}

Return only the fixed implementation code without explanation."""

    def _format_requirements(self) -> str:
        """Format requirements list"""
        if not self.current_task:
            return ""
        return "\n".join(f"- {req}" for req in self.current_task.requirements)

    async def _get_model_response(self, prompt: str) -> str:
        """Get response from LLM"""
        response = ""
        async for chunk in self.config.model.chat([
            {"role": "system", "content": "You are an expert Python developer."},
            {"role": "user", "content": prompt}
        ]):
            response += chunk
        return response

    def _extract_code(self, response: str) -> str:
        """Extract code from model response"""
        # Remove markdown code blocks if present
        code = response.strip()
        if code.startswith("```") and code.endswith("```"):
            code = code[code.index("\n")+1:code.rindex("```")]
        return code.strip()
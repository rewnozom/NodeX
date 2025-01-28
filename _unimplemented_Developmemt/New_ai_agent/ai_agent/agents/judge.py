# ai_agent/agents/judge.py
"""
ai_agent/agents/judge.py - Quality control and validation agent
"""

from typing import Dict, Any, List
from ..core.agents.base import BaseAgent, AgentConfig, AgentState
from ..testing.validators import CodeValidator, TestValidator, ValidationResult
from dataclasses import dataclass

@dataclass
class ValidationResult:
    passed: bool
    score: float
    issues: List[str]
    recommendations: List[str]

class JudgeAgent(BaseAgent):
    """Agent responsible for quality control and validation"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.code_validator = CodeValidator()
        self.test_validator = TestValidator()
        self.quality_thresholds = {
            'code_complexity': 10,  # Adjusted key name for clarity
            'code_duplication': 0.1,
            'test_coverage': 0.8
        }

    async def _initialize_resources(self) -> None:
        """Load quality checking resources"""
        await self.code_validator.initialize()
        await self.test_validator.initialize()

    async def _load_prompts(self) -> None:
        """Load judge-specific prompts"""
        # TODO: Implement prompt loading
        pass

    async def _pre_process(self, input_data: Dict[str, Any]) -> None:
        """Prepare for validation"""
        self.set_state(AgentState.ANALYZING)
        
        # Extract validation targets
        self.code = input_data.get('code', '')
        self.tests = input_data.get('tests', '')
        self.requirements = input_data.get('requirements', [])

    async def _process_implementation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run validation checks"""
        try:
            # Validate code quality
            code_result = await self._validate_code()

            # Validate tests
            test_result = await self._validate_tests()

            # Check requirements coverage
            req_result = await self._validate_requirements()

            # Generate feedback
            feedback = await self._generate_feedback(
                code_result, test_result, req_result
            )

            return {
                'passed': all(r.passed for r in [code_result, test_result, req_result]),
                'code_validation': code_result,
                'test_validation': test_result, 
                'requirements_validation': req_result,
                'feedback': feedback
            }

        except Exception as e:
            self.set_state(AgentState.ERROR)
            raise

    async def _post_process(self, result: Dict[str, Any]) -> None:
        """Handle validation results"""
        if result['passed']:
            self.set_state(AgentState.VALIDATING)
        else:
            # Request changes if needed
            await self._request_changes(result)

    async def _validate_code(self) -> ValidationResult:
        """Validate code quality"""
        # Run static analysis
        analysis = await self.code_validator.analyze(self.code)
        
        # Check metrics against thresholds
        passed = (
            analysis.complexity <= self.quality_thresholds['code_complexity'] and
            analysis.duplication <= self.quality_thresholds['code_duplication']
        )

        issues = []
        if analysis.complexity > self.quality_thresholds['code_complexity']:
            issues.append(f"Code complexity {analysis.complexity} exceeds threshold ({self.quality_thresholds['code_complexity']})")
        if analysis.duplication > self.quality_thresholds['code_duplication']:
            issues.append(f"Code duplication {analysis.duplication*100:.1f}% exceeds threshold ({self.quality_thresholds['code_duplication']*100}%)")

        return ValidationResult(
            passed=passed,
            score=analysis.quality_score,
            issues=issues,
            recommendations=analysis.recommendations
        )

    async def _validate_tests(self) -> ValidationResult:
        """Validate test quality and coverage"""
        test_analysis = await self.test_validator.analyze(
            self.code, self.tests
        )
        
        passed = (
            test_analysis.coverage >= self.quality_thresholds['test_coverage']
        )

        issues = []
        if test_analysis.coverage < self.quality_thresholds['test_coverage']:
            issues.append(
                f"Test coverage {test_analysis.coverage*100:.1f}% below threshold ({self.quality_thresholds['test_coverage']*100}%)"
            )

        return ValidationResult(
            passed=passed,
            score=test_analysis.quality_score,
            issues=issues,
            recommendations=test_analysis.recommendations
        )

    async def _validate_requirements(self) -> ValidationResult:
        """Validate requirements coverage"""
        # TODO: Implement requirements validation
        return ValidationResult(
            passed=True,
            score=1.0,
            issues=[],
            recommendations=[]
        )

    async def _generate_feedback(
        self,
        code_result: ValidationResult,
        test_result: ValidationResult,
        req_result: ValidationResult
    ) -> str:
        """Generate detailed feedback"""
        messages = []

        # Add issues
        for result in [code_result, test_result, req_result]:
            messages.extend(result.issues)

        # Add recommendations 
        for result in [code_result, test_result, req_result]:
            messages.extend(result.recommendations)

        return "\n".join(messages)

    async def _request_changes(self, result: Dict[str, Any]) -> None:
        """Request changes based on validation results"""
        # TODO: Implement change requests
        pass

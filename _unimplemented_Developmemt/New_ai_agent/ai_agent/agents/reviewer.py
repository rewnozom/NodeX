"""
ai_agent/agents/reviewer.py - Code reviewer agent implementation
"""
import json
from typing import Dict, List, Any
from ..core.agents.base import BaseAgent, AgentConfig, AgentState
from dataclasses import dataclass

@dataclass
class ReviewResult:
    issues: List[str]
    suggestions: List[str]
    code_quality_score: float
    maintainability_score: float
    security_score: float

class ReviewerAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.review_history = []

    async def _process_implementation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.set_state(AgentState.ANALYZING)
        
        code = input_data["code"]
        review_type = input_data.get("review_type", "general")
        
        # Analyze code
        result = await self._analyze_code(code, review_type)
        
        # Generate detailed review
        review_result = await self._generate_review(code, result)
        
        self.review_history.append(review_result)
        return {
            "issues": review_result.issues,
            "suggestions": review_result.suggestions,
            "scores": {
                "quality": review_result.code_quality_score,
                "maintainability": review_result.maintainability_score,
                "security": review_result.security_score
            }
        }

    async def _analyze_code(self, code: str, review_type: str) -> Dict[str, Any]:
        prompt = self._create_analysis_prompt(code, review_type)
        analysis = await self._get_model_response(prompt)
        return self._parse_analysis(analysis)

    async def _generate_review(self, code: str, analysis: Dict[str, Any]) -> ReviewResult:
        prompt = self._create_review_prompt(code, analysis)
        response = await self._get_model_response(prompt)
        return self._parse_review_result(response)

    def _create_analysis_prompt(self, code: str, review_type: str) -> str:
        return f"""Analyze this code focusing on {review_type}:
Code:
{code}

Analyze the following aspects:
1. Code structure and organization
2. Best practices adherence
3. Potential bugs or issues
4. Security concerns
5. Performance implications

Return analysis in JSON format."""

    def _create_review_prompt(self, code: str, analysis: Dict[str, Any]) -> str:
        return f"""Generate detailed code review based on analysis:
Analysis: {json.dumps(analysis, indent=2)}

Code:
{code}

Provide:
1. List of issues
2. Improvement suggestions
3. Quality scores (0-1)

Return in JSON format."""

    def _parse_analysis(self, analysis: str) -> Dict[str, Any]:
        return json.loads(analysis)

    def _parse_review_result(self, review: str) -> ReviewResult:
        data = json.loads(review)
        return ReviewResult(
            issues=data["issues"],
            suggestions=data["suggestions"],
            code_quality_score=data["scores"]["quality"],
            maintainability_score=data["scores"]["maintainability"],
            security_score=data["scores"]["security"]
        )
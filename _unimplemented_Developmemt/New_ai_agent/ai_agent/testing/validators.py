# ai_agent/testing/validators/validators.py
"""
ai_agent/testing/validators/validators.py - Code and Test Validators
"""
import os
import ast
import asyncio
import json
import tempfile
import subprocess
from dataclasses import dataclass
from typing import List, Dict, Any
import radon.complexity as radon
from pylint import epylint as lint
import coverage

@dataclass
class CodeAnalysis:
    complexity: float
    duplication: float
    maintainability: float
    quality_score: float
    issues: List[str]
    recommendations: List[str]

@dataclass
class TestAnalysis:
    coverage: float
    quality_score: float
    issues: List[str]
    recommendations: List[str]

class CodeValidator:
    """Validates code quality and style"""

    async def initialize(self):
        """Initialize validator"""
        # Initialize any resources if needed
        self.pylint_opts = [
            '--output-format=json',
            '--disable=C0111',  # Missing docstring
            '--disable=C0103',  # Invalid name
            '--disable=C0301',  # Line too long
        ]

    async def analyze(self, code: str) -> CodeAnalysis:
        """Analyze code quality"""
        results = await asyncio.gather(
            self._check_complexity(code),
            self._check_duplication(code),
            self._run_pylint(code),
            self._check_maintainability(code)
        )

        complexity, duplication, pylint_issues, maintainability = results

        # Collect issues and recommendations
        issues = []
        recommendations = []

        # Add pylint issues
        for issue in pylint_issues:
            issues.append(f"Line {issue.get('line', 'N/A')}: {issue.get('message', 'No message')}")
            if 'symbol' in issue:
                recommendations.append(f"{issue['symbol']}: {issue.get('message', '')}")

        # Example: Add more rules based on analysis
        if complexity > 10:
            issues.append(f"Code complexity {complexity} exceeds threshold (10)")
            recommendations.append("Refactor code to reduce complexity.")

        if duplication > 0.1:
            issues.append(f"Code duplication {duplication*100:.1f}% exceeds threshold (10%)")
            recommendations.append("Remove duplicated code.")

        # Calculate overall quality score
        quality_score = self._calculate_quality_score(
            complexity, duplication, maintainability, len(issues)
        )

        return CodeAnalysis(
            complexity=complexity,
            duplication=duplication,
            maintainability=maintainability,
            quality_score=quality_score,
            issues=issues,
            recommendations=recommendations
        )

    async def _check_complexity(self, code: str) -> float:
        """Calculate code complexity using Radon"""
        try:
            complexity = radon.cc_visit(code)
            if complexity:
                average_complexity = sum(cc.complexity for cc in complexity) / len(complexity)
                return average_complexity
            return 0.0
        except Exception as e:
            return float('inf')

    async def _check_duplication(self, code: str) -> float:
        """Check for code duplication"""
        # This is a placeholder. Implement actual duplication checking if needed.
        # For demonstration, we'll return 0.0 indicating no duplication.
        return 0.0

    async def _run_pylint(self, code: str) -> List[Dict[str, Any]]:
        """Run pylint on the provided code"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name

            # Run pylint as a subprocess
            cmd = ['pylint', temp_file_path] + self.pylint_opts
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Parse JSON output
            pylint_output = process.stdout.strip()
            if pylint_output:
                issues = json.loads(pylint_output)
                return issues
            return []
        except Exception as e:
            return []
        finally:
            # Clean up the temporary file
            try:
                os.remove(temp_file_path)
            except:
                pass

    async def _check_maintainability(self, code: str) -> float:
        """Check code maintainability using Radon's Maintainability Index"""
        try:
            mi = radon.mi_visit(code, multi=True)
            if mi:
                average_mi = sum(mi.values()) / len(mi)
                return average_mi
            return 100.0
        except:
            return 0.0

    def _calculate_quality_score(
        self,
        complexity: float,
        duplication: float,
        maintainability: float,
        issue_count: int
    ) -> float:
        """Calculate overall quality score"""
        # Convert metrics to 0-1 scale
        complexity_score = max(0, 1 - (complexity / 15))  # Assuming max complexity of 15
        duplication_score = 1 - duplication  # Assuming duplication is between 0 and 1
        maintainability_score = maintainability / 100  # Maintainability is out of 100
        issues_score = max(0, 1 - (issue_count / 10))  # Assuming max 10 issues

        # Weight and combine scores
        weights = {
            'complexity': 0.3,
            'duplication': 0.2,
            'maintainability': 0.3,
            'issues': 0.2
        }

        score = (
            complexity_score * weights['complexity'] +
            duplication_score * weights['duplication'] +
            maintainability_score * weights['maintainability'] +
            issues_score * weights['issues']
        )

        return max(0, min(1, score))  # Ensure score is between 0 and 1

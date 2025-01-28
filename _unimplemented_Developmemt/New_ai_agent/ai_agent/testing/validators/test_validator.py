# ai_agent/testing/validators/test_validator.py
"""
ai_agent/testing/validators/test_validator.py - Test validation implementation
"""

import os
import ast
import pytest
import coverage
import tempfile  # Added import
import subprocess  # Added import
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from ai_agent.testing.validators import TestAnalysis  # Updated import

@dataclass
class TestMetrics:
    total_tests: int
    assertions: int
    complexity: float
    coverage: float

class TestValidator:
    async def analyze(self, code: str, tests: str) -> TestAnalysis:
        """Analyze test quality and coverage"""
        
        metrics = await self._collect_metrics(code, tests)
        quality_issues = await self._check_quality(tests)
        coverage_report = await self._measure_coverage(code, tests)

        issues = []
        recommendations = []

        # Analyze metrics
        if metrics.assertions / metrics.total_tests < 2:
            issues.append("Low assertion density")
            recommendations.append("Add more assertions per test")

        if metrics.complexity > 3:
            issues.append("High test complexity")
            recommendations.append("Simplify test cases")

        if metrics.coverage < 0.8:
            issues.append(f"Low coverage: {metrics.coverage*100:.1f}%")
            recommendations.append("Add tests for uncovered code paths")

        # Add quality issues
        issues.extend(quality_issues)

        # Calculate score
        quality_score = self._calculate_quality_score(metrics, len(quality_issues))

        return TestAnalysis(
            coverage=metrics.coverage,
            quality_score=quality_score,
            issues=issues,
            recommendations=recommendations
        )

    async def _collect_metrics(self, code: str, tests: str) -> TestMetrics:
        """Collect test metrics"""
        tree = ast.parse(tests)
        
        # Count tests and assertions
        test_count = 0
        assertion_count = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                test_count += 1
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Call):
                        if (isinstance(subnode.func, ast.Name) and 
                            subnode.func.id.startswith('assert_')):
                            assertion_count += 1
                        elif (isinstance(subnode.func, ast.Attribute) and 
                              subnode.func.attr.startswith('assert_')):
                            assertion_count += 1

        # Calculate complexity
        complexity = self._calculate_test_complexity(tree)
        
        # Measure coverage
        coverage_data = await self._measure_coverage(code, tests)
        
        return TestMetrics(
            total_tests=test_count,
            assertions=assertion_count,
            complexity=complexity,
            coverage=coverage_data
        )

    async def _check_quality(self, tests: str) -> List[str]:
        """Check test quality issues"""
        issues = []
        tree = ast.parse(tests)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                # Check test function length
                if len(node.body) > 20:
                    issues.append(f"Test {node.name} is too long")

                # Check for test isolation
                if self._has_shared_state(node):
                    issues.append(f"Test {node.name} may have shared state")

                # Check for multiple assertions
                assertions = self._count_assertions(node)
                if assertions == 0:
                    issues.append(f"Test {node.name} has no assertions")
                elif assertions > 5:
                    issues.append(f"Test {node.name} has too many assertions")

        return issues

    def _calculate_test_complexity(self, tree: ast.AST) -> float:
        """Calculate test complexity"""
        complexity = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
        return complexity

    def _has_shared_state(self, node: ast.AST) -> bool:
        """Check for shared state usage"""
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.Name):
                if subnode.id.startswith(('global_', 'shared_')):
                    return True
        return False

    def _count_assertions(self, node: ast.AST) -> int:
        """Count assertions in node"""
        count = 0
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.Call):
                if (isinstance(subnode.func, ast.Name) and 
                    subnode.func.id.startswith('assert_')):
                    count += 1
                elif (isinstance(subnode.func, ast.Attribute) and 
                      subnode.func.attr.startswith('assert_')):
                    count += 1
        return count

    async def _measure_coverage(self, code: str, tests: str) -> float:
        """Measure test coverage"""
        # Initialize coverage
        cov = coverage.Coverage(source=["ai_agent"])
        cov.start()

        # Write code and tests to temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as code_file:
            code_file.write(code)
            code_file_path = code_file.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as test_file:
            test_file.write(tests)
            test_file_path = test_file.name

        try:
            # Run pytest on the test file
            result = subprocess.run(
                ['pytest', test_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Stop coverage
            cov.stop()
            cov.save()

            # Calculate coverage
            coverage_percent = cov.report()

            return coverage_percent / 100  # Convert to 0-1 scale

        except Exception as e:
            return 0.0
        finally:
            # Clean up temporary files
            try:
                os.remove(code_file_path)
                os.remove(test_file_path)
            except:
                pass

    def _calculate_quality_score(self, metrics: TestMetrics, issue_count: int) -> float:
        """Calculate overall test quality score"""
        # Coverage score (0-0.4)
        coverage_score = 0.4 * metrics.coverage

        # Assertion density score (0-0.2)  
        assertion_ratio = min(1.0, metrics.assertions / (metrics.total_tests * 2))
        assertion_score = 0.2 * assertion_ratio

        # Complexity score (0-0.2)
        complexity_score = 0.2 * max(0, 1 - (metrics.complexity / 10))

        # Issues score (0-0.2)
        issues_score = 0.2 * max(0, 1 - (issue_count / 5))

        return coverage_score + assertion_score + complexity_score + issues_score

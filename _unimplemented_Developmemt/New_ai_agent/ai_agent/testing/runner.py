# ai_agent/testing/runner.py
"""
ai_agent/testing/runner.py - Test execution and management
"""

import asyncio
import pytest
import coverage
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import json
import sys
import os

@dataclass
class TestResult:
    passed: bool
    tests_run: int
    tests_passed: int
    test_coverage: float
    execution_time: float
    error_messages: List[str]
    coverage_report: Dict[str, Any]

class TestRunner:
    def __init__(self, work_dir: str):
        self.work_dir = Path(work_dir)
        self.cov = coverage.Coverage()
        self.cov.start()

    async def run_tests(self, code: str, tests: str) -> TestResult:
        """Run tests with coverage"""
        try:
            # Write code and tests to temp files
            code_file = self.work_dir / "test_target.py"
            test_file = self.work_dir / "test_cases.py"

            code_file.write_text(code)
            test_file.write_text(tests)

            # Start coverage
            self.cov.start()

            # Run tests
            test_output = await self._run_pytest(test_file)

            # Stop coverage
            self.cov.stop()
            self.cov.save()

            # Generate coverage report
            coverage_data = self._generate_coverage_report()

            return TestResult(
                passed=test_output["passed"],
                tests_run=test_output["total"],
                tests_passed=test_output["passed_tests"],
                test_coverage=coverage_data["total_coverage"],
                execution_time=test_output["duration"],
                error_messages=test_output["errors"],
                coverage_report=coverage_data
            )

        except Exception as e:
            # Handle exceptions
            print(f"Error while running tests: {e}")
            raise

        finally:
            # Cleanup
            self.cov.erase()
            if code_file.exists():
                code_file.unlink()
            if test_file.exists():
                test_file.unlink()

    async def _run_pytest(self, test_file: Path) -> Dict[str, Any]:
        """Run pytest and capture JSON report"""
        report_path = self.work_dir / "report.json"

        # Ensure the report file does not exist before running tests
        if report_path.exists():
            report_path.unlink()

        # Run pytest with JSON reporting
        exit_code = pytest.main([
            "-v",
            "--tb=short",
            "--json-report",
            f"--json-report-file={report_path}",
            str(test_file)
        ])

        # Check if the report was generated
        if not report_path.exists():
            return {
                "passed": False,
                "total": 0,
                "passed_tests": 0,
                "duration": 0.0,
                "errors": ["No report generated."]
            }

        # Read and parse the JSON report
        with open(report_path, 'r') as f:
            report = json.load(f)

        total = report.get("summary", {}).get("total", 0)
        passed = report.get("summary", {}).get("passed", 0)
        duration = report.get("duration", 0.0)
        errors = [test.get("nodeid") for test in report.get("tests", []) if test.get("outcome") == "failed"]

        # Clean up the report file
        report_path.unlink()

        return {
            "passed": exit_code == 0,
            "total": total,
            "passed_tests": passed,
            "duration": duration,
            "errors": errors
        }

    def _generate_coverage_report(self) -> Dict[str, Any]:
        """Generate coverage report"""
        # Analyze coverage
        self.cov.load()
        total = self.cov.report()

        # Generate detailed report
        report = {}
        for filename in self.cov.get_data().measured_files():
            file_coverage = self.cov.analysis2(filename)
            report[filename] = {
                "total_coverage": file_coverage[0],
                "missing_lines": file_coverage[1],
                "excluded_lines": file_coverage[2]
            }

        return {
            "total_coverage": total,
            "files": report
        }

    async def run_performance_test(self, code: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run performance tests"""
        try:
            # Write code to file
            code_file = self.work_dir / "perf_target.py"
            code_file.write_text(code)

            results = {}
            for test in test_cases:
                # Run performance test
                result = await self._run_perf_test(
                    code_file,
                    test["input"],
                    test.get("iterations", 100)
                )
                results[test["name"]] = result

            return results

        finally:
            if code_file.exists():
                code_file.unlink()

    async def _run_perf_test(
        self,
        code_file: Path,
        test_input: Any,
        iterations: int
    ) -> Dict[str, float]:
        """Run single performance test"""
        import cProfile
        import pstats
        import time
        import importlib.util

        # Import test module
        spec = importlib.util.spec_from_file_location(
            "test_module", code_file
        )
        if not spec or not spec.loader:
            raise ImportError("Could not load test module")
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Setup profiler
        pr = cProfile.Profile()
        pr.enable()

        # Run test
        start_time = time.time()
        for _ in range(iterations):
            module.main(test_input)  # type: ignore
        duration = time.time() - start_time

        # Get profiler stats
        pr.disable()
        stats = pstats.Stats(pr)

        return {
            "avg_duration": duration / iterations,
            "total_calls": stats.total_calls,
            "primitive_calls": stats.prim_calls
        }

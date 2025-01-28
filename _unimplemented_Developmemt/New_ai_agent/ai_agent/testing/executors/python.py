"""
ai_agent/testing/executors/python.py - Python code executor
"""

import sys
import ast
import time
import asyncio
from io import StringIO
from typing import Optional
import psutil
from .base import TestExecutor, ExecutionResult

class PythonExecutor(TestExecutor):
    def __init__(self, working_dir: str):
        super().__init__(working_dir)
        self.globals = {}
        self.locals = {}

    async def execute(self, code: str, timeout: int = 30, **kwargs) -> ExecutionResult:
        start_time = time.time()
        try:
            # Validate code
            ast.parse(code)
            
            # Capture output
            stdout = StringIO()
            stderr = StringIO()
            sys.stdout = stdout
            sys.stderr = stderr

            # Execute code
            start_memory = psutil.Process().memory_info().rss
            
            try:
                exec(code, self.globals, self.locals)
                success = True
                error = None
            except Exception as e:
                success = False
                error = str(e)

            end_memory = psutil.Process().memory_info().rss
            execution_time = time.time() - start_time

            return ExecutionResult(
                success=success,
                output=stdout.getvalue(),
                error=error or stderr.getvalue(),
                return_code=0 if success else 1,
                execution_time=execution_time,
                memory_usage=(end_memory - start_memory) / 1024 / 1024  # MB
            )

        except SyntaxError as e:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Syntax error: {str(e)}",
                return_code=1,
                execution_time=time.time() - start_time,
                memory_usage=0.0
            )

        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

    async def validate_environment(self) -> bool:
        """Validate Python environment"""
        try:
            result = await self.execute("print('test')")
            return result.success and "test" in result.output
        except Exception:
            return False
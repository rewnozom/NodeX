"""
ai_agent/testing/executors/terminal.py - Terminal-based code execution
"""

import os
import asyncio
import time
import subprocess
import psutil
from typing import Optional, Dict, Any

from .base import TestExecutor, ExecutionResult
from ...utils.shell import ShellSession

class TerminalExecutor(TestExecutor):
    """Execute code and commands in a terminal environment"""

    def __init__(self, working_dir: str, shell_cmd: str = None):
        super().__init__(working_dir)
        self.shell_cmd = shell_cmd or os.environ.get("SHELL", "/bin/bash")
        self.session: Optional[ShellSession] = None
        self.current_process: Optional[subprocess.Popen] = None

    async def initialize(self) -> None:
        """Initialize shell session"""
        if not self.session:
            self.session = ShellSession()
            await self.session.start(self.shell_cmd)
            # Change to working directory
            await self.session.execute(f"cd {self.working_dir}")

    async def execute(self, code: str, timeout: int = 30, **kwargs) -> ExecutionResult:
        """Execute code in terminal"""
        if not self.session:
            await self.initialize()

        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss

        try:
            # Execute command
            output, error, return_code = await self.session.execute(
                code, 
                timeout=timeout
            )

            execution_time = time.time() - start_time
            memory_used = (psutil.Process().memory_info().rss - start_memory) / 1024 / 1024

            result = ExecutionResult(
                success=(return_code == 0),
                output=output,
                error=error,
                return_code=return_code,
                execution_time=execution_time,
                memory_usage=memory_used
            )

        except asyncio.TimeoutError:
            result = ExecutionResult(
                success=False,
                output="",
                error=f"Execution timed out after {timeout} seconds",
                return_code=-1,
                execution_time=timeout,
                memory_usage=0.0
            )
            await self._kill_current_process()

        except Exception as e:
            result = ExecutionResult(
                success=False,
                output="",
                error=str(e),
                return_code=-1,
                execution_time=time.time() - start_time,
                memory_usage=0.0
            )

        self.last_result = result
        return result

    async def cleanup(self) -> None:
        """Cleanup shell session"""
        if self.session:
            await self.session.stop()
            self.session = None

    async def _kill_current_process(self) -> None:
        """Kill the currently running process"""
        if self.current_process:
            try:
                if self.current_process.poll() is None:
                    self.current_process.kill()
                    self.current_process.wait()
            except Exception:
                pass
            finally:
                self.current_process = None
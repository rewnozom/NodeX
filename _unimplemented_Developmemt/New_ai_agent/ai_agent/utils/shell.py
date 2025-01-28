"""
ai_agent/utils/shell.py - Shell interaction utilities
"""

import asyncio
import os
import sys
import time
import shlex
from typing import Tuple, Optional
import pty
import select
import re
import signal

class ShellSession:
    """Manages an interactive shell session"""

    def __init__(self):
        self.master_fd: Optional[int] = None
        self.slave_fd: Optional[int] = None
        self.process: Optional[asyncio.subprocess.Process] = None
        self._read_buffer = bytearray()
        self._last_command_output = ""

    async def start(self, shell_cmd: str = "/bin/bash") -> None:
        """Start a new shell session"""
        # Create pseudo-terminal
        self.master_fd, self.slave_fd = pty.openpty()

        # Start shell process
        self.process = await asyncio.create_subprocess_exec(
            shell_cmd,
            stdin=self.slave_fd,
            stdout=self.slave_fd,
            stderr=self.slave_fd,
            preexec_fn=os.setsid  # Create new process group
        )

        # Wait for shell to initialize
        await self._read_until_prompt()

    async def execute(self, command: str, timeout: int = 30) -> Tuple[str, str, int]:
        """Execute a command and return output, error and return code"""
        if not self.process or not self.master_fd:
            raise RuntimeError("Shell session not initialized")

        try:
            # Clear read buffer
            self._read_buffer.clear()
            
            # Send command with newline
            command = command.strip() + "\n"
            os.write(self.master_fd, command.encode())

            # Read output until prompt returns
            output = await asyncio.wait_for(
                self._read_until_prompt(),
                timeout=timeout
            )

            # Extract return code
            os.write(self.master_fd, b"echo $?\n")
            rc_output = await self._read_until_prompt() 
            try:
                return_code = int(rc_output.splitlines()[0])
            except (ValueError, IndexError):
                return_code = -1

            # Clean up command echo and prompt
            output_lines = output.splitlines()[1:-1]
            clean_output = "\n".join(output_lines)

            return clean_output, "", return_code

        except asyncio.TimeoutError:
            error = f"Command timed out after {timeout} seconds"
            return "", error, -1
        except Exception as e:
            return "", str(e), -1

    async def stop(self) -> None:
        """Stop the shell session"""
        if self.process:
            try:
                # Send SIGTERM to process group
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                await self.process.wait()
            except ProcessLookupError:
                pass
            self.process = None

        if self.master_fd:
            os.close(self.master_fd)
            self.master_fd = None
        if self.slave_fd:
            os.close(self.slave_fd)
            self.slave_fd = None

    async def _read_until_prompt(self) -> str:
        """Read output until shell prompt is found"""
        if not self.master_fd:
            raise RuntimeError("Shell session not initialized")

        # Pattern matching common shell prompts
        prompt_pattern = re.compile(rb'[>$#] $')
        
        while True:
            # Wait for data or timeout
            r, _, _ = select.select([self.master_fd], [], [], 0.1)
            if not r:
                await asyncio.sleep(0.1)
                continue

            # Read available data
            try:
                data = os.read(self.master_fd, 1024)
                self._read_buffer.extend(data)
            except OSError:
                break

            # Check for prompt
            if prompt_pattern.search(self._read_buffer):
                break

        output = self._read_buffer.decode(errors='replace')
        return output

    def __del__(self):
        """Cleanup on deletion"""
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            except:
                pass
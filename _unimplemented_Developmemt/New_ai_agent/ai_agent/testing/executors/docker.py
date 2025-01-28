"""
ai_agent/testing/executors/docker.py - Docker-based code execution
"""

import os
import docker
import time
from typing import Optional, Dict, Any
from docker.models.containers import Container

from .base import TestExecutor, ExecutionResult

class DockerExecutor(TestExecutor):
    """Execute code inside a Docker container"""

    def __init__(
        self, 
        working_dir: str,
        image: str,
        container_name: Optional[str] = None,
        ports: Optional[Dict[str, int]] = None,
        volumes: Optional[Dict[str, Dict[str, str]]] = None,
        environment: Optional[Dict[str, str]] = None
    ):
        super().__init__(working_dir)
        self.image = image
        self.container_name = container_name
        self.ports = ports or {}
        self.volumes = volumes or {}
        self.environment = environment or {}
        self.client = docker.from_env()
        self.container: Optional[Container] = None

    async def initialize(self) -> None:
        """Initialize Docker container"""
        try:
            # Check if container exists
            if self.container_name:
                containers = self.client.containers.list(
                    all=True,
                    filters={"name": self.container_name}
                )
                if containers:
                    self.container = containers[0]
                    if self.container.status != "running":
                        self.container.start()
                    return

            # Create new container
            self.container = self.client.containers.run(
                self.image,
                name=self.container_name,
                detach=True,
                ports=self.ports,
                volumes=self.volumes,
                environment=self.environment,
                working_dir="/workspace"
            )

        except Exception as e:
            raise RuntimeError(f"Failed to initialize Docker container: {str(e)}")

    async def execute(self, code: str, timeout: int = 30, **kwargs) -> ExecutionResult:
        """Execute code in Docker container"""
        if not self.container:
            await self.initialize()

        start_time = time.time()
        try:
            # Write code to file
            code_file = os.path.join(self.working_dir, "_temp_code.py")
            with open(code_file, "w") as f:
                f.write(code)

            # Execute in container
            exec_id = self.container.exec_run(  # type: ignore
                f"python /workspace/_temp_code.py",
                workdir="/workspace",
                stream=True
            )

            # Collect output with timeout
            output = []
            error = None
            for chunk in exec_id.output:  # type: ignore
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Execution timed out after {timeout} seconds")
                output.append(chunk.decode())

            execution_time = time.time() - start_time
            success = exec_id.exit_code == 0  # type: ignore
            
            result = ExecutionResult(
                success=success,
                output="".join(output),
                error=error,
                return_code=exec_id.exit_code,  # type: ignore
                execution_time=execution_time,
                memory_usage=0.0  # TODO: Add memory tracking
            )

        except TimeoutError as e:
            result = ExecutionResult(
                success=False,
                output="",
                error=str(e),
                return_code=-1,
                execution_time=timeout,
                memory_usage=0.0
            )

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
        """Cleanup Docker container"""
        if self.container:
            try:
                self.container.stop()
                self.container.remove()
            except:
                pass
            self.container = None
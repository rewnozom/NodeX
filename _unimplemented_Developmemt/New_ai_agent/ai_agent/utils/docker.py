# ai_agent/utils/docker.py
"""
ai_agent/utils/docker.py - Docker utilities
"""

import docker
from typing import Optional, Dict, List, Union

def get_docker_client() -> docker.DockerClient:
    """Get a Docker client instance"""
    return docker.from_env()

def run_container(
    image: str,
    command: Optional[Union[str, List[str]]] = None,
    **kwargs
) -> docker.models.containers.Container:
    """Run a Docker container and return the container instance"""
    client = get_docker_client()
    return client.containers.run(image, command=command, **kwargs)

def list_containers(
    filters: Optional[Dict[str, Union[str, List[str]]]] = None,
    all: bool = False
) -> List[docker.models.containers.Container]:
    """List Docker containers based on filters"""
    client = get_docker_client()
    return client.containers.list(filters=filters, all=all)

def container_logs(
    container: Union[str, docker.models.containers.Container],
    **kwargs
) -> str:
    """Get the logs of a Docker container"""
    client = get_docker_client()
    if isinstance(container, str):
        container = client.containers.get(container)
    return container.logs(**kwargs).decode('utf-8')
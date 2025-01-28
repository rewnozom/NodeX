"""
ai_agent/config/settings.py - Project configuration system
"""

from typing import Dict, Any, Optional
from pathlib import Path
import yaml
import os
from dataclasses import dataclass

@dataclass
class AgentConfig:
    name: str
    model_name: str
    temperature: float
    max_tokens: int
    stop_sequences: list[str]
    timeout: int

@dataclass
class TestConfig:
    timeout: int
    max_retries: int
    coverage_threshold: float
    performance_threshold: float

@dataclass
class SystemConfig:
    work_dir: Path
    log_level: str
    max_memory: int
    max_processes: int

class Config:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """Load all config files"""
        config_files = [
            "agents.yml",
            "testing.yml", 
            "system.yml"
        ]

        for file in config_files:
            path = self.config_dir / file
            if path.exists():
                with open(path) as f:
                    self.config.update(yaml.safe_load(f))

        # Override with environment variables
        self._load_env_vars()

    def _load_env_vars(self):
        """Load config from environment variables"""
        prefix = "AI_AGENT_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                self.config[config_key] = value

    def get_agent_config(self, agent_name: str) -> AgentConfig:
        """Get agent configuration"""
        if agent_name not in self.config.get("agents", {}):
            raise ValueError(f"No configuration for agent: {agent_name}")

        agent_config = self.config["agents"][agent_name]
        return AgentConfig(
            name=agent_name,
            model_name=agent_config["model_name"],
            temperature=float(agent_config.get("temperature", 0.7)),
            max_tokens=int(agent_config.get("max_tokens", 2000)),
            stop_sequences=agent_config.get("stop_sequences", []),
            timeout=int(agent_config.get("timeout", 30))
        )

    def get_test_config(self) -> TestConfig:
        """Get test configuration"""
        test_config = self.config.get("testing", {})
        return TestConfig(
            timeout=int(test_config.get("timeout", 30)),
            max_retries=int(test_config.get("max_retries", 3)),
            coverage_threshold=float(test_config.get("coverage_threshold", 0.8)),
            performance_threshold=float(test_config.get("performance_threshold", 0.9))
        )

    def get_system_config(self) -> SystemConfig:
        """Get system configuration"""
        sys_config = self.config.get("system", {})
        return SystemConfig(
            work_dir=Path(sys_config.get("work_dir", "work")),
            log_level=sys_config.get("log_level", "INFO"),
            max_memory=int(sys_config.get("max_memory", 1024)),
            max_processes=int(sys_config.get("max_processes", 4))
        )

    def save(self):
        """Save current configuration"""
        config_by_file = {
            "agents.yml": {"agents": self.config.get("agents", {})},
            "testing.yml": {"testing": self.config.get("testing", {})},
            "system.yml": {"system": self.config.get("system", {})}
        }

        for filename, config in config_by_file.items():
            path = self.config_dir / filename
            with open(path, "w") as f:
                yaml.safe_dump(config, f, default_flow_style=False)
#!/usr/bin/env python3
# ai_agent/agents/base_agent.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    Provides common functionality and interface requirements for all agents.
    """
    def __init__(self, config: Dict[str, Any], model: Optional[Any] = None):
        """
        Initialize the base agent.

        Args:
            config (Dict[str, Any]): Agent configuration dictionary
            model (Optional[Any]): Language model instance
        """
        self.config = config or {}
        self.model = model
        self.is_active = False
        self.last_activity = None
        self.error_count = 0
        self.max_retries = self.config.get('max_retries', 3)
        self._initialize_agent()

    def _initialize_agent(self) -> None:
        """Initialize agent-specific settings from configuration."""
        try:
            # Set basic agent properties from config
            self.name = self.config.get('name', self.__class__.__name__)
            self.version = self.config.get('version', '1.0.0')
            self.description = self.config.get('description', 'Base agent implementation')
            logger.debug(f"Initialized agent: {self.name} (v{self.version})")
        except Exception as e:
            logger.error(f"Error initializing agent {self.__class__.__name__}: {e}")
            raise

    @abstractmethod
    def process_message(self, messages: List[Dict[str, str]]) -> str:
        """
        Process a message using the agent's logic.
        
        Args:
            messages (List[Dict[str, str]]): List of message dictionaries with 'role' and 'content'
            
        Returns:
            str: The agent's response
            
        Raises:
            ValueError: If messages are invalid
            RuntimeError: If processing fails
        """
        pass

    def activate(self) -> bool:
        """
        Activate the agent.
        
        Returns:
            bool: True if activation was successful
        """
        try:
            self.is_active = True
            self.last_activity = datetime.now()
            logger.info(f"Agent {self.name} activated")
            return True
        except Exception as e:
            logger.error(f"Failed to activate agent {self.name}: {e}")
            return False

    def deactivate(self) -> bool:
        """
        Deactivate the agent.
        
        Returns:
            bool: True if deactivation was successful
        """
        try:
            self.is_active = False
            self.last_activity = datetime.now()
            logger.info(f"Agent {self.name} deactivated")
            return True
        except Exception as e:
            logger.error(f"Failed to deactivate agent {self.name}: {e}")
            return False

    @property
    def is_running(self) -> bool:
        """Check if the agent is currently active."""
        return self.is_active

    @property
    def status(self) -> Dict[str, Any]:
        """Get the current status of the agent."""
        return {
            "is_active": self.is_active,
            "last_activity": self.last_activity,
            "error_count": self.error_count,
            "model_loaded": self.model is not None
        }

    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        Update the agent's configuration.
        
        Args:
            new_config (Dict[str, Any]): New configuration to apply
            
        Returns:
            bool: True if update was successful
        """
        try:
            self.config.update(new_config)
            self._initialize_agent()
            logger.info(f"Configuration updated for agent {self.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to update config for agent {self.name}: {e}")
            return False

    def reset(self) -> bool:
        """
        Reset the agent to its initial state.
        
        Returns:
            bool: True if reset was successful
        """
        try:
            self.is_active = False
            self.last_activity = None
            self.error_count = 0
            logger.info(f"Agent {self.name} reset to initial state")
            return True
        except Exception as e:
            logger.error(f"Failed to reset agent {self.name}: {e}")
            return False

    @abstractmethod
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about the agent for display purposes.
        
        Returns:
            Dict[str, Any]: Dictionary containing agent information
        """
        pass

    def validate_messages(self, messages: List[Dict[str, str]]) -> bool:
        """
        Validate message format.
        
        Args:
            messages (List[Dict[str, str]]): Messages to validate
            
        Returns:
            bool: True if messages are valid
            
        Raises:
            ValueError: If message format is invalid
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        for msg in messages:
            if not isinstance(msg, dict):
                raise ValueError(f"Invalid message format: {msg}")
            if 'role' not in msg or 'content' not in msg:
                raise ValueError(f"Message missing required fields: {msg}")
            if not isinstance(msg['role'], str) or not isinstance(msg['content'], str):
                raise ValueError(f"Invalid field types in message: {msg}")
        
        return True

    def handle_error(self, error: Exception) -> None:
        """
        Handle agent errors.
        
        Args:
            error (Exception): The error that occurred
        """
        self.error_count += 1
        logger.error(f"Agent {self.name} encountered error: {error}")
        if self.error_count >= self.max_retries:
            logger.critical(f"Agent {self.name} exceeded max retries ({self.max_retries})")
            self.deactivate()
import logging
from typing import Dict, Type, Any, Optional, List
from pathlib import Path
from .base_agent import BaseAgent
from .chat_agent import ChatAgent
from .developer_agent import DeveloperAgent
from .crew_agent import CrewAIAgent

logger = logging.getLogger(__name__)

class AgentFactory:
    """Factory class for creating and managing different types of agents"""
    
    _agents: Dict[str, Type[BaseAgent]] = {}
    _initialized: bool = False
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialize()

    @classmethod
    def _initialize(cls) -> None:
        """Initialize agent registry with available agents"""
        if cls._initialized:
            return

        try:
            # Register all available agents
            cls._agents = {
                "chat": ChatAgent,
                "developer": DeveloperAgent,
                "crew": CrewAIAgent
            }
            logger.debug(f"Registered agents: {list(cls._agents.keys())}")
        except Exception as e:
            logger.error(f"Failed to register agents: {e}")
            raise

        cls._initialized = True

    @classmethod
    def register_agent(cls, name: str, agent_class: Type[BaseAgent]) -> None:
        """
        Register a new agent type
        
        Args:
            name: Identifier for the agent type
            agent_class: Agent class to register
        """
        if not cls._initialized:
            cls._initialize()
            
        if not issubclass(agent_class, BaseAgent):
            raise TypeError(f"Agent class must inherit from BaseAgent")
            
        cls._agents[name] = agent_class
        logger.debug(f"Successfully registered agent: {name}")

    @classmethod
    def unregister_agent(cls, name: str) -> None:
        """
        Remove an agent type from registry
        
        Args:
            name: Agent type identifier to remove
        """
        if name in cls._agents:
            del cls._agents[name]
            logger.debug(f"Unregistered agent: {name}")

    @classmethod
    def create_agent(cls, agent_type: str, config: Dict[str, Any], model: Optional[Any] = None) -> BaseAgent:
        """
        Create an instance of the specified agent type
        
        Args:
            agent_type: Type of agent to create
            config: Configuration dictionary for the agent
            model: Optional language model instance
            
        Returns:
            Instantiated agent of requested type
        """
        if not cls._initialized:
            cls._initialize()

        if agent_type not in cls._agents:
            available = list(cls._agents.keys())
            raise ValueError(f"Unknown agent type: {agent_type}. Available types: {available}")

        try:
            agent = cls._agents[agent_type](config, model)
            agent.activate()
            logger.debug(f"Successfully created agent of type: {agent_type}")
            return agent
        except Exception as e:
            logger.error(f"Failed to create agent {agent_type}: {e}")
            raise

    @classmethod
    def create_agents(cls, agent_types: List[str], config: Dict[str, Any], model: Optional[Any] = None) -> List[BaseAgent]:
        """
        Create multiple agents
        
        Args:
            agent_types: List of agent types to create
            config: Configuration dictionary for the agents
            model: Optional language model instance
            
        Returns:
            List of instantiated agents
        """
        return [cls.create_agent(agent_type, config, model) for agent_type in agent_types]

    @classmethod
    def get_available_agents(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all registered agent types
        
        Returns:
            Dictionary mapping agent names to their information
        """
        if not cls._initialized:
            cls._initialize()

        available_agents = {}
        for name, agent_class in cls._agents.items():
            try:
                # Create temporary instance to get info
                agent = agent_class(config={}, model=None)
                agent_info = agent.get_agent_info()
                agent_info['available'] = True
                available_agents[name] = agent_info
            except Exception as e:
                logger.error(f"Failed to get info for agent {name}: {e}")
                available_agents[name] = {
                    "name": name,
                    "error": str(e),
                    "available": False
                }
        
        return available_agents

    @classmethod
    def validate_agent_config(cls, agent_type: str, config: Dict[str, Any]) -> bool:
        """
        Validate configuration for an agent type
        
        Args:
            agent_type: Agent type to validate config for
            config: Configuration to validate
            
        Returns:
            True if configuration is valid
        """
        if agent_type not in cls._agents:
            raise ValueError(f"Unknown agent type: {agent_type}")
            
        try:
            # Create temporary agent to validate config
            agent = cls._agents[agent_type](config, None)
            return True
        except Exception as e:
            logger.error(f"Invalid configuration for {agent_type}: {e}")
            return False

    @classmethod
    def reset(cls) -> None:
        """Reset the factory to uninitialized state"""
        cls._agents.clear()
        cls._initialized = False
        cls._instance = None
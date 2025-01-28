# ai_agent/agents/agent_factory.py

import logging
from typing import Dict, Type, Any, Optional
from .base_agent import BaseAgent
from .chat_agent import ChatAgent

logger = logging.getLogger(__name__)

class AgentFactory:
    """
    Factory class for creating and managing different types of agents
    """
    _agents: Dict[str, Type[BaseAgent]] = {}
    _initialized: bool = False

    @classmethod
    def _initialize(cls) -> None:
        """Initialize agent registry with available agents"""
        if cls._initialized:
            return

        # Register basic chat agent
        try:
            cls._agents["chat"] = ChatAgent
            logger.debug("Registered chat agent successfully")
        except Exception as e:
            logger.error(f"Failed to register chat agent: {e}")

        # Try to register CrewAI agent if available
        try:
            from .crew_agent import CrewAIAgent
            cls._agents["crew"] = CrewAIAgent
            logger.debug("Registered CrewAI agent successfully")
        except ImportError:
            logger.warning("CrewAI not available - crew agent features will be disabled")
        except Exception as e:
            logger.error(f"Failed to register CrewAI agent: {e}")

        # Try to register Developer agent if available
        try:
            from .developer_agent import DeveloperAgent
            cls._agents["developer"] = DeveloperAgent
            logger.debug("Registered Developer agent successfully")
        except ImportError:
            logger.warning("Developer agent dependencies not available - developer features will be disabled")
        except Exception as e:
            logger.error(f"Failed to register Developer agent: {e}")

        cls._initialized = True
        logger.info(f"Agent factory initialized with agents: {list(cls._agents.keys())}")

    @classmethod
    def register_agent(cls, name: str, agent_class: Type[BaseAgent]) -> None:
        """Register a new agent type"""
        try:
            if not cls._initialized:
                cls._initialize()
            cls._agents[name] = agent_class
            logger.debug(f"Successfully registered agent: {name}")
        except Exception as e:
            logger.error(f"Failed to register agent {name}: {e}")
            raise

    @classmethod
    def create_agent(cls, agent_type: str, config: Dict[str, Any], model: Optional[Any] = None) -> BaseAgent:
        """Create an instance of the specified agent type"""
        if not cls._initialized:
            cls._initialize()

        try:
            if agent_type not in cls._agents:
                logger.error(f"Unknown agent type requested: {agent_type}")
                raise ValueError(f"Unknown agent type: {agent_type}")

            agent = cls._agents[agent_type](config, model)
            logger.debug(f"Successfully created agent of type: {agent_type}")
            return agent
        except Exception as e:
            logger.error(f"Failed to create agent {agent_type}: {e}")
            raise

    @classmethod
    def get_available_agents(cls) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered agent types"""
        if not cls._initialized:
            cls._initialize()

        try:
            available_agents = {}
            for name, agent_class in cls._agents.items():
                try:
                    agent_info = agent_class(config={}, model=None).get_agent_info()
                    available_agents[name] = agent_info
                except Exception as e:
                    logger.error(f"Failed to get info for agent {name}: {e}")
                    available_agents[name] = {
                        "name": name,
                        "error": str(e),
                        "available": False
                    }
            return available_agents
        except Exception as e:
            logger.error(f"Failed to get available agents: {e}")
            return {}

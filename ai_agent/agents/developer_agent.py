# ai_agent/agents/developer_agent.py

import logging
from typing import List, Dict, Any, Optional
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Try to import CrewAI dependencies
try:
    from crewai import Agent, Task, Crew, Process
    CREWAI_AVAILABLE = True
    logger.debug("CrewAI dependencies loaded successfully")
except ImportError:
    CREWAI_AVAILABLE = False
    logger.warning("CrewAI not available, developer agent will run in limited mode")
    # Create dummy classes to prevent errors
    class Agent:
        def __init__(self, *args, **kwargs): pass
    class Task:
        def __init__(self, *args, **kwargs): pass
    class Crew:
        def __init__(self, *args, **kwargs): pass
        def kickoff(self): return "CrewAI not available - operation not supported"

class DeveloperAgent(BaseAgent):
    """Developer agent implementation that manages software development workflows"""
    
    def __init__(self, config: Dict[str, Any], model: Any = None):
        if not CREWAI_AVAILABLE:
            logger.warning("Initializing DeveloperAgent without CrewAI support")
        super().__init__(config, model)
        self.name = "Developer Agent"
        self.description = "Multi-agent system for software development"
        self.current_workflow = None
        self.team_initialized = False
        self.initialize_team()

    def initialize_team(self) -> None:
        """Initialize the development team with specialized roles"""
        if not CREWAI_AVAILABLE:
            logger.warning("Team initialization skipped - CrewAI not available")
            return

        try:
            # Initialize team members
            self.architect = Agent(
                role='Software Architect',
                goal='Design and maintain system architecture',
                backstory="Expert software architect with deep knowledge of patterns and practices.",
                verbose=True,
                allow_delegation=True,
                llm=self.model
            )

            self.developer = Agent(
                role='Developer',
                goal='Implement features and fix bugs',
                backstory="Skilled developer with expertise in clean code practices.",
                verbose=True,
                allow_delegation=True,
                llm=self.model
            )

            self.reviewer = Agent(
                role='Code Reviewer',
                goal='Review code and ensure quality',
                backstory="Meticulous code reviewer focused on quality and security.",
                verbose=True,
                allow_delegation=True,
                llm=self.model
            )

            self.team_initialized = True
            logger.info("Development team initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing development team: {e}")
            self.team_initialized = False

    def set_workflow(self, workflow_name: str) -> bool:
        """Set the current workflow"""
        if not CREWAI_AVAILABLE:
            logger.warning("Cannot set workflow - CrewAI not available")
            return False

        try:
            agent_config = self.config.get("AGENT_PROFILES", {}).get("developer", {})
            all_workflows = agent_config.get("config", {}).get("workflows", {})

            if workflow_name not in all_workflows:
                logger.warning(f"Invalid or missing workflow: {workflow_name}")
                return False
            if not all_workflows[workflow_name].get("enabled", True):
                logger.warning(f"Workflow '{workflow_name}' is disabled.")
                return False

            self.current_workflow = workflow_name
            logger.info(f"Workflow set to: {workflow_name}")
            return True
        except Exception as e:
            logger.error(f"Error setting workflow: {e}")
            return False

    def process_message(self, messages: List[Dict[str, str]]) -> str:
        """Process a message using the current workflow"""
        if not CREWAI_AVAILABLE:
            return "Developer agent features are not available - CrewAI is required"

        if not self.team_initialized:
            return "Development team not properly initialized"

        if not self.current_workflow:
            return "Please select a workflow first using set_workflow()"

        try:
            user_message = messages[-1]['content']
            workflow_config = self._get_workflow_config()  # <--- new local method

            # Create tasks for each workflow step
            tasks = []
            for step in workflow_config["steps"]:
                task = self._create_task_for_step(step, user_message)
                if task:
                    tasks.append(task)

            if not tasks:
                return "No valid tasks created for the current workflow"

            # Execute the workflow
            crew = Crew(
                agents=[self.architect, self.developer, self.reviewer],
                tasks=tasks,
                verbose=True
            )

            result = crew.kickoff()
            logger.info(f"Workflow {self.current_workflow} completed successfully")
            return result

        except Exception as e:
            error_msg = f"Error in workflow processing: {e}"
            logger.error(error_msg)
            return f"Error during execution: {str(e)}"

    def _get_workflow_config(self) -> Dict[str, Any]:
        """
        Helper to retrieve the developer workflow data from config.
        Raises an Exception if missing or disabled.
        """
        agent_config = self.config.get("AGENT_PROFILES", {}).get("developer", {})
        workflows = agent_config.get("config", {}).get("workflows", {})

        if self.current_workflow not in workflows:
            raise ValueError(f"Workflow '{self.current_workflow}' not found in developer config")

        wf_data = workflows[self.current_workflow]
        if not wf_data.get("enabled", False):
            raise ValueError(f"Workflow '{self.current_workflow}' is disabled")

        return wf_data


    def _create_task_for_step(self, step: str, context: str) -> Optional[Task]:
        """Create a specific task based on the workflow step"""
        if not self.team_initialized:
            return None

        task_configs = {
            'analysis': {
                'agent': self.architect,
                'description': f"Analyze request and provide architectural insights: {context}"
            },
            'planning': {
                'agent': self.architect,
                'description': f"Create implementation plan for: {context}"
            },
            'implementation': {
                'agent': self.developer,
                'description': f"Implement solution based on plan: {context}"
            },
            'review': {
                'agent': self.reviewer,
                'description': f"Review implementation and provide feedback: {context}"
            },
            'testing': {
                'agent': self.developer,
                'description': f"Create and execute tests for: {context}"
            },
            'documentation': {
                'agent': self.developer,
                'description': f"Create documentation for: {context}"
            },
            'suggestions': {
                'agent': self.reviewer,
                'description': f"Provide improvement suggestions for: {context}"
            },
            'reproduction': {
                'agent': self.developer,
                'description': f"Reproduce and analyze bug: {context}"
            },
            'fixing': {
                'agent': self.developer,
                'description': f"Implement bug fix for: {context}"
            }
        }

        try:
            if step in task_configs:
                config = task_configs[step]
                return Task(
                    description=config['description'],
                    agent=config['agent']
                )
            else:
                logger.warning(f"Unknown workflow step: {step}")
                return None
        except Exception as e:
            logger.error(f"Error creating task for step {step}: {e}")
            return None

    def get_agent_info(self) -> Dict[str, Any]:
        """Return agent information"""
        return {
            "name": self.name,
            "description": self.description,
            "type": "developer",
            "capabilities": [
                "code-review",
                "feature-development",
                "bug-fixing",
                "refactoring"
            ],
            "is_active": self.is_active,
            "current_workflow": self.current_workflow,
            "team_members": [
                "Software Architect",
                "Developer",
                "Code Reviewer"
            ],
            "crewai_available": CREWAI_AVAILABLE,
            "team_initialized": self.team_initialized
        }
# ai_agent/agents/crew_agent.py

#!/usr/bin/env python3
# ai_agent/agents/crew_agent.py

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Try to import CrewAI dependencies
try:
    from crewai import Agent as CrewAgent, Task, Crew, Process
    CREWAI_AVAILABLE = True
    logger.debug("CrewAI dependencies loaded successfully")
except ImportError:
    CREWAI_AVAILABLE = False
    logger.warning("CrewAI not available, crew agent will run in limited mode")

    # Dummy classes if `crewai` isn't installed:
    class CrewAgent:
        def __init__(self, *args, **kwargs): pass

    class Task:
        def __init__(self, *args, **kwargs): pass

    class Crew:
        def __init__(self, *args, **kwargs): pass

        def kickoff(self): return "CrewAI not available - operation not supported"

    class Process:
        sequential = "sequential"
        parallel = "parallel"


class CrewAgentError(Exception):
    """Base exception class for crew agent errors"""
    pass


class WorkflowError(CrewAgentError):
    """Raised when there are workflow-related errors"""
    pass


class AgentInitializationError(CrewAgentError):
    """Raised when agent initialization fails"""
    pass


class Tool:
    """
    Represents a tool that can be assigned to a sub-agent.
    """

    def __init__(self, name: str, description: str, functionality: str):
        self.name = name
        self.description = description
        self.functionality = functionality

    def execute(self, *args, **kwargs) -> Any:
        """
        Execute the tool's functionality.
        This method should be overridden by subclasses implementing specific tools.
        """
        raise NotImplementedError("Execute method must be implemented by the tool subclass.")


# Example tool subclasses
class CodeFormatterTool(Tool):
    def __init__(self):
        super().__init__(
            name="Code Formatter",
            description="Formats code according to predefined style guidelines.",
            functionality="Formats code snippets for consistency."
        )

    def execute(self, code: str) -> str:
        # Placeholder for actual formatting logic
        formatted_code = f"// Formatted Code:\n{code}"
        logger.debug("CodeFormatterTool executed.")
        return formatted_code


class DocumentationGeneratorTool(Tool):
    def __init__(self):
        super().__init__(
            name="Documentation Generator",
            description="Generates documentation from code comments and structure.",
            functionality="Creates comprehensive documentation for the codebase."
        )

    def execute(self, code: str) -> str:
        # Placeholder for actual documentation generation logic
        documentation = f"// Documentation:\nGenerated documentation for the provided code."
        logger.debug("DocumentationGeneratorTool executed.")
        return documentation


class CrewAIAgent(BaseAgent):
    """
    Advanced 'crew' agent that manages software development workflows
    via a specialized team of AI sub-agents (CrewAI).
    """

    def __init__(self, config: Dict[str, Any], model: Optional[Any] = None):
        """
        Initialize the CrewAIAgent.

        Args:
            config (Dict[str, Any]): Configuration dictionary.
            model (Optional[Any]): Language model instance.
        """
        if not CREWAI_AVAILABLE:
            logger.warning("Initializing CrewAIAgent without CrewAI support")

        super().__init__(config, model)
        self.name = "Developer Crew"
        self.description = "Multi-agent system for advanced software development"
        self.current_workflow: Optional[str] = None
        self.agents: Dict[str, CrewAgent] = {}
        self.tools: Dict[str, Tool] = {}
        self.initialization_time: Optional[datetime] = None
        self.last_workflow_execution: Optional[datetime] = None
        self.execution_count: int = 0
        self.success_count: int = 0

        self._initialize_tools()
        self._initialize_crew()

    def _initialize_tools(self) -> None:
        """
        Initialize tools that can be assigned to sub-agents.
        """
        try:
            self.tools['code_formatter'] = CodeFormatterTool()
            self.tools['doc_generator'] = DocumentationGeneratorTool()
            # Add more tools as needed
            logger.debug("Tools initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing tools: {e}")
            raise CrewAgentError(f"Failed to initialize tools: {str(e)}")

    def _initialize_crew(self) -> None:
        """
        Initialize the development crew with specialized roles and assign tools.
        """
        if not CREWAI_AVAILABLE:
            logger.warning("Crew initialization skipped - CrewAI not available")
            return

        try:
            self._create_architect_agent()
            self._create_developer_agent()
            self._create_analyst_agent()
            self._create_integrator_agent()

            self.initialization_time = datetime.now()
            logger.info("Development crew initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing development crew: {e}")
            raise AgentInitializationError(f"Failed to initialize crew: {str(e)}")

    def _create_architect_agent(self) -> None:
        """Create the system architect agent and assign tools."""
        architect_agent = CrewAgent(
            role='System Architect',
            goal='Design and manage system architecture and dependencies',
            backstory=(
                "Expert system architect with deep understanding of "
                "architecture, design patterns, and system integration."
            ),
            verbose=True,
            allow_delegation=True,
            llm=self.model
        )
        # Assign tools to architect
        architect_agent.tools = {
            'code_formatter': self.tools['code_formatter']
        }
        self.agents['architect'] = architect_agent
        logger.debug("Architect agent created and tools assigned.")

    def _create_developer_agent(self) -> None:
        """Create the senior developer agent and assign tools."""
        developer_agent = CrewAgent(
            role='Senior Developer',
            goal='Implement solutions and manage code quality',
            backstory=(
                "Skilled senior developer with expertise in development, "
                "debugging, and optimization."
            ),
            verbose=True,
            allow_delegation=True,
            llm=self.model
        )
        # Assign tools to developer
        developer_agent.tools = {
            'code_formatter': self.tools['code_formatter'],
            'doc_generator': self.tools['doc_generator']
        }
        self.agents['developer'] = developer_agent
        logger.debug("Developer agent created and tools assigned.")

    def _create_analyst_agent(self) -> None:
        """Create the technical analyst agent and assign tools."""
        analyst_agent = CrewAgent(
            role='Technical Analyst',
            goal='Analyze code and create documentation',
            backstory=(
                "Detail-oriented analyst specializing in code analysis, "
                "pattern recognition, and technical documentation."
            ),
            verbose=True,
            allow_delegation=True,
            llm=self.model
        )
        # Assign tools to analyst
        analyst_agent.tools = {
            'doc_generator': self.tools['doc_generator']
        }
        self.agents['analyst'] = analyst_agent
        logger.debug("Analyst agent created and tools assigned.")

    def _create_integrator_agent(self) -> None:
        """Create the system integrator agent and assign tools."""
        integrator_agent = CrewAgent(
            role='System Integrator',
            goal='Manage system integration and dependencies',
            backstory=(
                "Experienced integrator managing dependencies, "
                "compatibility, and system consistency."
            ),
            verbose=True,
            allow_delegation=True,
            llm=self.model
        )
        # Assign tools to integrator
        integrator_agent.tools = {}
        self.agents['integrator'] = integrator_agent
        logger.debug("Integrator agent created.")

    def set_workflow(self, workflow_name: str) -> bool:
        if not CREWAI_AVAILABLE:
            logger.warning("Cannot set workflow - CrewAI not available")
            return False

        try:
            # Directly load from AGENT_PROFILES["crew"]["config"]["workflows"]
            agent_config = self.config.get("AGENT_PROFILES", {}).get("crew", {})
            all_workflows = agent_config.get("config", {}).get("workflows", {})

            # Check if the workflow is defined
            if workflow_name not in all_workflows:
                raise WorkflowError(f"Workflow '{workflow_name}' not found in configuration")

            # Check if it is enabled
            wf_data = all_workflows[workflow_name]
            if not wf_data.get("enabled", True):
                raise WorkflowError(f"Workflow '{workflow_name}' is disabled")

            self.current_workflow = workflow_name
            logger.info(f"Workflow set to: {workflow_name}")
            return True

        except WorkflowError as we:
            logger.error(f"Workflow error: {we}")
            return False
        except Exception as e:
            logger.error(f"Error setting workflow: {e}")
            return False

    def process_message(self, messages: List[Dict[str, str]]) -> str:
        """
        Process a message using the current workflow.

        Args:
            messages (List[Dict[str, str]]): List of message dictionaries.

        Returns:
            str: Result of processing.
        """
        if not CREWAI_AVAILABLE:
            return "Crew agent features are not available - CrewAI is required"

        if not self.initialization_time:
            return "Development crew not properly initialized"

        if not self.current_workflow:
            return "Please select a workflow first (troubleshoot/improve/develop/document)"

        try:
            start_time = datetime.now()
            user_message = messages[-1]['content']
            workflow_config = self._get_workflow_config()

            # Create and validate tasks
            tasks = self._create_workflow_tasks(
                workflow_config['steps'],
                user_message,
                workflow_config.get('roles', {})
            )

            if not tasks:
                raise WorkflowError("No valid tasks created for the workflow")

            # Get required agents
            active_agents = self._get_workflow_agents(workflow_config.get('roles', {}))
            if not active_agents:
                raise WorkflowError("No valid agents available for the workflow")

            # Execute workflow
            result = self._execute_workflow(active_agents, tasks)
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_execution_stats(True, execution_time)

            return result

        except WorkflowError as we:
            self._update_execution_stats(False)
            logger.error(f"Workflow processing error: {we}")
            return f"Workflow execution failed: {we}"
        except Exception as e:
            self._update_execution_stats(False)
            error_msg = f"Error in workflow processing: {e}"
            logger.error(error_msg)
            return f"Workflow execution failed: {e}"

    def _get_workflow_config(self) -> Dict[str, Any]:
        try:
            agent_config = self.config.get('AGENT_PROFILES', {}).get('crew', {})
            workflows = agent_config.get('config', {}).get('workflows', {})
            workflow_config = workflows.get(self.current_workflow)
            
            if not workflow_config:
                raise WorkflowError(f"Configuration not found for workflow: {self.current_workflow}")
                
            if not workflow_config.get('enabled', False):
                raise WorkflowError(f"Workflow '{self.current_workflow}' is disabled")
                
            return workflow_config
        except Exception as e:
            logger.error(f"Error getting workflow configuration: {e}")
            raise

    def _execute_workflow(self, agents: List[CrewAgent], tasks: List[Task]) -> str:
        try:
            workflow_config = self._get_workflow_config()
            process_type = workflow_config.get('process_type', Process.sequential)

            crew = Crew(
                agents=agents,
                tasks=tasks,
                verbose=True,
                process=process_type
            )

            # Execute each task and collect results
            results = []
            for task in tasks:
                try:
                    task_result = task.execute()
                    results.append(f"Step '{task.description}': {task_result}")
                except Exception as e:
                    logger.error(f"Task execution failed: {e}")
                    results.append(f"Step '{task.description}' failed: {str(e)}")

            # Execute the full workflow
            final_result = crew.kickoff()
            
            # Combine task results with final workflow output
            combined_result = "\n".join([
                "Workflow Execution Results:",
                "------------------------",
                *results,
                "------------------------",
                "Final Output:",
                final_result
            ])

            logger.info(f"Workflow '{self.current_workflow}' completed successfully")
            return combined_result

        except Exception as e:
            logger.error(f"Error during workflow execution: {e}")
            raise WorkflowError(f"Workflow execution failed: {e}")

    def _update_execution_stats(self, success: bool, execution_time: Optional[float] = None) -> None:
        """
        Update workflow execution statistics.

        Args:
            success (bool): Whether the workflow execution was successful.
            execution_time (Optional[float]): Time taken for execution in seconds.
        """
        self.execution_count += 1
        if success:
            self.success_count += 1
        self.last_workflow_execution = datetime.now()

        if execution_time:
            success_rate = (self.success_count / self.execution_count) * 100 if self.execution_count > 0 else 0
            logger.info(
                f"Workflow execution completed - Success: {success}, "
                f"Time: {execution_time:.2f}s, "
                f"Success rate: {success_rate:.1f}%"
            )

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Return detailed agent information, including which workflows exist and are enabled.
        """
        # If CrewAI is not installed, no advanced features
        if not CREWAI_AVAILABLE:
            return {
                "name": self.name,
                "description": self.description,
                "type": "crew",
                "capabilities": [],
                "workflows": {},
                "is_active": self.is_active,
                "current_workflow": self.current_workflow,
                "team_members": list(self.agents.keys()),
                "crewai_available": CREWAI_AVAILABLE,
                "initialization_time": self.initialization_time,
                "last_execution": self.last_workflow_execution,
                "execution_stats": {
                    "total_executions": self.execution_count,
                    "successful_executions": self.success_count,
                    "success_rate": (
                        (self.success_count / self.execution_count) * 100
                        if self.execution_count > 0 else 0
                    ),
                },
                "status": self.status,
                "tools": {tool_name: tool.description for tool_name, tool in self.tools.items()},
            }

        # If we DO have CrewAI, gather the list of “enabled” workflows
        agent_config = self.config.get("AGENT_PROFILES", {}).get("crew", {})
        all_workflows = agent_config.get("config", {}).get("workflows", {})
        active_workflows = {
            key: wf
            for key, wf in all_workflows.items()
            if wf.get("enabled", False)
        }

        return {
            "name": self.name,
            "description": self.description,
            "type": "crew",
            "capabilities": [
                "troubleshooting",
                "code-improvement",
                "feature-development",
                "documentation",
                "system-integration",
            ],
            "workflows": active_workflows,
            "is_active": self.is_active,
            "current_workflow": self.current_workflow,
            "team_members": list(self.agents.keys()),
            "crewai_available": CREWAI_AVAILABLE,
            "initialization_time": self.initialization_time,
            "last_execution": self.last_workflow_execution,
            "execution_stats": {
                "total_executions": self.execution_count,
                "successful_executions": self.success_count,
                "success_rate": (
                    (self.success_count / self.execution_count) * 100
                    if self.execution_count > 0 else 0
                ),
            },
            "status": self.status,
            "tools": {tool_name: tool.description for tool_name, tool in self.tools.items()},
        }

    def reset(self) -> bool:
        """
        Reset the crew agent to its initial state.

        Returns:
            bool: True if reset successfully, False otherwise.
        """
        try:
            super().reset()
            self.current_workflow = None
            self.execution_count = 0
            self.success_count = 0
            self.last_workflow_execution = None

            # Reset sub-agents
            for agent in self.agents.values():
                agent.reset()

            logger.info("CrewAIAgent has been reset successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to reset CrewAIAgent: {e}")
            return False

    ########################################################################
    # Enhanced Workflow-Creation Logic with Tool Integration
    ########################################################################

    def _create_workflow_tasks(
        self,
        step_list: List[str],
        user_message: str,
        role_map: Dict[str, str]
    ) -> List[Task]:
        """
        Create tasks for each step in the workflow with assigned agents and tools.

        Args:
            step_list (List[str]): List of workflow steps.
            user_message (str): User's message or request.
            role_map (Dict[str, str]): Mapping of roles to agents.

        Returns:
            List[Task]: List of tasks to execute.
        """
        tasks = []
        for step in step_list:
            agent_role = role_map.get(step, None)
            if not agent_role:
                logger.warning(f"No agent role mapped for step '{step}'. Skipping task creation.")
                continue

            agent = self._get_agent_by_role(agent_role)
            if not agent:
                logger.warning(f"No agent found for role '{agent_role}'. Skipping task creation.")
                continue

            # Assign tools based on step
            tools = agent.tools.get(step, [])  # Assuming step corresponds to tool names
            task_description = f"Step '{step}': {user_message}"
            task = Task(
                description=task_description,
                agent=agent,
                tools=tools
            )
            tasks.append(task)
            logger.debug(f"Task created for step '{step}' with agent '{agent_role}' and tools '{tools}'.")
        return tasks

    def _get_agent_by_role(self, role: str) -> Optional[CrewAgent]:
        """
        Retrieve an agent by its role.

        Args:
            role (str): Role of the agent.

        Returns:
            Optional[CrewAgent]: The corresponding agent or None if not found.
        """
        for agent in self.agents.values():
            if agent.role.lower() == role.lower():
                return agent
        logger.warning(f"Agent with role '{role}' not found.")
        return None

    def _get_workflow_agents(self, role_map: Dict[str, str]) -> List[CrewAgent]:
        """
        Return the actual sub-agents needed for this workflow based on role mapping.

        Args:
            role_map (Dict[str, str]): Mapping of roles to agents.

        Returns:
            List[CrewAgent]: List of agents involved in the workflow.
        """
        agents = []
        for step, role in role_map.items():
            agent = self._get_agent_by_role(role)
            if agent and agent not in agents:
                agents.append(agent)
        if not agents:
            logger.warning("No valid agents found for the workflow.")
        return agents


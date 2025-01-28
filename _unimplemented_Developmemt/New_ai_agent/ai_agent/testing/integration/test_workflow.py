"""
tests/integration/test_workflow.py - Integration tests for workflows
"""

import pytest
import asyncio
from typing import Dict, Any
from ai_agent.core.workflow.manager import WorkflowManager
from ai_agent.core.workflow.templates import DevelopmentWorkflow
from ai_agent.agents.architect import ArchitectAgent
from ai_agent.agents.developer import DeveloperAgent
from ai_agent.agents.judge import JudgeAgent
from ai_agent.config.settings import Config

@pytest.fixture
async def config():
    return Config()

@pytest.fixture
async def workflow_agents(config):
    architect = ArchitectAgent(config.get_agent_config("architect"))
    developer = DeveloperAgent(config.get_agent_config("developer"))
    judge = JudgeAgent(config.get_agent_config("judge"))
    await asyncio.gather(
        architect.initialize(),
        developer.initialize(), 
        judge.initialize()
    )
    return architect, developer, judge

@pytest.mark.asyncio
async def test_development_workflow(workflow_agents):
    """Test complete development workflow"""
    architect, developer, judge = workflow_agents
    
    # Configure workflow
    workflow = DevelopmentWorkflow(architect, developer, judge)
    workflow.setup(
        requirements=[
            "Create a function to calculate fibonacci numbers",
            "Function should be efficient for large numbers",
            "Include input validation"
        ],
        constraints=[
            "Use dynamic programming",
            "Maximum recursion depth of 100",
            "Handle negative inputs appropriately" 
        ]
    )
    
    # Execute workflow
    results = await workflow.execute()
    
    # Verify results
    assert results["design"]["components"]
    assert results["implement"]["code"]
    assert results["implement"]["tests"]
    assert results["validate"]["passed"]
    
    # Verify code quality
    validation = results["validate"]
    assert validation["test_results"]["coverage"] >= 0.8
    assert not validation["test_results"]["error_messages"]

@pytest.mark.asyncio
async def test_workflow_error_handling(workflow_agents):
    """Test workflow error handling"""
    architect, developer, judge = workflow_agents
    
    # Configure workflow with invalid requirements
    workflow = DevelopmentWorkflow(architect, developer, judge)
    workflow.setup(
        requirements=[],
        constraints=["Invalid constraint"]
    )
    
    # Execute workflow
    results = await workflow.execute()
    
    # Verify error handling
    assert workflow.get_status()["state"] == "failed"
    assert workflow.get_status()["current_step"] == "design"

@pytest.mark.asyncio
async def test_workflow_cancellation(workflow_agents):
    """Test workflow cancellation"""
    architect, developer, judge = workflow_agents
    
    # Configure workflow
    workflow = DevelopmentWorkflow(architect, developer, judge)
    workflow.setup(
        requirements=["Long running task"],
        constraints=[]
    )
    
    # Start workflow
    task = asyncio.create_task(workflow.execute())
    
    # Cancel after short delay
    await asyncio.sleep(0.1)
    workflow.cancel()
    
    # Verify cancellation
    try:
        await task
    except Exception as e:
        assert "cancelled" in str(e).lower()
    
    assert workflow.get_status()["state"] == "cancelled"

"""
tests/integration/test_agents.py - Integration tests for agents
"""

import pytest
import asyncio
from ai_agent.core.agents.base import AgentState
from ai_agent.testing.executors.terminal import TerminalExecutor
from ai_agent.config.settings import Config

@pytest.fixture
async def developer_agent(config):
    agent = DeveloperAgent(config.get_agent_config("developer"))
    agent.test_executor = TerminalExecutor("work/tests")
    await agent.initialize()
    return agent

@pytest.mark.asyncio
async def test_test_driven_development(developer_agent):
    """Test TDD workflow"""
    # Set up task
    task = {
        "name": "sort_list",
        "description": "Implement an efficient sorting function",
        "requirements": [
            "Sort list in ascending order",
            "Handle duplicate values",
            "Return new sorted list"
        ]
    }
    
    # Process task
    result = await developer_agent.process(task)
    
    # Verify TDD workflow
    assert result["tests"]
    assert result["implementation"]
    assert result["test_results"]["success"]
    
    # Verify code quality
    test_results = result["test_results"]
    assert test_results["tests_passed"] == test_results["tests_run"]
    assert test_results["coverage"] >= 0.8

@pytest.mark.asyncio
async def test_error_handling(developer_agent):
    """Test agent error handling"""
    # Invalid task
    task = {
        "name": "invalid",
        "description": "",
        "requirements": []
    }
    
    # Process should raise error
    with pytest.raises(ValueError):
        await developer_agent.process(task)
    
    assert developer_agent.state == AgentState.ERROR

@pytest.mark.asyncio
async def test_auto_fix(developer_agent):
    """Test automatic error fixing"""
    # Task with edge case
    task = {
        "name": "divide",
        "description": "Implement division function",
        "requirements": [
            "Divide two numbers",
            "Handle division by zero",
            "Return float result"
        ]
    }
    
    # Process task
    result = await developer_agent.process(task)
    
    # Verify auto-fix
    assert result["test_results"]["success"]
    assert "ZeroDivisionError" not in result["implementation"]
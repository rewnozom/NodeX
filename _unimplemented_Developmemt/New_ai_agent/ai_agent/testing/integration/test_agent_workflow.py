"""
tests/integration/test_agent_workflow.py - Integration tests for agent workflows
"""

import pytest
import asyncio
from ai_agent.core.workflow.manager import WorkflowManager
from ai_agent.core.workflow.steps import StepBuilder
from ai_agent.agents import JudgeAgent, DeveloperAgent, ArchitectAgent, ReviewerAgent
from ai_agent.config import Config

@pytest.fixture
async def config():
    return Config("test_config")

@pytest.fixture
async def agents(config):
    architect = ArchitectAgent(config.get_agent_config("architect"))
    developer = DeveloperAgent(config.get_agent_config("developer"))
    judge = JudgeAgent(config.get_agent_config("judge"))
    reviewer = ReviewerAgent(config.get_agent_config("reviewer"))
    
    await asyncio.gather(
        architect.initialize(),
        developer.initialize(),
        judge.initialize(),
        reviewer.initialize()
    )
    
    return architect, developer, judge, reviewer

@pytest.mark.asyncio
async def test_full_development_cycle(agents):
    """Test complete development workflow"""
    architect, developer, judge, reviewer = agents
    workflow = WorkflowManager()

    # Design step
    design_step = (StepBuilder("design", architect)
        .with_inputs({
            "requirements": ["Create a function to validate email addresses"],
            "constraints": ["Must use regex", "Handle edge cases"]
        })
        .build())
    workflow.add_step(design_step)

    # Implementation step
    impl_step = (StepBuilder("implement", developer)
        .with_inputs({
            "design": "$design.api_specs",
            "test_first": True
        })
        .build())
    workflow.add_step(impl_step)

    # Review step
    review_step = (StepBuilder("review", reviewer)
        .with_inputs({
            "code": "$implement.code",
            "review_type": "all"
        })
        .build())
    workflow.add_step(review_step)

    # Validation step
    validate_step = (StepBuilder("validate", judge)
        .with_inputs({
            "code": "$implement.code",
            "tests": "$implement.tests",
            "review": "$review"
        })
        .build())
    workflow.add_step(validate_step)

    results = await workflow.execute()
    
    assert results["design"]["components"]
    assert "email_validator" in results["implement"]["code"]
    assert results["review"]["scores"]["quality"] > 0.7
    assert results["validate"]["passed"]

@pytest.mark.asyncio
async def test_workflow_recovery(agents):
    """Test workflow error recovery"""
    _, developer, judge, _ = agents
    workflow = WorkflowManager()

    async def on_failure(e):
        return {"fixed_code": "def fixed(): pass"}

    # Add failing step
    fail_step = (StepBuilder("fail", developer)
        .with_inputs({"code": "invalid syntax"})
        .with_failure_handler(on_failure)
        .with_retries(2)
        .build())
    workflow.add_step(fail_step)

    # Add validation
    validate_step = (StepBuilder("validate", judge)
        .with_inputs({"code": "$fail.fixed_code"})
        .build())
    workflow.add_step(validate_step)

    results = await workflow.execute()
    assert workflow.get_status()["state"] == "completed"
    assert "fixed_code" in results["fail"]

@pytest.mark.asyncio
async def test_conditional_steps(agents):
    """Test conditional workflow steps"""
    _, developer, judge, _ = agents
    workflow = WorkflowManager()

    def should_run(inputs):
        return inputs.get("run", True)

    # Add conditional step
    cond_step = (StepBuilder("conditional", developer)
        .with_inputs({"run": False})
        .with_condition(should_run)
        .build())
    workflow.add_step(cond_step)

    results = await workflow.execute()
    assert workflow.get_status()["state"] == "completed"
    assert "conditional" not in results
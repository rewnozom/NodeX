import pytest
from unittest.mock import MagicMock
from datetime import datetime

from ai_agent.agents.base_agent import BaseAgent

@pytest.mark.usefixtures("mock_model")
class TestBaseAgentPytest:
    @pytest.fixture
    def agent(self, mock_model):
        config = {
            'max_retries': 3,
            'name': 'Test Agent',
            'version': '1.0.0',
            'description': 'Test agent implementation'
        }
        return BaseAgent(config, mock_model)

    def test_initialization(self, agent, mock_model):
        assert agent.config['name'] == 'Test Agent'
        assert agent.model == mock_model
        assert agent.is_active is False
        assert agent.last_activity is None
        assert agent.error_count == 0
        assert agent.max_retries == 3

    def test_activate(self, agent):
        activated = agent.activate()
        assert activated is True
        assert agent.is_active is True
        assert agent.last_activity is not None

    def test_deactivate(self, agent):
        agent.activate()
        deactivated = agent.deactivate()
        assert deactivated is True
        assert agent.is_active is False
        assert agent.last_activity is not None

    def test_update_config(self, agent):
        new_config = {
            'max_retries': 5,
            'name': 'Updated Agent'
        }
        updated = agent.update_config(new_config)
        assert updated is True
        assert agent.config['max_retries'] == 5
        assert agent.config['name'] == 'Updated Agent'

    def test_reset(self, agent):
        agent.activate()
        agent.error_count = 2
        reset_ok = agent.reset()
        assert reset_ok is True
        assert agent.is_active is False
        assert agent.last_activity is None
        assert agent.error_count == 0

    @pytest.mark.parametrize("valid_messages", [
        [{"role": "system", "content": "Test system message"},
         {"role": "user", "content": "Test user message"}],
        [{"role": "assistant", "content": "Assistant message"}]
    ])
    def test_validate_messages_valid(self, agent, valid_messages):
        assert agent.validate_messages(valid_messages) is True

    @pytest.mark.parametrize("invalid_messages", [
        [{"role": "system", "content": 123}],
        [{"content": "Missing role"}],
    ])
    def test_validate_messages_invalid(self, agent, invalid_messages):
        with pytest.raises(ValueError):
            agent.validate_messages(invalid_messages)

    def test_handle_error(self, agent):
        test_error = Exception("Test error")
        agent.handle_error(test_error)
        assert agent.error_count == 1

        # Exceed max retries
        for _ in range(agent.max_retries):
            agent.handle_error(test_error)
        # Agent should become inactive
        assert agent.is_active is False
        assert agent.error_count == agent.max_retries + 1

    def test_is_running_property(self, agent):
        assert agent.is_running is False
        agent.activate()
        assert agent.is_running is True
        agent.deactivate()
        assert agent.is_running is False

    def test_status_property(self, agent):
        status = agent.status
        assert isinstance(status, dict)
        assert "is_active" in status
        assert "last_activity" in status
        assert "error_count" in status
        assert "model_loaded" in status

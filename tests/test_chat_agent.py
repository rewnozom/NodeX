import pytest
from unittest.mock import MagicMock
from ai_agent.agents.chat_agent import ChatAgent

@pytest.mark.usefixtures("mock_model")
class TestChatAgentPytest:
    @pytest.fixture
    def agent(self, mock_model):
        config = {
            'max_history': 10,
            'save_history': True,
            'response_timeout': 30,
            'max_retries': 3,
            'temperature': 0.7
        }
        return ChatAgent(config, mock_model)

    def test_initialization(self, agent):
        assert agent.name == "Standard Chat"
        assert agent.save_history is True
        assert agent.max_history == 10
        assert agent.response_timeout == 30
        assert isinstance(agent.message_history, list)

    def test_message_based_processing(self, agent, mock_model):
        # Pretend we have an OpenAI Chat model
        mock_model.__class__.__name__ = 'OpenAIChat'
        messages = [
            {"role": "system", "content": "Test system message"},
            {"role": "user", "content": "Test query"}
        ]
        expected_response = "Test response"
        mock_model.return_value = expected_response

        response = agent.process_message(messages)
        assert response == expected_response
        mock_model.assert_called_once_with(messages)

    def test_text_based_processing(self, agent, mock_model):
        # Pretend we have a custom model
        mock_model.__class__.__name__ = 'CustomModel'
        mock_model.invoke.return_value = "Model response"
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"}
        ]
        response = agent.process_message(messages)
        assert response == "Model response"
        mock_model.invoke.assert_called_once()

    def test_history_management(self, agent):
        msgs = [{"role": "user", "content": "Test"}]
        agent._update_history(msgs, "Response")
        assert len(agent.message_history) == 1

        # Overflow the history
        for _ in range(15):
            agent._update_history(msgs, "Response")
        assert len(agent.message_history) == agent.max_history

    def test_error_handling(self, agent, mock_model):
        mock_model.side_effect = Exception("Test error")
        with pytest.raises(RuntimeError, match="Test error"):
            agent.process_message([{"role": "user", "content": "Test"}])
        assert agent.error_count == 1

    def test_response_formatting(self, agent):
        assert agent._format_response("test") == "test"
        assert agent._format_response({"content": "test"}) == "test"

        mock_resp = MagicMock()
        mock_resp.content = "test"
        assert agent._format_response(mock_resp) == "test"

    def test_clear_history(self, agent):
        agent.message_history = [{"test": "data"}] * 5
        agent.clear_history()
        assert len(agent.message_history) == 0

    def test_get_agent_info(self, agent):
        info = agent.get_agent_info()
        required_keys = {
            'name', 'description', 'type', 'capabilities',
            'is_active', 'model_type', 'last_response',
            'history_size', 'error_count', 'status'
        }
        assert required_keys.issubset(info.keys())
        assert info['type'] == 'chat'

    def test_max_retries_exceeded(self, agent, mock_model):
        mock_model.side_effect = Exception("Test error")
        messages = [{"role": "user", "content": "Test"}]

        for _ in range(agent.config['max_retries'] + 1):
            with pytest.raises(RuntimeError):
                agent.process_message(messages)

        assert agent.is_active is False
        assert agent.error_count == agent.config['max_retries'] + 1

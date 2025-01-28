import pytest
from unittest.mock import patch
from ai_agent.agents.developer_agent import DeveloperAgent

@pytest.mark.usefixtures("mock_model")
class TestDeveloperAgentPytest:
    @pytest.fixture
    def agent(self, mock_model, agent_config):
        # agent_config is a Config object from conftest
        agent_config_dict = {
            'profile': {
                'config': {
                    'workflows': {
                        'test_workflow': {
                            'enabled': True,
                            'steps': ['analysis', 'implementation', 'review']
                        }
                    }
                }
            }
        }
        # Simulate loading these
        agent_config.update_agent_config(agent_config_dict)
        return DeveloperAgent(agent_config, mock_model)

    def test_initialization(self, agent):
        assert agent.name == "Developer Agent"
        assert agent.description == "Multi-agent system for software development"
        assert agent.current_workflow is None
        assert agent.team_initialized is False

    @patch('ai_agent.agents.developer_agent.Agent')
    def test_initialize_team(self, mock_agent_class, agent):
        agent.initialize_team()
        assert agent.team_initialized is True
        assert agent.architect is not None
        assert agent.developer is not None
        assert agent.reviewer is not None
        mock_agent_class.assert_called()

    def test_set_workflow(self, agent):
        assert agent.set_workflow('test_workflow') is True
        assert agent.current_workflow == 'test_workflow'

        assert agent.set_workflow('nonexistent_workflow') is False
        # Add disabled workflow
        agent.config.get_agent_config()['config']['workflows']['disabled_workflow'] = {
            'enabled': False
        }
        assert agent.set_workflow('disabled_workflow') is False

    @patch('ai_agent.agents.developer_agent.Crew')
    def test_process_message(self, mock_crew_class, agent):
        agent.initialize_team()
        agent.set_workflow('test_workflow')
        mock_crew_instance = mock_crew_class.return_value
        mock_crew_instance.kickoff.return_value = "Task completed successfully"

        result = agent.process_message([{"role": "user", "content": "Test task"}])
        assert result == "Task completed successfully"

    def test_process_message_no_init(self, agent):
        # Not initialized
        result = agent.process_message([{"role": "user", "content": "Test"}])
        assert "team not properly initialized" in result

    def test_process_message_no_workflow(self, agent):
        agent.initialize_team()
        result = agent.process_message([{"role": "user", "content": "Test"}])
        assert "select a workflow" in result

    @patch('ai_agent.agents.developer_agent.Task')
    def test_create_task_for_step(self, mock_task_class, agent):
        agent.initialize_team()
        valid_steps = ['analysis', 'planning', 'implementation', 'review',
                       'testing', 'documentation', 'suggestions', 'reproduction', 'fixing']
        context = "Test context"

        for step in valid_steps:
            t = agent._create_task_for_step(step, context)
            assert t is not None, f"Task should be created for step={step}"
            mock_task_class.assert_called()

        # invalid step
        t2 = agent._create_task_for_step('unknown_step', context)
        assert t2 is None

    def test_get_agent_info(self, agent):
        info = agent.get_agent_info()
        required_keys = {
            'name', 'description', 'type', 'capabilities',
            'is_active', 'current_workflow', 'team_members',
            'crewai_available', 'team_initialized'
        }
        assert required_keys.issubset(info.keys())
        assert info['type'] == 'developer'

    @pytest.mark.usefixtures("has_crewai")
    def test_crewai_unavailable(self, monkeypatch, agent):
        # Force CREWAI_AVAILABLE = False
        from ai_agent.agents import developer_agent
        monkeypatch.setattr(developer_agent, 'CREWAI_AVAILABLE', False)

        result = agent.process_message([{"role": "user", "content": "Test"}])
        assert "CrewAI is required" in result
        assert agent.team_initialized is False

    def test_concurrent_workflows(self, agent):
        agent.initialize_team()
        agent.set_workflow('test_workflow')
        current = agent.current_workflow
        # Suppose there's another workflow
        agent.config.get_agent_config()['config']['workflows']['another'] = {
            'enabled': True, 'steps': []
        }
        agent.set_workflow('another')
        assert agent.current_workflow != current

    @patch('ai_agent.agents.developer_agent.Crew')
    def test_error_propagation(self, mock_crew_class, agent):
        agent.initialize_team()
        agent.set_workflow('test_workflow')
        mock_crew_class.side_effect = Exception("Test error")

        result = agent.process_message([{"role": "user", "content": "Test"}])
        assert "Error during execution" in result

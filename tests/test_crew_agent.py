import pytest
from unittest.mock import patch, MagicMock
from ai_agent.agents.crew_agent import CrewAIAgent, WorkflowError

@pytest.mark.usefixtures("mock_model")
class TestCrewAIAgentPytest:
    @pytest.fixture
    def agent(self, mock_model):
        config = {
            'max_team_size': 3,
            'process_type': 'sequential',
            'verbose': True,
            'workflows': {
                'test_workflow': {
                    'enabled': True,
                    'steps': ['analysis', 'implementation', 'review'],
                    'roles': {
                        'architect': 'Design system',
                        'developer': 'Implement features',
                        'reviewer': 'Review code'
                    }
                }
            }
        }
        return CrewAIAgent(config, mock_model)

    @pytest.mark.usefixtures("has_crewai")
    def test_initialization(self, agent):
        assert agent.name == "Developer Crew"
        assert agent.description == "Multi-agent system for advanced software development"
        assert agent.current_workflow is None
        assert isinstance(agent.agents, dict)

    def test_workflow_management(self, agent):
        assert agent.set_workflow('test_workflow') is True
        assert agent.current_workflow == 'test_workflow'
        assert agent.set_workflow('nonexistent_workflow') is False

        agent.config['workflows']['disabled_workflow'] = {'enabled': False}
        assert agent.set_workflow('disabled_workflow') is False

    @pytest.mark.usefixtures("has_crewai")
    @patch('ai_agent.agents.crew_agent.Crew')
    def test_process_message(self, mock_crew_class, agent):
        agent.set_workflow('test_workflow')
        mock_crew_instance = mock_crew_class.return_value
        mock_crew_instance.kickoff.return_value = "Workflow completed successfully"

        result = agent.process_message([{"role": "user", "content": "Test task"}])
        assert result == "Workflow completed successfully"
        assert agent.execution_count == 1
        assert agent.success_count == 1

    @pytest.mark.usefixtures("has_crewai")
    @patch('ai_agent.agents.crew_agent.Crew')
    def test_error_handling(self, mock_crew_class, agent):
        agent.set_workflow('test_workflow')
        mock_crew_instance = mock_crew_class.return_value
        mock_crew_instance.kickoff.side_effect = WorkflowError("Test error")

        result = agent.process_message([{"role": "user", "content": "Test task"}])
        assert "Workflow execution failed" in result
        assert agent.execution_count == 1
        assert agent.success_count == 0

    def test_workflow_validation(self, agent):
        # No workflow set
        result = agent.process_message([{"role": "user", "content": "Test"}])
        assert "Please select a workflow first" in result

        agent.current_workflow = "invalid"
        result2 = agent.process_message([{"role": "user", "content": "Test"}])
        assert "Workflow execution failed" in result2

    @pytest.mark.usefixtures("has_crewai")
    def test_execution_stats(self, agent):
        agent.set_workflow('test_workflow')

        with patch('ai_agent.agents.crew_agent.Crew') as mock_crew:
            mock_crew.return_value.kickoff.return_value = "Success"
            agent.process_message([{"role": "user", "content": "Test task"}])

        with patch('ai_agent.agents.crew_agent.Crew') as mock_crew:
            mock_crew.return_value.kickoff.side_effect = Exception("Error")
            agent.process_message([{"role": "user", "content": "Test task"}])

        assert agent.execution_count == 2
        assert agent.success_count == 1

        info = agent.get_agent_info()
        stats = info['execution_stats']
        assert stats['total_executions'] == 2
        assert stats['successful_executions'] == 1
        assert stats['success_rate'] == 50.0

    def test_reset(self, agent):
        agent.current_workflow = "test"
        agent.execution_count = 5
        agent.success_count = 3
        agent.last_workflow_execution = "timestamp"

        assert agent.reset() is True
        assert agent.current_workflow is None
        assert agent.execution_count == 0
        assert agent.success_count == 0
        assert agent.last_workflow_execution is None

    @pytest.mark.usefixtures("has_crewai")
    def test_get_workflow_agents(self, agent):
        agent.set_workflow('test_workflow')
        roles = {
            'architect': 'Design system',
            'developer': 'Implement features'
        }
        active_agents = agent._get_workflow_agents(roles)
        assert len(active_agents) == 2

    @pytest.mark.usefixtures("has_crewai")
    def test_crewai_unavailable_mock(self, monkeypatch, mock_model):
        # Force CREWAI_AVAILABLE=False in code
        from ai_agent.agents import crew_agent
        monkeypatch.setattr(crew_agent, 'CREWAI_AVAILABLE', False)

        agent_no_crew = crew_agent.CrewAIAgent({}, mock_model)
        result = agent_no_crew.process_message([{"role": "user", "content": "Test"}])
        assert "CrewAI is required" in result

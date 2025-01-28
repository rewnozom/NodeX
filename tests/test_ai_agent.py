# test_ai_agent.py

import unittest
from unittest.mock import patch, MagicMock, mock_open
from ai_agent.services.ai_service import AIService
from ai_agent.config.ai_config import Config
from ai_agent.config.prompt_manager import PromptService

class TestAIAgent(unittest.TestCase):
    def setUp(self):
        # Create config & service
        self.config = Config()
        self.ai_service = AIService(self.config)

        # Replace the real LLM client with a mock
        self.mock_client = MagicMock(name="MockClientClass")
        self.ai_service.client = self.mock_client

    def test_ai_service_initialization(self):
        # We expect the client to be a mock named "MockClientClass"
        self.assertEqual(self.ai_service.client.__class__.__name__, "MockClientClass")

    def test_get_response_success(self):
        mock_response = "This is a mock response"
        self.mock_client.__call__.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        response = self.ai_service.get_response(messages)

        self.assertEqual(response, mock_response)
        self.mock_client.__call__.assert_called_once_with(messages)

    def test_get_response_failure(self):
        self.mock_client.__call__.side_effect = Exception("Mock error")
        with self.assertRaises(Exception) as ctx:
            self.ai_service.get_response([{"role": "user", "content": "Bang!"}])
        self.assertIn("Mock error", str(ctx.exception))

    @patch('ai_agent.config.prompt_manager.save_system_prompt')
    @patch('builtins.open', new_callable=mock_open, read_data='This is a test system prompt.')
    @patch('os.path.exists', return_value=True)
    def test_prompt_service_get_system_prompt(self, mock_exists, mock_file, mock_save):
        ps = PromptService(self.config)
        ps.load_system_prompts()  # or whichever method triggers reading 'example.md'
        content = ps.get_system_prompt("example")
        self.assertEqual(content, "This is a test system prompt.")
        mock_save.assert_called_once_with("This is a test system prompt.")

    def test_update_agent(self):
        # Switch agent to 'developer' and enable
        result = self.ai_service.update_agent(agent_type='developer', enabled=True)
        self.assertTrue(result)
        
        # Force a re-load
        self.ai_service.load_agent_config()
        self.assertEqual(self.ai_service.current_agent, 'developer')


if __name__ == '__main__':
    unittest.main()


# -*- coding: utf-8 -*-
# ./frontend/pages/desktop/Layout/test_chat.py

import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication, QMessageBox
import sys
import logging

class TestChatPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize the QApplication once for all tests
        cls.app = QApplication(sys.argv)

    def setUp(self):
        # Patch the Config class before importing Page
        with patch('ai_agent.config.ai_config.Config') as mock_config_class:
            self.mock_config = mock_config_class.return_value

            # Setup mock config return values
            self.mock_config.get_agent_config.return_value = {
                'current_agent': 'chat',
                'enabled': True,
                'developer': {
                    'enabled': False,
                    'profile': {
                        'name': 'DevAgent',
                        'config': {
                            'current_workflow': 'develop'
                        }
                    }
                },
                'crew': {
                    'enabled': False,
                    'profile': {
                        'name': 'CrewAgent',
                        'config': {
                            'current_workflow': 'design'
                        }
                    }
                }
            }
            self.mock_config.CHAT_TEMPERATURE = 0.5
            self.mock_config.CHAT_MODEL = 'GPT-3.5-Turbo'
            self.mock_config.MAX_TOKENS = 2048
            self.mock_config.ENABLE_MEMORY = False  # Adjust as needed

            # Patch AgentFactory to prevent loading crewai modules
            with patch('ai_agent.agents.agent_factory.AgentFactory') as mock_agent_factory_class:
                self.mock_agent_factory = mock_agent_factory_class.return_value

                # Setup mock agent
                self.mock_agent = MagicMock()
                self.mock_agent.is_running = False
                self.mock_agent.process_message.return_value = "Mock response"
                self.mock_agent_factory.create_agent.return_value = self.mock_agent

                # Create a mock parent (MainWindow) with necessary attributes
                self.mock_parent = MagicMock()

                # Import Page after patches
                from frontend.Pages.desktop.Layout.chat import Page
                self.page = Page(parent=self.mock_parent)

    def tearDown(self):
        # Clean up after each test
        self.page = None

    def test_initialization(self):
        # Test if the Page initializes correctly
        self.assertIsNotNone(self.page.ai_service, "AIService should be initialized.")
        self.assertEqual(self.page.current_model_name, self.mock_config.CHAT_MODEL, "Current model name should match config.")
        self.assertIsNotNone(self.page.chat_history_list, "Chat history list should be initialized.")
        self.assertIsNotNone(self.page.chat_display, "Chat display should be initialized.")
        self.assertIsNotNone(self.page.send_button, "Send button should be initialized.")

    def test_send_message_empty(self):
        # Test sending an empty message does nothing
        with patch.object(self.page, 'display_user_message') as mock_display_user, \
             patch.object(self.page, 'add_to_chat_history') as mock_add_history, \
             patch.object(self.page, 'prepare_messages') as mock_prepare_messages, \
             patch.object(self.page, 'update_status_message') as mock_update_status:
            self.page.user_message_textedit.setPlainText("   ")  # Set to empty message
            self.page.send_message()
            mock_display_user.assert_not_called()
            mock_add_history.assert_not_called()
            mock_prepare_messages.assert_not_called()
            mock_update_status.assert_not_called()

    def test_send_message_valid(self):
        # Test sending a valid message
        test_message = "Hello, AI!"
        with patch.object(self.page, 'display_user_message') as mock_display_user, \
             patch.object(self.page, 'add_to_chat_history') as mock_add_history, \
             patch.object(self.page, 'prepare_messages') as mock_prepare_messages, \
             patch.object(self.page, 'update_status_message') as mock_update_status, \
             patch('ai_agent.threads.worker_thread.WorkerThread.start') as mock_worker_start:
            
            mock_prepare_messages.return_value = [
                {'role': 'system', 'content': 'Test system prompt'},
                {'role': 'user', 'content': test_message}
            ]
            
            self.page.user_message_textedit.setPlainText(test_message)
            self.page.send_message()
            
            mock_display_user.assert_called_once_with(test_message)
            mock_add_history.assert_called_once()
            mock_prepare_messages.assert_called_once()
            mock_update_status.assert_called_once_with("Processing message...", is_agent_message=True)
            mock_worker_start.assert_called_once()

    def test_toggle_agent_mode_enable(self):
        # Test enabling an agent
        with patch.object(self.page.ai_service, 'update_agent') as mock_update_agent, \
             patch.object(self.page, 'update_status_message') as mock_update_status:
            mock_update_agent.return_value = True
            self.page.toggle_agent_mode('developer', True)
            mock_update_agent.assert_called_with(
                agent_type='developer',
                enabled=True,
                settings={'current_workflow': 'troubleshoot'}  # Assuming default selection
            )
            mock_update_status.assert_called_with("Developer Agent Enabled", is_agent_message=True)

    def test_toggle_agent_mode_disable(self):
        # Test disabling an agent
        with patch.object(self.page.ai_service, 'update_agent') as mock_update_agent, \
             patch.object(self.page, 'update_status_message') as mock_update_status:
            mock_update_agent.return_value = True
            self.page.toggle_agent_mode('crew', False)
            mock_update_agent.assert_called_with(
                agent_type='crew',
                enabled=False,
                settings={'current_workflow': None}
            )
            mock_update_status.assert_called_with("Crew Agent Disabled", is_agent_message=True)

    def test_handle_ai_response_with_code_blocks(self):
        # Test handling AI response that includes code blocks
        response_content = "Here is some code:\n```python\nprint('Hello World')\n```"
        additional_data = {}
        with patch.object(self.page, 'display_ai_message') as mock_display_ai, \
             patch.object(self.page, 'show_code_window') as mock_show_code_window, \
             patch.object(self.page, 'add_to_chat_history') as mock_add_history, \
             patch.object(self.page, 'save_chat_log') as mock_save_chat_log, \
             patch.object(self.page, 'update_status_message') as mock_update_status:
            self.page.handle_ai_response(response_content, additional_data)
            mock_display_ai.assert_called_once_with("")
            mock_show_code_window.assert_called_once_with("print('Hello World')", "python")
            mock_add_history.assert_called_once_with(
                self.page.current_chat_id,
                self.page.chats,
                {'role': 'assistant', 'content': "Here is some code:"}
            )
            mock_save_chat_log.assert_called_once_with(
                self.page.current_chat_id,
                self.page.chats[self.page.current_chat_id]
            )
            mock_update_status.assert_called_once_with("Response received", is_agent_message=True)

    def test_handle_ai_response_no_code_blocks(self):
        # Test handling AI response without code blocks
        response_content = "This is a simple response."
        additional_data = {}
        with patch.object(self.page, 'display_ai_message') as mock_display_ai, \
             patch.object(self.page, 'show_code_window') as mock_show_code_window, \
             patch.object(self.page, 'add_to_chat_history') as mock_add_history, \
             patch.object(self.page, 'save_chat_log') as mock_save_chat_log, \
             patch.object(self.page, 'update_status_message') as mock_update_status:
            self.page.handle_ai_response(response_content, additional_data)
            mock_display_ai.assert_called_once_with(response_content)
            mock_show_code_window.assert_not_called()
            mock_add_history.assert_called_once_with(
                self.page.current_chat_id,
                self.page.chats,
                {'role': 'assistant', 'content': response_content}
            )
            mock_save_chat_log.assert_called_once_with(
                self.page.current_chat_id,
                self.page.chats[self.page.current_chat_id]
            )
            mock_update_status.assert_called_once_with("Response received", is_agent_message=True)

    def test_clear_chat_with_active_chat(self):
        # Test clearing an active chat
        self.page.current_chat_id = "chat123"
        self.page.chats = {"chat123": {'messages': [{'role': 'user', 'content': 'Hi'}]}}
        with patch.object(self.page, 'save_chat_log') as mock_save_chat_log, \
             patch.object(self.page.chat_display, 'setMarkdown') as mock_set_markdown:
            self.page.clear_chat()
            self.assertEqual(self.page.chats["chat123"]['messages'], [])
            mock_save_chat_log.assert_called_once_with("chat123", self.page.chats["chat123"])
            mock_set_markdown.assert_called_once_with("")

    def test_clear_chat_no_active_chat(self):
        # Test clearing when there is no active chat
        self.page.current_chat_id = None
        with patch.object(QMessageBox, 'warning') as mock_warning:
            self.page.clear_chat()
            mock_warning.assert_called_once_with(
                self.page,
                "No Chat Selected",
                "No chat session is currently active."
            )

    @classmethod
    def tearDownClass(cls):
        # Clean up the QApplication after all tests
        cls.app.quit()

if __name__ == '__main__':
    unittest.main()

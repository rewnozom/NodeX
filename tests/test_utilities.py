import pytest
from unittest.mock import MagicMock
from ai_agent.utils.token_counter import (
    count_tokens_in_string, count_tokens_in_messages,
    update_token_counter
)

def test_token_counting():
    test_string = "This is a test string"
    token_count = count_tokens_in_string(test_string)
    assert token_count >= 1  # Just a sanity check

    test_messages = [
        {"role": "system", "content": "System message"},
        {"role": "user", "content": "User message"}
    ]
    message_tokens = count_tokens_in_messages(test_messages)
    assert message_tokens >= 1

def test_token_counter_update():
    message_widget = MagicMock()
    message_widget.toPlainText.return_value = "Test message"
    counter_label = MagicMock()

    update_token_counter(message_widget, counter_label)
    counter_label.setText.assert_called_once()
    args, _ = counter_label.setText.call_args
    assert "Tokens:" in args[0]

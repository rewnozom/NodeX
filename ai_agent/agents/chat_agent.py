#!/usr/bin/env python3
# ai_agent/agents/chat_agent.py

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ChatAgent(BaseAgent):
    """
    Standard chat agent implementation that provides direct model interaction
    with enhanced error handling and message validation.
    """
    
    # Supported model types for message-based interaction
    MESSAGE_BASED_MODELS = {
        'OpenAIChat', 
        'AzureChatOpenAI', 
        'ChatOpenAI',
        'AnthropicChat',
        'ClaudeChat'
    }

    def __init__(self, config: Dict[str, Any], model: Optional[Any] = None):
        """
        Initialize the chat agent.

        Args:
            config (Dict[str, Any]): Agent configuration
            model (Optional[Any]): Language model instance
        """
        super().__init__(config, model)
        self.name = "Standard Chat"
        self.description = "Standard chat interface with direct model interaction"
        self.message_history: List[Dict[str, Any]] = []
        self.last_response_time: Optional[datetime] = None
        self._initialize_chat_settings()

    def _initialize_chat_settings(self) -> None:
        """Initialize chat-specific settings from configuration."""
        try:
            self.max_history = self.config.get('max_history', 100)
            self.save_history = self.config.get('save_history', True)
            self.response_timeout = self.config.get('response_timeout', 30)
            logger.debug(f"Initialized chat settings for {self.name}")
        except Exception as e:
            logger.error(f"Error initializing chat settings: {e}")
            raise

    def process_message(self, messages: List[Dict[str, str]]) -> str:
        """
        Process messages using standard chat logic with enhanced error handling.

        Args:
            messages (List[Dict[str, str]]): List of messages to process

        Returns:
            str: The model's response

        Raises:
            ValueError: If model is not configured or messages are invalid
            RuntimeError: If processing fails
        """
        try:
            # Validate inputs
            if not self.model:
                raise ValueError("No model configured for chat agent")
            self.validate_messages(messages)

            # Determine model type and process accordingly
            model_name = self.model.__class__.__name__
            accepts_messages = model_name in self.MESSAGE_BASED_MODELS
            
            # Process message based on model type
            start_time = datetime.now()
            
            try:
                if accepts_messages:
                    response = self._process_message_based(messages)
                else:
                    response = self._process_text_based(messages)
                
                self.last_response_time = datetime.now()
                self._update_history(messages, response)
                
                logger.debug(
                    f"Message processed successfully by {model_name} "
                    f"in {(datetime.now() - start_time).total_seconds():.2f}s"
                )
                
                return self._format_response(response)
                
            except Exception as e:
                self.handle_error(e)
                raise RuntimeError(f"Failed to process message: {str(e)}")

        except Exception as e:
            logger.error(f"Error in chat agent {self.name}: {e}")
            raise

    def _process_message_based(self, messages: List[Dict[str, str]]) -> Any:
        """Handle message-based model processing."""
        try:
            return self.model(messages)
        except Exception as e:
            logger.error(f"Error in message-based processing: {e}")
            raise

    def _process_text_based(self, messages: List[Dict[str, str]]) -> Any:
        """Handle text-based model processing."""
        try:
            concatenated_messages = ' '.join(m['content'] for m in messages)
            if hasattr(self.model, 'invoke'):
                return self.model.invoke(concatenated_messages)
            return self.model(concatenated_messages)
        except Exception as e:
            logger.error(f"Error in text-based processing: {e}")
            raise

    def _format_response(self, response: Any) -> str:
        """Format the model's response into a string."""
        if isinstance(response, str):
            return response
        elif isinstance(response, dict) and 'content' in response:
            return response['content']
        elif hasattr(response, 'content'):
            return response.content
        return str(response)

    def _update_history(self, messages: List[Dict[str, str]], response: Any) -> None:
        """Update message history if enabled."""
        if self.save_history:
            current_time = datetime.now()
            history_entry = {
                'timestamp': current_time,
                'messages': messages,
                'response': response
            }
            self.message_history.append(history_entry)
            
            # Trim history if needed
            if len(self.message_history) > self.max_history:
                self.message_history = self.message_history[-self.max_history:]

    def clear_history(self) -> None:
        """Clear the message history."""
        self.message_history.clear()
        logger.debug(f"Cleared message history for {self.name}")

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get detailed information about the chat agent.

        Returns:
            Dict[str, Any]: Agent information dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": "chat",
            "capabilities": ["direct-chat"],
            "is_active": self.is_active,
            "model_type": self.model.__class__.__name__ if self.model else None,
            "last_response": self.last_response_time,
            "history_size": len(self.message_history),
            "error_count": self.error_count,
            "status": self.status
        }

    def reset(self) -> bool:
        """
        Reset the chat agent to initial state.

        Returns:
            bool: True if reset was successful
        """
        try:
            super().reset()
            self.clear_history()
            self.last_response_time = None
            return True
        except Exception as e:
            logger.error(f"Failed to reset chat agent: {e}")
            return False
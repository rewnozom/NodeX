# services/ai_service.py

from ai_agent.models.llm_models import get_model
from log.logger import logger

class AIService:
    def __init__(self, config):
        self.config = config
        self.client = self.initialize_client()

    def initialize_client(self):
        model_name = self.config.CHAT_MODEL
        temperature = self.config.CHAT_TEMPERATURE
        client = get_model(model_name, temperature=temperature)
        logger.info(f"AIService initialized with model: {model_name}")
        return client

    def get_response(self, messages):
        try:
            accepts_messages = self.client.__class__.__name__ in ['OpenAIChat', 'AzureChatOpenAI', 'ChatOpenAI']
            if accepts_messages:
                response = self.client(messages)
            else:
                concatenated_messages = ' '.join(m['content'] for m in messages)
                response = self.client.invoke(concatenated_messages) if hasattr(self.client, 'invoke') else self.client(concatenated_messages)

            if isinstance(response, str):
                response_content = response
            elif isinstance(response, dict) and 'content' in response:
                response_content = response['content']
            elif hasattr(response, 'content'):
                response_content = response.content
            else:
                response_content = str(response)

            return response_content
        except Exception as e:
            logger.error(f"Error getting response from model: {e}")
            raise e

    def update_model(self, model_name, temperature=None):
        self.client = get_model(model_name, temperature=temperature if temperature else self.config.CHAT_TEMPERATURE)
        logger.info(f"AIService updated to model: {model_name}")

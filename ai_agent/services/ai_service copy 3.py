from ai_agent.models.llm_models import get_model
from log.logger import logger

class AIService:
    def __init__(self, config):
        self.config = config
        self.client = self.initialize_client()
        self.current_agent = None
        self.load_agent_config()

    def initialize_client(self):
        model_name = self.config.CHAT_MODEL
        temperature = self.config.CHAT_TEMPERATURE
        client = get_model(model_name, temperature=temperature)
        logger.info(f"AIService initialized with model: {model_name}")
        return client

    def load_agent_config(self):
        """Load current agent configuration from config."""
        agent_config = self.config.get_agent_config()
        self.current_agent = agent_config.get('current_agent', 'chat')
        logger.info(f"Loaded agent configuration: {agent_config}")

    def update_agent(self, agent_type=None, enabled=None, settings=None):
        """
        Update the agent configuration and reinitialize if necessary.
        
        Args:
            agent_type (str, optional): Type of agent to switch to ('chat', 'developer', etc.)
            enabled (bool, optional): Whether the agent is enabled
            settings (dict, optional): Additional configuration updates to be placed in AGENT_CONFIG
        """
        try:
            current_config = self.config.get_agent_config()
            
            # Create updates dictionary
            updates = {
                'enabled': enabled if enabled is not None else current_config.get('enabled', False),
                'current_agent': agent_type or current_config.get('current_agent', 'chat')
            }

            # Handle settings updates correctly
            if settings:
                # Place settings directly in the config key
                updates['config'] = settings
                
                # Log the full update for debugging
                logger.debug(f"Agent update details - Type: {agent_type}, Enabled: {enabled}, Settings: {settings}")
            
            # Update the configuration
            self.config.update_agent_config(updates)
            
            # Reload agent configuration
            self.load_agent_config()
            
            # Reinitialize client if needed based on agent type
            if agent_type and agent_type != self.current_agent:
                self.client = self.initialize_client()
            
            logger.info(f"Agent updated successfully: {updates}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating agent: {e}")
            return False

    def get_response(self, messages):
        """Get response from the AI model."""
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
        """Update the AI model configuration."""
        self.client = get_model(model_name, temperature=temperature if temperature else self.config.CHAT_TEMPERATURE)
        logger.info(f"AIService updated to model: {model_name}")
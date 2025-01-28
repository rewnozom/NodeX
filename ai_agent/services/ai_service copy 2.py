from ai_agent.models.llm_models import get_model
from ai_agent.agents.agent_factory import AgentFactory
from log.logger import logger

class AIService:
    def __init__(self, config):
        self.config = config
        self.client = self.initialize_client()
        self.agent_factory = AgentFactory()
        self.current_agent = None
        self.load_agent_config()

    def initialize_client(self):
        model_name = self.config.CHAT_MODEL
        temperature = self.config.CHAT_TEMPERATURE
        client = get_model(model_name, temperature=temperature)
        logger.info(f"AIService initialized with model: {model_name}")
        return client

    def load_agent_config(self):
        """Load and initialize current agent configuration."""
        agent_config = self.config.get_agent_config()
        agent_type = agent_config.get('current_agent', 'chat')
        if agent_config.get('enabled', False):
            try:
                self.current_agent = self.agent_factory.create_agent(
                    agent_type=agent_type,
                    config=agent_config,
                    model=self.client
                )
                self.current_agent.activate()
                logger.info(f"Agent {agent_type} initialized and activated")
            except Exception as e:
                logger.error(f"Failed to initialize agent {agent_type}: {e}")
                self.current_agent = None
        else:
            self.current_agent = None
        logger.info(f"Loaded agent configuration: {agent_config}")

    def update_agent(self, agent_type=None, enabled=None, settings=None):
        """Update agent configuration and reinitialize if necessary."""
        try:
            current_config = self.config.get_agent_config()
            updates = {
                'enabled': enabled if enabled is not None else current_config.get('enabled', False),
                'current_agent': agent_type or current_config.get('current_agent', 'chat')
            }
            if settings:
                updates['config'] = settings
                logger.debug(f"Agent update details - Type: {agent_type}, Enabled: {enabled}, Settings: {settings}")
            
            self.config.update_agent_config(updates)
            self.load_agent_config()
            
            if agent_type and agent_type != current_config.get('current_agent'):
                self.client = self.initialize_client()
            
            logger.info(f"Agent updated successfully: {updates}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating agent: {e}")
            return False

    def get_response(self, messages):
        """Get response using active agent or direct model."""
        try:
            if self.current_agent and self.current_agent.is_running:
                logger.info(f"Processing message with {self.current_agent.__class__.__name__}")
                return self.current_agent.process_message(messages)
            
            logger.info("Processing message with direct model response")
            accepts_messages = self.client.__class__.__name__ in ['OpenAIChat', 'AzureChatOpenAI', 'ChatOpenAI']
            
            if accepts_messages:
                response = self.client(messages)
            else:
                concatenated_messages = ' '.join(m['content'] for m in messages)
                response = self.client.invoke(concatenated_messages) if hasattr(self.client, 'invoke') else self.client(concatenated_messages)

            return self._format_response(response)
            
        except Exception as e:
            logger.error(f"Error getting response: {e}")
            raise e

    def _format_response(self, response):
        """Format model response to string."""
        if isinstance(response, str):
            return response
        elif isinstance(response, dict) and 'content' in response:
            return response['content']
        elif hasattr(response, 'content'):
            return response.content
        return str(response)

    def update_model(self, model_name, temperature=None, llm=None):
        """Update model configuration."""
        if llm:
            self.client = llm
        else:
            self.client = get_model(model_name, temperature=temperature if temperature else self.config.CHAT_TEMPERATURE)
        
        if self.current_agent:
            self.current_agent.model = self.client
            
        logger.info(f"Model updated to: {model_name}")
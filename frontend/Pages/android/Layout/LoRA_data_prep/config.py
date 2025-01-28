# config.py

import os
# LMStudio does not require an API key
LMSTUDIO_API_KEY = None  # Set this to None or omit

# Ollama does not require an API key
OLLAMA_API_ENDPOINT = "http://localhost:your_ollama_port"
OLLAMA_API_ENDPOINT = "http://localhost:11434"

# Ensure critical configurations are set
class Config:
    def __init__(self):
        # Load from environment variables or use the default values
        self.disable_color = os.getenv('DISABLE_COLOR_PRINTING', 'False').lower() in ('true', '1', 't')
        self.debug = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
        self.log_directory = os.getenv('LOG_DIR', os.path.join(os.getcwd(), 'logs'))
        self.logging_rest_api = os.getenv('LOGGING_REST_API', 'False').lower() in ('true', '1', 't')

        # API keys
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_mistral_api_key_here")
        self.API_KEY_ANTHROPIC = os.getenv("API_KEY_ANTHROPIC", "your_mistral_api_key_here")
        self.API_KEY_GROQ = os.getenv("API_KEY_GROQ", "your_mistral_api_key_here")
        self.MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "your_mistral_api_key_here")
        
        # Other settings
        self.CHAT_MODEL = os.getenv("CHAT_MODEL", "LM Studio Model")
        self.CHAT_TEMPERATURE = float(os.getenv("CHAT_TEMPERATURE", 0.65))
        self.UTILITY_MODEL = os.getenv("UTILITY_MODEL", "LM Studio Model")
        self.UTILITY_TEMPERATURE = float(os.getenv("UTILITY_TEMPERATURE", 0.65))
        self.EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "HuggingFace Embeddings")

        self.ENABLE_HISTORY = os.getenv("ENABLE_HISTORY", "False").lower() in ('true', '1', 't')
        self.ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "True").lower() in ('true', '1', 't')

        self.MEMORY_FILE = os.getenv("MEMORY_FILE", "memory.json")
        self.SYSTEM_PROMPT_FILE = os.getenv("SYSTEM_PROMPT_FILE", "system_prompt.txt")
        self.DATA_MEMORY_FOLDER = os.getenv("DATA_MEMORY_FOLDER", "datamemory")
        self.SAVED_MODULES_FOLDER = os.getenv("SAVED_MODULES_FOLDER", "savedmodules")

    def get_logs_dir(self):
        return self.log_directory

    def get_logging_rest_api(self):
        return self.logging_rest_api

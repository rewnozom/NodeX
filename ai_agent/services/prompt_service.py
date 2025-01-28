# services/prompt_service.py


import os
from ai_agent.config.prompt_manager import save_system_prompt
from log.logger import logger

class PromptService:
    def __init__(self, config):
        self.config = config
        self.system_prompts = []

    def load_system_prompts(self):
        try:
            system_prompts_dir = "./System_Prompts"
            self.system_prompts = [
                filename[:-3] for filename in os.listdir(system_prompts_dir) if filename.endswith(".md")
            ]
            logger.info(f"Loaded system prompts: {self.system_prompts}")
        except Exception as e:
            logger.error(f"Error loading system prompts: {e}")
            self.system_prompts = []

    def get_system_prompt(self, prompt_name):
        try:
            file_path = os.path.join("./System_Prompts", f"{prompt_name}.md")
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                save_system_prompt(content)
                return content
        except FileNotFoundError:
            logger.warning(f"System prompt file '{prompt_name}.md' not found.")
            return None
        except Exception as e:
            logger.error(f"Error loading system prompt '{prompt_name}': {e}")
            return None

    def prepare_messages(self, system_message, user_message, memory=None):
        messages = [{"role": "system", "content": system_message}]
        if self.config.ENABLE_MEMORY and memory:
            messages += [{"role": m["role"], "content": m["content"]} for m in memory if m["content"]]
        messages.append({"role": "user", "content": user_message})
        return messages

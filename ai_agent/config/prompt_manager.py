# AI_Agent/config/prompt_manager.py

import os
import logging



# Dynamic path setup with fallback
SYSTEM_PROMPT_DIR = os.getenv("SYSTEM_PROMPT_DIR", "./System_Prompts")
SYSTEM_PROMPT_PATH = os.path.join(SYSTEM_PROMPT_DIR, "system_prompt.txt")

logger = logging.getLogger(__name__)

# Ensure the system prompt directory exists
os.makedirs(SYSTEM_PROMPT_DIR, exist_ok=True)


def save_system_prompt(prompt: str) -> None:
    """Save the current system prompt to system_prompt.txt."""
    try:
        with open(SYSTEM_PROMPT_PATH, 'w', encoding='utf-8') as file:
            file.write(prompt)
        logger.info("System prompt saved successfully to system_prompt.txt.")
    except Exception as e:
        logger.error(f"Unexpected error saving system prompt: {e}")


def load_system_prompt() -> str:
    """Load the current system prompt from system_prompt.txt or fallback to default."""
    try:
        if os.path.exists(SYSTEM_PROMPT_PATH):
            with open(SYSTEM_PROMPT_PATH, 'r', encoding='utf-8') as file:
                prompt = file.read()
                logger.info("System prompt loaded successfully from system_prompt.txt.")
                return prompt
        else:
            logger.warning("system_prompt.txt not found. Loading default system prompt.")
            return load_default_system_prompt()
    except Exception as e:
        logger.error(f"Unexpected error loading system prompt: {e}")
        return "You are a helpful, smart, kind, and efficient AI assistant."


def load_default_system_prompt() -> str:
    """Load the default system prompt from Original.md or fallback to hardcoded default."""
    default_prompt_path = os.path.join(SYSTEM_PROMPT_DIR, "Original.md")
    try:
        if os.path.exists(default_prompt_path):
            with open(default_prompt_path, 'r', encoding='utf-8') as file:
                prompt = file.read()
                logger.info("Default system prompt loaded successfully from Original.md.")
                # Save it as the current prompt for future use
                save_system_prompt(prompt)
                return prompt
        else:
            logger.warning("Original.md not found. Using fallback default system prompt.")
            default_prompt = "You are a helpful, smart, kind, and efficient AI assistant."
            save_system_prompt(default_prompt)
            return default_prompt
    except Exception as e:
        logger.error(f"Error loading default system prompt: {e}")
        return "You are a helpful, smart, kind, and efficient AI assistant."


def list_markdown_files(directory: str) -> list:
    """List all markdown files in a given directory."""
    try:
        return [file[:-3] for file in os.listdir(directory) if file.endswith(".md")]
    except Exception as e:
        logger.error(f"Error listing markdown files in directory {directory}: {e}")
        return []


def load_all_system_prompts() -> list:
    """Load all markdown system prompts from the specified directory."""
    prompts = list_markdown_files(SYSTEM_PROMPT_DIR)
    logger.info(f"Found {len(prompts)} system prompts in {SYSTEM_PROMPT_DIR}.")
    return prompts


def load_specific_system_prompt(prompt_name: str) -> str:
    """Load a specific system prompt by its name."""
    prompt_file_path = os.path.join(SYSTEM_PROMPT_DIR, f"{prompt_name}.md")
    try:
        if os.path.exists(prompt_file_path):
            with open(prompt_file_path, 'r', encoding='utf-8') as file:
                prompt = file.read()
                logger.info(f"System prompt '{prompt_name}' loaded successfully.")
                # Optionally save it as the current prompt
                save_system_prompt(prompt)
                return prompt
        else:
            logger.warning(f"System prompt file '{prompt_name}.md' not found.")
            return None
    except Exception as e:
        logger.error(f"Error loading system prompt '{prompt_name}': {e}")
        return None


def prepare_messages(system_message: str, user_message: str, config, memory=None) -> list:
    """Prepare messages for the AI model."""
    messages = [{"role": "system", "content": system_message}]
    if config.ENABLE_MEMORY and memory:
        messages.extend(
            {"role": mem["role"], "content": mem["content"]}
            for mem in memory if mem.get("content")
        )
    messages.append({"role": "user", "content": user_message})
    logger.debug(f"Prepared messages: {messages}")
    return messages


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

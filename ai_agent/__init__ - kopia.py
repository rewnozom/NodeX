# AI_Agent/__init__.py

from ai_agent.memory.memory_manager import save_memory, load_memory
from ai_agent.config.prompt_manager import save_system_prompt, load_system_prompt
from ai_agent.code_block_manager.code_block_manager import (
    save_code_block, update_code_block_in_datamemory, read_file_from_datamemory
)
from ai_agent.chat_manager.chat_manager import (
    load_history, load_chat_log, save_chat_log, delete_selected_chat
)
from ai_agent.memory.embedding.embedding_manager import load_embedding
from ai_agent.utils.helpers import insert_file_name, auto_suggest_files
from ai_agent.widgets.code_display import show_code_window, copy_to_clipboard
from ai_agent.models.llm_models import get_model, MODELS
# Assuming generate_data_and_save_excel is defined in auto_gen.py
from ai_agent.generation_manager.auto_gen import generate_data_and_save_excel as auto_generate_data
from ai_agent.config.ai_config import Config
from ai_agent.utils.token_counter import count_tokens_in_string, count_tokens_in_messages


from .memory.memory_manager import save_memory, load_memory, add_memory, remove_memory
from .config.prompt_manager import save_system_prompt, load_system_prompt
from .code_block_manager.code_block_manager import (
    save_code_block,
    update_code_block_in_datamemory,
    read_file_from_datamemory
)
from .generation_manager.auto_gen import (
    save_to_excel,
    generate_data_and_save_excel
)
from .chat_manager.chat_manager import (
    load_history,
    load_chat_log,
    save_chat_log,
    load_selected_chat,
    rename_selected_chat,
    delete_selected_chat,
    new_chat
)
from .memory.embedding.embedding_manager import load_embedding
from .utils.helpers import insert_file_name, auto_suggest_files
from .widgets.code_display import show_code_window, copy_to_clipboard
from .models.llm_models import get_model, MODELS

from .config.ai_config import Config
from .utils.token_counter import count_tokens_in_string, count_tokens_in_messages

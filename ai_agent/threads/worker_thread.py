# ai_agent/threads/worker_thread.py

import re
from PySide6.QtCore import QThread, Signal
from log.logger import logger
from ai_agent.utils.code_extractor import CodeBlockExtractor  # Import CodeBlockExtractor
from ai_agent.services.data_service import DataService
from ai_agent.services.ai_service import AIService

class WorkerThread(QThread):
    response_ready = Signal(str, dict)       # Emits AI response content and additional data
    error_occurred = Signal(str)             # Emits error messages
    code_blocks_found = Signal(list)         # Emits list of code blocks found in the response

    def __init__(self, messages, ai_service):
        """
        Initialize the WorkerThread.

        Args:
            messages (list): The list of messages to send to the AI model.
            ai_service (AIService): An instance of AIService to handle AI interactions.
        """
        super().__init__()
        self.messages = messages
        self.ai_service = ai_service
        self.code_extractor = CodeBlockExtractor()  # Instantiate CodeBlockExtractor

    def run(self):
        """
        Execute the thread's activity: fetch AI response, process it, and emit signals.
        """
        try:
            # Get the response from the AI model
            response_content = self.ai_service.get_response(self.messages)

            # Extract code blocks from the response using CodeBlockExtractor
            code_blocks = self.code_extractor.extract_code_blocks(response_content)  # Correctly call the method
            if code_blocks:
                self.code_blocks_found.emit(code_blocks)  # Emit the found code blocks

            # Handle data list saving
            saved_file = DataService.auto_generate_data(response_content)
            if saved_file:
                logger.info(f"Data list saved to {saved_file}")

            # Emit the AI response
            self.response_ready.emit(response_content, {})
        
        except Exception as e:
            logger.error(f"Error in AI response: {e}")
            self.error_occurred.emit(str(e))

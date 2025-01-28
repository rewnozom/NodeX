# ./frontend/pages/qframes/helper/workers.py

from PySide6.QtCore import QObject, Signal
from typing import Callable, Any, Optional
from Utils.llm_util.llm_sorted_func import (
    process_files,
    process_file,
    process_function,
    get_md_files
)
from log.logger import logger

class WorkerSignals(QObject):
    """Base signals class for worker threads."""
    finished = Signal()
    error = Signal(str)
    result = Signal(object)
    progress = Signal(str, str)
    status_changed = Signal(str)

class BaseWorker(QObject):
    """Base worker class with common functionality."""
    def __init__(self):
        super().__init__()
        self._is_running = True
        self.signals = WorkerSignals()

    def stop(self):
        """Stop the worker gracefully."""
        self._is_running = False
        self.signals.status_changed.emit("Stopped")
        logger.info("Worker stopped")

    @property
    def is_running(self) -> bool:
        return self._is_running

class ProcessingWorker(BaseWorker):
    """Unified worker for file processing and code analysis tasks."""
    
    def __init__(self, 
                 input_dir: str,
                 output_dir: str,
                 system_prompt: str,
                 llm: Any,
                 worker_type: str = "file_processing",
                 custom_processor: Optional[Callable] = None):
        """
        Initialize the processing worker.
        
        Args:
            input_dir: Input directory path
            output_dir: Output directory path
            system_prompt: System prompt for LLM
            llm: Language model instance
            worker_type: Type of processing ("file_processing" or "code_analysis")
            custom_processor: Optional custom processing function
        """
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.system_prompt = system_prompt
        self.llm = llm
        self.worker_type = worker_type
        self.custom_processor = custom_processor
        
        # Add specific signals
        self.progress_update = Signal(str, str)
        self.processing_finished = Signal()

        logger.debug(f"ProcessingWorker initialized with type: {worker_type}")

    def run(self):
        """Run the processing task."""
        try:
            logger.info(f"Starting {self.worker_type} processing")
            self.signals.status_changed.emit("Running")
            
            # Validate input directory contains required files
            if self.worker_type == "file_processing":
                files = get_md_files(self.input_dir)
                if not files:
                    raise ValueError("No markdown files found in input directory")
            
            # Choose the appropriate processor
            processor = self.custom_processor or process_files
            
            # Run the processor with progress tracking
            processor(
                input_dir=self.input_dir,
                output_dir=self.output_dir,
                system_prompt=self.system_prompt,
                llm=self.llm,
                progress_callback=self._handle_progress,
                is_running=lambda: self._is_running
            )
            
            if self._is_running:
                self.processing_finished.emit()
                self.signals.finished.emit()
                logger.info(f"{self.worker_type} processing completed successfully")
            else:
                logger.info(f"{self.worker_type} processing stopped by user")
            
        except Exception as e:
            error_msg = f"{self.worker_type} processing error: {str(e)}"
            logger.error(error_msg)
            self.signals.error.emit(error_msg)
        finally:
            self.signals.status_changed.emit("Completed")
            logger.debug(f"{self.worker_type} processing task finished")

    def _handle_progress(self, item_name: str, status: str):
        """Handle progress updates with logging."""
        if self._is_running:
            self.progress_update.emit(item_name, status)
            logger.debug(f"Progress - {item_name}: {status}")

class FileAnalysisWorker(ProcessingWorker):
    """Specialized worker for file analysis tasks."""
    
    def __init__(self, 
                 input_dir: str,
                 output_dir: str,
                 system_prompt: str,
                 llm: Any):
        super().__init__(
            input_dir=input_dir,
            output_dir=output_dir,
            system_prompt=system_prompt,
            llm=llm,
            worker_type="file_analysis",
            custom_processor=process_file
        )
        logger.debug("FileAnalysisWorker initialized")

class FunctionAnalysisWorker(ProcessingWorker):
    """Specialized worker for function analysis tasks."""
    
    def __init__(self, 
                 input_dir: str,
                 output_dir: str,
                 system_prompt: str,
                 llm: Any):
        super().__init__(
            input_dir=input_dir,
            output_dir=output_dir,
            system_prompt=system_prompt,
            llm=llm,
            worker_type="function_analysis",
            custom_processor=process_function
        )
        logger.debug("FunctionAnalysisWorker initialized")
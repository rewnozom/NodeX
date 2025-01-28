# ./src/__init__.py

from ._controller import Controller

from ._full_backend_ import (
    # Core Classes
    CodeParser,
    CodeFormatter,
    CodeIntegrator,
    CodeRemover,
    ConfigManager,
    FileManager,
    
    # Extractors
    ClassAndMethodNameExtractor,
    ClassNameExtractor,
    CodeBlockExtractor,
    CodeExtractor,
    ExtractAndRemoveSpecialImports,
    ModulePathExtractor,
    
    # Processors
    CodeBlockProcessor,
    CodeRemovalProcessor,
    LlmProcessor,
    ProcessCodeBlock,
    ProcessCodeBlocks,
    
    # Validators and Utilities
    SyntaxValidator,
    PathValidator,
    DiffGenerator,
    ImportMerger,
    
    # Finders
    FunctionFinder,
    MethodFinder,
    FindClass,
    
    # Comment Handlers
    CommentExtractor,
    InitialCommentRemover,
    ReAddInitialComments
)

from .Extractorz import CSVEx, MarkdownEx, reverse_markdown_extraction, reverse_csv_extraction
from .workers.extraction_worker import ExtractionWorker
from .workers.extraction_manager import ExtractionManager

# Aggregate all public exports
__all__ = [
    # _full_backend_ exports
    'CodeParser', 'CodeFormatter', 'CodeIntegrator', 'CodeRemover', 'ConfigManager', 'FileManager',
    'ClassAndMethodNameExtractor', 'ClassNameExtractor', 'CodeBlockExtractor', 'CodeExtractor',
    'ExtractAndRemoveSpecialImports', 'ModulePathExtractor',
    'CodeBlockProcessor', 'CodeRemovalProcessor', 'LlmProcessor', 'ProcessCodeBlock', 'ProcessCodeBlocks',
    'SyntaxValidator', 'PathValidator', 'DiffGenerator', 'ImportMerger',
    'FunctionFinder', 'MethodFinder', 'FindClass',
    'CommentExtractor', 'InitialCommentRemover', 'ReAddInitialComments',
    
    # Extractorz exports
    'CSVEx', 'MarkdownEx', 'reverse_csv_extraction', 'reverse_markdown_extraction',
    'ExtractionWorker', 'ExtractionManager',
    
    # Controller export
    'Controller',
]

# Version information
__version__ = '2.c.2'
__author__ = 'Tobias Raanaes'

# Optional: Set default logging configuration
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

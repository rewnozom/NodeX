# ./src/live/_controller.py

import difflib
from typing import Tuple, Optional, Dict, List

from logging import LoggerManager

from backends._full_backend_ import (
    FileManager, ConfigManager, CodeBlockExtractor, CodeParser, 
    ModulePathExtractor, CommentExtractor, ReAddInitialComments, CodeFormatter,
    CodeRemover, CodeIntegrator, SyntaxValidator, LlmProcessor, CodeRemovalProcessor
)

# Import everything from the backend

class Controller:
    """
    Orchestrates the overall process for extracting, processing, and updating code blocks.
    """

    def __init__(self, config_manager=None):
        # Initialize Config Manager
        self.config_manager = config_manager or ConfigManager()

        # Initialize Logger Manager
        self.logger_manager = LoggerManager(self.config_manager)
        self.logger = self.logger_manager.get_logger()

        # Initialize File Manager
        self.file_manager = FileManager(self.logger)

        # Initialize Parsers and Processors
        self.parser = CodeParser(self.logger)
        self.extractor = CodeBlockExtractor(self.config_manager)  # Updated
        self.module_path_extractor = ModulePathExtractor(self.config_manager)
        self.code_validator = SyntaxValidator(self.logger)
        self.code_formatter = CodeFormatter(enable_formatting=self.config_manager.get_config_value("enable_formatting", True), logger=self.logger)
        self.code_remover = CodeRemover(logger=self.logger, parser=self.parser, enable_removal=self.config_manager.get_config_value("enable_removal", True))
        self.code_integrator = CodeIntegrator(logger=self.logger, parser=self.parser, enable_integration=self.config_manager.get_config_value("enable_integration", True))

        # Initialize Additional Components
        self.code_removal_processor = CodeRemovalProcessor(
            file_manager=self.file_manager,
            parser=self.parser,
            code_remover=self.code_remover,
            validator=self.code_validator,
            formatter=self.code_formatter,
            config_manager=self.config_manager,
            logger=self.logger
        )

        # Initialize LLM Processor (modified to work without GUI elements)
        self.llm_processor = LlmProcessor(self)

    def run_step_by_step(self):
        """
        Executes the process in sequential steps:
        1. Extract code blocks from the input file.
        2. Process each code block based on its action (remove/update).
        """
        # Step 1: Extract code blocks
        self.logger.info("Step 1: Extracting code blocks...")
        input_file = self.config_manager.get_config_value("input_file", "")
        if not input_file:
            self.logger.error("Input file path is not specified in the configuration.")
            return

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                input_text = f.read()
        except Exception as e:
            self.logger.error(f"Failed to read input file {input_file}: {e}")
            return

        code_blocks = self.extractor.extract_code_blocks(input_text)
        self.logger.info(f"Extracted {len(code_blocks)} code blocks.")

        # Step 2: Process each code block
        self.process_code_blocks(code_blocks)

    def process_code_blocks(self, code_blocks: List[Dict]):
        """
        Processes a list of code blocks.
        """
        for idx, block in enumerate(code_blocks):
            self.logger.info(f"Processing code block {idx + 1}...")
            action = block.get("action")
            if action == "remove":
                success, message, diff = self.process_removal_block(block, return_diff=True)
            elif action == "update":
                success, message, diff = self.process_code_block(block, return_diff=True)
            else:
                self.logger.error(f"Unknown action: {action}")
                success = False
                message = f"Unknown action: {action}"
                diff = None

            if success:
                self.logger.info(f"Successfully processed code block {idx + 1}: {message}")
                if diff:
                    self.logger.debug(f"Diff for code block {idx + 1}:\n{diff}")
            else:
                self.logger.error(f"Failed to process code block {idx + 1}: {message}")

    def process_llm_output(self, text: str, auto_run: bool = False) -> List[Dict]:
        """
        Processes LLM output text, extracts code blocks, and processes them.
        If auto_run is True, automatically processes all code blocks.
        """
        if not text:
            self.logger.warning('No text provided for processing.')
            return []

        code_blocks = self.extractor.extract_code_blocks(text)

        if not code_blocks:
            self.logger.warning('No valid code blocks found in the input.')
            return []

        self.logger.info(f"Processing {'all' if auto_run else 'selected'} {len(code_blocks)} code blocks.")

        if auto_run:
            self.process_code_blocks(code_blocks)

        return code_blocks

    def process_removal_block(self, block: Dict, return_diff: bool = False) -> Tuple[bool, str, Optional[str]]:
        """
        Processes a code removal block.
        """
        # Delegate to the CodeRemovalProcessor
        success, message, diff = self.code_removal_processor.process_removal_block(block, return_diff)
        return success, message, diff

    def process_code_block(self, block: Dict, return_diff: bool = False) -> Tuple[bool, str, Optional[str]]:
        """
        Processes a single code block for updates or additions.
        """
        # Extract necessary information from the block
        module_path = block.get("module_path")
        new_code_block = block.get("code_block")
        updated_methods = block.get("updated_methods", {})
        imports = block.get("imports", [])

        self.logger.debug(f"Processing module: {module_path}")

        # Validate and process module path
        if not module_path:
            self.logger.error("Module path is missing in the code block.")
            return False, "Module path is missing in the code block.", None
        
        # Use the updated ModulePathExtractor to process the module path
        processed_module_path = self.module_path_extractor.process_module_path(module_path)
        self.logger.debug(f"Processed module path: {processed_module_path}")

        # Use the processed_module_path for further operations
        if not self.file_manager.validate_path(processed_module_path):
            if self.config_manager.get_config_value("create_missing_modules", True):
                self.logger.warning(
                    f"Module {processed_module_path} does not exist. Creating new module."
                )
                try:
                    self.file_manager.create_module(processed_module_path)
                except Exception as e:
                    self.logger.error(f"Error creating module {processed_module_path}: {e}")
                    return False, f"Error creating module {processed_module_path}: {e}", None
            else:
                self.logger.error(f"Module {processed_module_path} does not exist.")
                return False, f"Module {processed_module_path} does not exist.", None

        try:
            original_code = self.file_manager.read_file(processed_module_path)
        except Exception as e:
            self.logger.error(f"Failed to read module {processed_module_path}: {e}")
            return False, f"Failed to read module {processed_module_path}: {e}", None

        # Parse existing code into AST
        try:
            existing_tree = self.parser.parse_code(original_code)
        except SyntaxError as e:
            self.logger.error(f"Syntax error in existing code: {e}")
            return False, f"Syntax error in existing code: {e}", None

        # Parse new code into AST
        try:
            new_tree = self.parser.parse_code(new_code_block)
        except SyntaxError as e:
            self.logger.error(f"Syntax error in new code block: {e}")
            return False, f"Syntax error in new code block: {e}", None

        # Collect and merge imports
        self.logger.info("Collecting and merging imports...")
        self.code_integrator.collect_and_merge_imports(existing_tree, new_tree)

        # Integrate new classes/functions
        self.logger.info("Integrating new classes/functions...")
        new_code_nodes = new_tree.body  # Assume that new_tree has the new nodes
        self.code_integrator.integrate_nodes(existing_tree, new_code_nodes)

        # Integrate updated methods if any
        if block.get("class_name") and updated_methods:
            class_name = block.get("class_name")
            class_node = self.parser.find_class(existing_tree, class_name)
            if class_node:
                self.logger.info(f"Integrating updated methods into class {class_name}...")
                for method_name, method_code in updated_methods.items():
                    method_block = {
                        "action": "update",
                        "module_path": processed_module_path,
                        "class_name": class_name,
                        "method_name": method_name,
                        "language": "python",
                        "code_block": method_code,
                        "imports": imports,
                        "updated_methods": {}
                    }
                    success, message, diff = self.process_code_block(method_block, return_diff)
                    if not success:
                        self.logger.error(f"Failed to update method {method_name} in class {class_name}: {message}")
            else:
                self.logger.error(
                    f"Class {class_name} not found in existing code."
                )
                return False, f"Class {class_name} not found in existing code.", None

        # Convert AST back to code
        try:
            updated_code_body = self.parser.ast_to_code(existing_tree)
        except Exception as e:
            self.logger.error(f"Failed to convert AST to code: {e}")
            return False, f"Failed to convert AST to code: {e}", None

        # Re-add initial comments if necessary
        initial_comments, _ = self.extract_initial_comments(original_code)
        updated_code = self.re_add_initial_comments(initial_comments, updated_code_body)

        # Validate updated code syntax
        self.logger.info("Validating updated code syntax...")
        if not self.code_validator.validate_syntax_strict(updated_code, processed_module_path):
            return False, "Updated code has syntax errors.", None

        # Format code if necessary
        if self.config_manager.get_config_value("enable_formatting", True) and not self.config_manager.get_config_value("preserve_formatting", True):
            self.logger.info("Formatting the code with Black...")
            updated_code = self.code_formatter.format_code(updated_code)
        else:
            self.logger.info("Preserving original code formatting.")

        # Write updated code
        try:
            self.file_manager.write_file(processed_module_path, updated_code)
            self.logger.info(f"Module {processed_module_path} has been updated.")
        except Exception as e:
            self.logger.error(f"Failed to write updated code to {processed_module_path}: {e}")
            return False, f"Failed to write updated code to {processed_module_path}: {e}", None

        # If diff is requested, compute and return it
        if return_diff:
            try:
                original_lines = original_code.splitlines(keepends=True)
                updated_lines = updated_code.splitlines(keepends=True)
                diff = ''.join(difflib.unified_diff(
                    original_lines,
                    updated_lines,
                    fromfile='original',
                    tofile='updated',
                    lineterm=''
                ))
                self.logger.debug("Generated diff for the code block.")
                return True, f"Updated module {processed_module_path}.", diff
            except Exception as e:
                self.logger.error(f"Failed to generate diff: {e}")
                return True, f"Updated module {processed_module_path}, but failed to generate diff.", None

        return True, f"Updated module {processed_module_path}.", None

    def extract_initial_comments(self, code: str) -> Tuple[List[str], str]:
        """
        Extracts initial comments from the code.
        """
        # Use the CommentExtractor class
        comment_extractor = CommentExtractor()
        initial_comments, remaining_code = comment_extractor.extract_initial_comments(code)
        return initial_comments, remaining_code

    def re_add_initial_comments(self, comments: List[str], code: str) -> str:
        """
        Re-adds the initial comments to the code.
        """
        # Use the ReAddInitialComments class
        re_adder = ReAddInitialComments()
        updated_code = re_adder.re_add_initial_comments(comments, code)
        return updated_code

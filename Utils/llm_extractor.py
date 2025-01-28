# ./LLM_Output_Extractor/llm_output_extractor.py

import ast
import json
import logging
import os
import re
import shutil
from typing import List, Dict, Tuple, Any

import astor
import black  # For code formatting
from markdown_it import MarkdownIt  # Markdown parser

# Configuration Settings
CONFIG = {
    "input_file": "./testing/test_llm_output.md",  # Updated path
    "output_directory": "./",              # Updated directory
    "theme": "dark",                       # Updated theme
    "DEBUG_WORKFLOW": True,
    "enable_version_control": False,
    "strict_parsing": True,
    "logging_level": "DEBUG",
    "preserve_formatting": True,
    "enable_backup": True,
    "create_missing_modules": True,
}

# Logger Manager
class LoggerManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        log_level_str = CONFIG.get("logging_level", "DEBUG").upper()
        log_level = getattr(logging, log_level_str, logging.DEBUG)

        self.logger = logging.getLogger("DeveloperEfficiencyTool")
        self.logger.setLevel(log_level)

        # Avoid adding multiple handlers
        if not self.logger.handlers:
            # Create handlers
            log_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "app.log"
            )
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)

            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)

            # Create formatters and add to handlers
            formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # Add handlers to the logger
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger

    def close_handlers(self):
        """
        Closes all handlers to release resources.
        Useful for clean shutdowns.
        """
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

# File Manager
class FileManager:
    def __init__(self):
        self.logger = LoggerManager().get_logger()
        self.enable_backup = CONFIG.get("enable_backup", True)

    def read_file(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.logger.debug(f"Read file: {file_path}")
            return content
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            raise

    def create_module(self, file_path: str):
        """
        Creates a new module file with a basic template if it does not exist.
        """
        try:
            self.ensure_directory(file_path)
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    # Basic module template
                    f.write("# Auto-generated module\n\n")
                    f.write("import logging\n\n")
                    f.write(f"class {self.extract_class_name(file_path)}:\n")
                    f.write("    def __init__(self):\n")
                    f.write("        pass\n")
                self.logger.debug(f"Created new module: {file_path}")
            else:
                self.logger.debug(f"Module already exists: {file_path}")
        except Exception as e:
            self.logger.error(f"Error creating module {file_path}: {e}")
            raise

    def extract_class_name(self, file_path: str) -> str:
        """
        Extracts the class name from the file path, converting to CamelCase.
        """
        base_name = os.path.basename(file_path)
        class_name = ''.join(word.capitalize() for word in os.path.splitext(base_name)[0].split('_'))
        return class_name

    def write_file(self, file_path, content):
        try:
            self.ensure_directory(file_path)
            if self.enable_backup and os.path.exists(file_path):
                self.backup_file(file_path)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.logger.debug(f"Wrote to file: {file_path}")
        except Exception as e:
            self.logger.error(f"Error writing to file {file_path}: {e}")
            raise

    def backup_file(self, file_path):
        try:
            backup_path = f"{file_path}.bak"
            shutil.copy(file_path, backup_path)
            self.logger.debug(
                f"Backup created for {file_path} at {backup_path}"
            )
        except Exception as e:
            self.logger.error(f"Error creating backup for {file_path}: {e}")
            raise

    def validate_path(self, file_path):
        exists = os.path.isfile(file_path)
        self.logger.debug(f"Validating path {file_path}: Exists={exists}")
        return exists

    def ensure_directory(self, file_path):
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory)
                self.logger.debug(f"Created directory: {directory}")
            except Exception as e:
                self.logger.error(f"Error creating directory {directory}: {e}")
                raise

# Code Block Extractor
class CodeBlockExtractor:
    """
    Extracts code blocks from LLM outputs and prepares them for integration.
    """

    def __init__(self, input_file: str = None):
        self.input_file = input_file
        self.logger = LoggerManager().get_logger()
        self.md_parser = MarkdownIt()

    def get_code_blocks(self) -> List[Dict[str, Any]]:
        """
        Reads the input file and extracts code blocks.
        """
        code_blocks = []
        if self.input_file:
            input_text = self.read_input_file()
            code_blocks.extend(self.extract_code_blocks(input_text))
        return code_blocks

    def read_input_file(self) -> str:
        """
        Reads the input file and returns its content.
        """
        try:
            with open(self.input_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.logger.debug(f"Read input file: {self.input_file}")
            return content
        except Exception as e:
            self.logger.error(f"Error reading file {self.input_file}: {e}")
            return ""

    def extract_code_blocks(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts code blocks from Markdown content using markdown-it-py.
        Returns a list of dictionaries representing the code blocks.
        """
        code_blocks = []
        tokens = self.md_parser.parse(text)

        # Iterate over parsed tokens to extract code blocks
        for token in tokens:
            if token.type == 'fence':  # 'fence' token represents a code block in Markdown
                language = token.info.strip()
                code = token.content.strip()

                if language.lower() == "json":
                    # Parse JSON removal instructions
                    removal_instructions = self.parse_removal_json(code)
                    if removal_instructions:
                        code_blocks.append({
                            "action": "remove",
                            "removal_instructions": removal_instructions
                        })
                else:
                    # Assume it's a code block to update
                    module_path = self.extract_module_path(code)
                    if module_path:
                        code = self.remove_initial_comment(code)
                    imports, code = self.extract_and_remove_special_imports(code)
                    class_name, method_name = self.extract_class_and_method_names(code)
                    updated_methods = self.extract_updated_methods(code)
                    code = self.handle_unchanged_parts(code)

                    code_blocks.append({
                        "action": "update",
                        "module_path": module_path,
                        "class_name": class_name,
                        "method_name": method_name,
                        "language": language,
                        "code_block": code,
                        "imports": imports,
                        "updated_methods": updated_methods,
                    })

        self.logger.debug(f"Extracted {len(code_blocks)} code blocks.")
        return code_blocks

    def parse_removal_json(self, json_code: str) -> Dict[str, Any]:
        """
        Parses the JSON code block to extract removal instructions,
        handling dirty JSON.
        """
        try:
            # Try parsing the JSON code directly
            removal_data = json.loads(json_code)
            self.logger.debug(f"Parsed removal JSON: {removal_data}")
            return removal_data
        except json.JSONDecodeError as e:
            self.logger.warning(f"Standard JSON parsing failed: {e}")
            # Attempt to parse dirty JSON
            removal_data = self.parse_dirty_json(json_code)
            if removal_data:
                self.logger.debug(f"Parsed dirty JSON successfully: {removal_data}")
                return removal_data
            else:
                self.logger.error("Failed to parse removal instructions from JSON.")
                return {}

    def parse_dirty_json(self, json_str: str) -> Dict[str, Any]:
        """
        Attempts to parse dirty JSON strings by correcting common issues.
        """
        # Replace single quotes with double quotes
        json_str = json_str.replace("'", '"')

        # Remove trailing commas
        json_str = re.sub(r",\s*([}\]])", r"\1", json_str)

        # Remove comments (// or /* */)
        json_str = re.sub(r"//.*?\n|/\*.*?\*/", "", json_str, flags=re.DOTALL)

        # Remove extra whitespace
        json_str = json_str.strip()

        # Attempt to extract JSON object
        json_str = self.extract_json_object_string(json_str)

        if not json_str:
            self.logger.error("No valid JSON object found.")
            return None

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            self.logger.error(f"Dirty JSON parsing failed: {e}")
            return None

    def extract_json_object_string(self, text: str) -> str:
        """
        Extracts the first JSON object found in a string.
        """
        # Regex pattern to match JSON objects
        pattern = re.compile(r'\{.*?\}', re.DOTALL)
        matches = pattern.findall(text)
        if matches:
            return matches[0]
        else:
            return None

    def extract_module_path(self, code: str) -> str:
        """
        Extracts the full file path from the initial comment.
        """
        pattern = r"^#\s*(.*\.py)$"
        match = re.search(pattern, code, flags=re.MULTILINE)
        if match:
            module_path = match.group(1).strip()
            self.logger.debug(f"Extracted module path: {module_path}")
            return module_path
        self.logger.error("Module path not found in the code block.")
        return None

    def remove_initial_comment(self, code: str) -> str:
        """
        Removes the initial comment (module path) from the code.
        """
        code = re.sub(
            r"^#\s*.*\.py$", "", code, count=1, flags=re.MULTILINE
        ).lstrip()
        self.logger.debug("Removed initial module path comment from code.")
        return code

    def extract_and_remove_special_imports(
        self, code: str
    ) -> Tuple[List[str], str]:
        """
        Extracts and removes imports or variables marked with a special marker.
        """
        imports = []
        lines = code.split("\n")
        cleaned_lines = []
        for line in lines:
            if line.strip().startswith("#¤#"):
                imports.append(line.strip()[3:].strip())
            else:
                cleaned_lines.append(line)
        code = "\n".join(cleaned_lines)
        self.logger.debug(f"Extracted special imports/variables: {imports}")
        return imports, code

    def extract_class_and_method_names(
        self, code: str
    ) -> Tuple[str, str]:
        """
        Extracts class and method names from the code.
        """
        class_name = None
        method_name = None
        class_match = re.search(r"class\s+(\w+)\s*(\(.*\))?:", code)
        if class_match:
            class_name = class_match.group(1)
            method_pattern = r"def\s+(\w+)\s*\(.*\):"
            method_matches = re.finditer(method_pattern, code)
            for method_match in method_matches:
                method_name = method_match.group(1)
                # Assuming only one method per code block
                break
        else:
            # Check for standalone function
            function_match = re.search(r"def\s+(\w+)\s*\(.*\):", code)
            if function_match:
                method_name = function_match.group(1)
        self.logger.debug(
            f"Extracted class name: {class_name}, method name: {method_name}"
        )
        return class_name, method_name

    def extract_updated_methods(self, code: str) -> Dict[str, str]:
        """
        Extracts methods between # BEGIN UPDATED METHOD and # END UPDATED METHOD markers.
        """
        pattern = r"# BEGIN UPDATED METHOD\n(.*?)\n# END UPDATED METHOD"
        matches = re.finditer(pattern, code, re.DOTALL)
        updated_methods = {}
        for match in matches:
            method_code = match.group(1).strip()
            method_name_match = re.search(
                r"def\s+(\w+)\s*\(.*\):", method_code
            )
            if method_name_match:
                method_name = method_name_match.group(1)
                updated_methods[method_name] = method_code
        # Remove the updated methods from the code block to prevent duplication
        code = re.sub(pattern, "", code, flags=re.DOTALL)
        self.logger.debug(
            f"Extracted updated methods: {list(updated_methods.keys())}"
        )
        return updated_methods

    def handle_unchanged_parts(self, code: str) -> str:
        """
        Removes '## ...' markers to preserve code structure.
        """
        code = code.replace("## ...", "")
        self.logger.debug("Handled unchanged parts marked with ## ...")
        return code

# Code Parser
class CodeParser:
    def __init__(self):
        self.logger = LoggerManager().get_logger()

    def parse_code(self, code):
        """
        Parses code into an AST.
        """
        try:
            tree = ast.parse(code)
            self.logger.debug("Parsed code into AST.")
            return tree
        except SyntaxError as e:
            self.logger.error(f"Syntax error while parsing code: {e}")
            raise

    def ast_to_code(self, tree):
        """
        Converts an AST back to code.
        """
        try:
            code = astor.to_source(tree)
            self.logger.debug("Converted AST back to code.")
            return code
        except Exception as e:
            self.logger.error(f"Error converting AST to code: {e}")
            raise

    def find_class(self, tree, class_name):
        """
        Recursively searches for a class node with the given name.
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return node
        return None

    def find_function(self, tree, function_name):
        """
        Searches for a function node with the given name.
        """
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                return node
        return None

    def find_assignments(self, tree, variable_names):
        """
        Finds assignments to the given variable names.
        """
        assignments = []
        for node in tree.body:
            if isinstance(node, ast.Assign):
                targets = [
                    t.id for t in node.targets if isinstance(t, ast.Name)
                ]
                if any(var_name in targets for var_name in variable_names):
                    assignments.append(node)
        return assignments

# Code Remover
class CodeRemover:
    """
    Handles the removal of code elements (classes, functions, variables)
    from the AST based on JSON instructions.
    """

    def __init__(self):
        self.logger = LoggerManager().get_logger()
        self.parser = CodeParser()

    def remove_code(self, tree, removal_instructions: Dict):
        """
        Removes code elements specified in the removal_instructions from the AST.
        """
        targets = removal_instructions.get("targets", [])
        for target in targets:
            target_type = target.get("type")
            name = target.get("name")

            if target_type == "class":
                self.remove_class(tree, name)
            elif target_type == "function":
                self.remove_function(tree, name)
            elif target_type == "variable":
                self.remove_assignments(tree, [name])
            else:
                self.logger.warning(f"Unknown target type: {target_type}")

        return tree

    def remove_class(self, tree, class_name):
        """
        Removes a class definition from the AST.
        """
        original_len = len(tree.body)
        tree.body = [
            node
            for node in tree.body
            if not (isinstance(node, ast.ClassDef) and node.name == class_name)
        ]
        if len(tree.body) < original_len:
            self.logger.debug(f"Removed class: {class_name}")
        else:
            self.logger.warning(f"Class {class_name} not found for removal.")

    def remove_function(self, tree, function_name):
        """
        Removes a function definition from the AST.
        """
        original_len = len(tree.body)
        tree.body = [
            node
            for node in tree.body
            if not (
                isinstance(node, ast.FunctionDef) and node.name == function_name
            )
        ]
        if len(tree.body) < original_len:
            self.logger.debug(f"Removed function: {function_name}")
        else:
            self.logger.warning(
                f"Function {function_name} not found for removal."
            )

    def remove_assignments(self, tree, variable_names):
        """
        Removes variable assignments from the AST.
        """
        original_len = len(tree.body)
        tree.body = [
            node
            for node in tree.body
            if not (
                isinstance(node, ast.Assign)
                and any(
                    isinstance(t, ast.Name) and t.id in variable_names
                    for t in node.targets
                )
            )
        ]
        if len(tree.body) < original_len:
            self.logger.debug(
                f"Removed assignments for variables: {', '.join(variable_names)}"
            )
        else:
            self.logger.warning(
                f"Assignments for variables {', '.join(variable_names)} not found for removal."
            )

# Code Integrator
class CodeIntegrator:
    def __init__(self):
        self.logger = LoggerManager().get_logger()
        self.preserve_formatting = CONFIG.get("preserve_formatting", True)
        self.parser = CodeParser()  # Ensure access to parser methods
        self.code_remover = CodeRemover()

    def integrate_nodes(self, original_tree, new_nodes):
        """
        Integrates new_nodes into original_tree, replacing existing definitions and adding new ones.
        """
        original_nodes = {self.get_node_key(n): n for n in original_tree.body}

        for new_node in new_nodes:
            key = self.get_node_key(new_node)
            if key in original_nodes:
                index = original_tree.body.index(original_nodes[key])
                original_tree.body[index] = new_node
                self.logger.debug(f"Replaced {type(new_node).__name__}: {key}")
            else:
                original_tree.body.append(new_node)
                self.logger.debug(f"Added new {type(new_node).__name__}: {key}")

    def get_node_key(self, node):
        """
        Generates a unique key for a node based on its type and name or targets.
        """
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return node.name
        elif isinstance(node, ast.Assign):
            # For assignments, use the variable names
            targets = []
            for target in node.targets:
                if isinstance(target, ast.Name):
                    targets.append(target.id)
                elif isinstance(target, (ast.Tuple, ast.List)):
                    targets.extend(
                        [elt.id for elt in target.elts if isinstance(elt, ast.Name)]
                    )
            return ",".join(targets)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            return ast.dump(node)
        else:
            # For other node types, use their type and position
            return f"{type(node).__name__}_{id(node)}"

    def integrate_updated_methods(self, class_node, updated_methods):
        """
        Integrates updated methods into the class node.
        """
        existing_methods = {
            node.name: node
            for node in class_node.body
            if isinstance(node, ast.FunctionDef)
        }
        for method_name, method_code in updated_methods.items():
            method_tree = self.parser.parse_code(method_code)
            method_node = method_tree.body[0]  # Assuming the method is the first node
            if method_name in existing_methods:
                index = class_node.body.index(existing_methods[method_name])
                class_node.body[index] = method_node
                self.logger.debug(
                    f"Updated method {method_name} in class {class_node.name}"
                )
            else:
                class_node.body.append(method_node)
                self.logger.debug(
                    f"Added new method {method_name} to class {class_node.name}"
                )

# Code Validator
class CodeValidator:
    def __init__(self):
        self.logger = LoggerManager().get_logger()

    def validate_syntax(self, code, filename):
        """
        Validates the syntax of the given code.
        """
        try:
            compile(code, filename, "exec")
            self.logger.debug(f"Code in {filename} passed syntax validation.")
            return True
        except SyntaxError as e:
            self.logger.error(f"Syntax error in code {filename}: {e}")
            return False

# Code Formatter
class CodeFormatter:
    def __init__(self):
        self.logger = LoggerManager().get_logger()

    def format_code(self, code):
        """
        Formats code using Black.
        """
        try:
            formatted_code = black.format_str(code, mode=black.FileMode())
            self.logger.debug("Formatted code using Black.")
            return formatted_code
        except Exception as e:
            self.logger.error(f"Error formatting code: {e}")
            return code  # Return original code if formatting fails

# Controller
class Controller:
    def __init__(self):
        self.logger = LoggerManager().get_logger()
        self.extractor = CodeBlockExtractor(CONFIG.get("input_file", ""))
        self.parser = CodeParser()
        self.integrator = CodeIntegrator()
        self.file_manager = FileManager()
        self.validator = CodeValidator()
        self.formatter = CodeFormatter()
        self.code_remover = CodeRemover()

    def run_step_by_step(self):
        # Step 1: Extracting code blocks
        self.logger.info("Step 1: Extracting code blocks...")
        input_text = self.extractor.read_input_file()
        code_blocks = self.extractor.extract_code_blocks(input_text)
        self.logger.info(f"Extracted {len(code_blocks)} code block(s).")

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

    def process_removal_block(self, block, return_diff=False):
        """
        Process a code removal block.

        Args:
            block (dict): The code block to process.
            return_diff (bool): Whether to return the diff after processing.

        Returns:
            tuple: (success, message, diff_text) if return_diff is True, else (success, message, None)
        """
        removal_instructions = block.get("removal_instructions", {})
        module_path = removal_instructions.get("module_path")

        if not module_path:
            self.logger.error("Module path is missing in the removal instructions.")
            return False, "Module path is missing in the removal instructions.", None

        if not self.file_manager.validate_path(module_path):
            self.logger.error(f"Module {module_path} does not exist.")
            return False, f"Module {module_path} does not exist.", None

        original_code = self.file_manager.read_file(module_path)
        self.logger.info(f"Module ready for removal: {module_path}")

        # Parse existing code into AST
        try:
            existing_tree = self.parser.parse_code(original_code)
        except SyntaxError as e:
            self.logger.error(f"Syntax error in existing code: {e}")
            return False, f"Syntax error in existing code: {e}", None

        # Remove code as per instructions
        self.logger.info("Removing specified code elements...")
        existing_tree = self.code_remover.remove_code(
            existing_tree, removal_instructions
        )

        # Convert AST back to code
        updated_code = self.parser.ast_to_code(existing_tree)

        # Validate updated code syntax
        self.logger.info("Validating updated code syntax...")
        if not self.validator.validate_syntax(updated_code, module_path):
            return False, "Updated code has syntax errors.", None

        # Format code if required
        if not CONFIG.get("preserve_formatting", True):
            self.logger.info("Formatting the code using Black...")
            updated_code = self.formatter.format_code(updated_code)
        else:
            self.logger.info("Preserving original code formatting.")

        # Re-add initial comments if necessary
        initial_comments, code_body = self.extract_initial_comments(original_code)
        updated_code = self.re_add_initial_comments(initial_comments, updated_code)

        # Write updated code
        self.logger.info("Writing updated code to file...")
        self.file_manager.write_file(module_path, updated_code)
        self.logger.info(f"Module {module_path} has been updated after removal.")

        # If diff is requested, compute and return it
        if return_diff:
            import difflib

            original_lines = original_code.splitlines(keepends=True)
            updated_lines = updated_code.splitlines(keepends=True)
            diff = ''.join(difflib.unified_diff(
                original_lines,
                updated_lines,
                fromfile='original',
                tofile='updated',
                lineterm=''
            ))
            self.logger.debug("Generated diff for the removal block.")
            return True, f"Removed specified elements from {module_path}.", diff

        return True, f"Removed specified elements from {module_path}.", None

    def process_code_block(self, block, return_diff=False):
        """
        Processes a single code block for updates or additions.

        Args:
            block (dict): The code block to process.
            return_diff (bool): Whether to return the diff after processing.

        Returns:
            tuple: (success, message, diff_text) if return_diff is True, else (success, message, None)
        """
        module_path = block.get("module_path")
        new_code_block = block.get("code_block")
        updated_methods = block.get("updated_methods", {})
        imports = block.get("imports", [])

        self.logger.debug(f"Processing module: {module_path}")

        # Validate module path
        if not module_path:
            self.logger.error("Module path is missing in the code block.")
            return False, "Module path is missing in the code block.", None

        # Step 2: Read or Create Module Code
        if not self.file_manager.validate_path(module_path):
            if CONFIG.get("create_missing_modules", True):
                self.logger.warning(
                    f"Module {module_path} does not exist. Creating new module."
                )
                try:
                    self.file_manager.create_module(module_path)
                except Exception as e:
                    self.logger.error(f"Error creating module {module_path}: {e}")
                    return False, f"Error creating module {module_path}: {e}", None
            else:
                self.logger.error(f"Module {module_path} does not exist.")
                return False, f"Module {module_path} does not exist.", None

        original_code = self.file_manager.read_file(module_path)

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
        new_code_nodes = new_tree.body  # Assuming new_tree has the new nodes
        self.integrator.collect_and_merge_imports(existing_tree, new_tree)

        # Integrate new classes/functions
        self.logger.info("Integrating new classes/functions...")
        self.integrator.integrate_nodes(existing_tree, new_code_nodes)

        # Integrate updated methods if any
        if block.get("class_name") and updated_methods:
            class_node = self.parser.find_class(existing_tree, block["class_name"])
            if class_node:
                self.logger.info(f"Integrating updated methods into class {block['class_name']}...")
                self.integrator.integrate_updated_methods(class_node, updated_methods)
            else:
                self.logger.error(
                    f"Class {block['class_name']} not found in existing code."
                )
                return False, f"Class {block['class_name']} not found in existing code.", None

        # Convert AST back to code
        updated_code_body = self.parser.ast_to_code(existing_tree)

        # Re-add initial comments if necessary
        initial_comments, code_body = self.extract_initial_comments(original_code)
        updated_code = self.re_add_initial_comments(initial_comments, updated_code_body)

        # Validate updated code syntax
        self.logger.info("Validating updated code syntax...")
        if not self.validator.validate_syntax(updated_code, module_path):
            return False, "Updated code has syntax errors.", None

        # Format code if required
        if not CONFIG.get("preserve_formatting", True):
            self.logger.info("Formatting the code using Black...")
            updated_code = self.formatter.format_code(updated_code)
        else:
            self.logger.info("Preserving original code formatting.")

        # Write updated code
        self.logger.info("Writing updated code to file...")
        self.file_manager.write_file(module_path, updated_code)
        self.logger.info(f"Module {module_path} has been updated.")

        # If diff is requested, compute and return it
        if return_diff:
            import difflib

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
            return True, f"Updated module {module_path}.", diff

        return True, f"Updated module {module_path}.", None

    def extract_initial_comments(self, code: str):
        """
        Extracts initial comments from the code.
        """
        lines = code.splitlines()
        initial_comments = []
        code_body = []
        comment_pattern = re.compile(r"^#.*")

        # Skip leading blank lines
        started = False
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line == "" and not started:
                continue  # Skip leading blank lines
            if comment_pattern.match(stripped_line):
                initial_comments.append(line)
                started = True
            else:
                code_body = lines[i:]
                break

        remaining_code = "\n".join(code_body)
        self.logger.debug(f"Extracted initial comments: {initial_comments}")
        return initial_comments, remaining_code

    def re_add_initial_comments(self, comments: List[str], code: str) -> str:
        """
        Re-adds the initial comments to the code.
        """
        if comments:
            comments_str = "\n".join(comments) + "\n"
            updated_code = comments_str + code
            self.logger.debug("Re-added initial comments to the updated code.")
            return updated_code
        return code

# Code Validator
class CodeValidator:
    def __init__(self):
        self.logger = LoggerManager().get_logger()

    def validate_syntax(self, code, filename):
        """
        Validates the syntax of the given code.
        """
        try:
            compile(code, filename, "exec")
            self.logger.debug(f"Code in {filename} passed syntax validation.")
            return True
        except SyntaxError as e:
            self.logger.error(f"Syntax error in code {filename}: {e}")
            return False

# Code Formatter
class CodeFormatter:
    def __init__(self):
        self.logger = LoggerManager().get_logger()

    def format_code(self, code):
        """
        Formats code using Black.
        """
        try:
            formatted_code = black.format_str(code, mode=black.FileMode())
            self.logger.debug("Formatted code using Black.")
            return formatted_code
        except Exception as e:
            self.logger.error(f"Error formatting code: {e}")
            return code  # Return original code if formatting fails

# Controller
class Controller:
    def __init__(self):
        self.logger = LoggerManager().get_logger()
        self.extractor = CodeBlockExtractor(CONFIG.get("input_file", ""))
        self.parser = CodeParser()
        self.integrator = CodeIntegrator()
        self.file_manager = FileManager()
        self.validator = CodeValidator()
        self.formatter = CodeFormatter()
        self.code_remover = CodeRemover()

    def run_step_by_step(self):
        # Step 1: Extracting code blocks
        self.logger.info("Step 1: Extracting code blocks...")
        input_text = self.extractor.read_input_file()
        code_blocks = self.extractor.extract_code_blocks(input_text)
        self.logger.info(f"Extracted {len(code_blocks)} code block(s).")

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

    def process_removal_block(self, block, return_diff=False):
        """
        Process a code removal block.

        Args:
            block (dict): The code block to process.
            return_diff (bool): Whether to return the diff after processing.

        Returns:
            tuple: (success, message, diff_text) if return_diff is True, else (success, message, None)
        """
        removal_instructions = block.get("removal_instructions", {})
        module_path = removal_instructions.get("module_path")

        if not module_path:
            self.logger.error("Module path is missing in the removal instructions.")
            return False, "Module path is missing in the removal instructions.", None

        if not self.file_manager.validate_path(module_path):
            self.logger.error(f"Module {module_path} does not exist.")
            return False, f"Module {module_path} does not exist.", None

        original_code = self.file_manager.read_file(module_path)
        self.logger.info(f"Module ready for removal: {module_path}")

        # Parse existing code into AST
        try:
            existing_tree = self.parser.parse_code(original_code)
        except SyntaxError as e:
            self.logger.error(f"Syntax error in existing code: {e}")
            return False, f"Syntax error in existing code: {e}", None

        # Remove code as per instructions
        self.logger.info("Removing specified code elements...")
        existing_tree = self.code_remover.remove_code(
            existing_tree, removal_instructions
        )

        # Convert AST back to code
        updated_code = self.parser.ast_to_code(existing_tree)

        # Validate updated code syntax
        self.logger.info("Validating updated code syntax...")
        if not self.validator.validate_syntax(updated_code, module_path):
            return False, "Updated code has syntax errors.", None

        # Format code if required
        if not CONFIG.get("preserve_formatting", True):
            self.logger.info("Formatting the code using Black...")
            updated_code = self.formatter.format_code(updated_code)
        else:
            self.logger.info("Preserving original code formatting.")

        # Re-add initial comments if necessary
        initial_comments, code_body = self.extract_initial_comments(original_code)
        updated_code = self.re_add_initial_comments(initial_comments, updated_code)

        # Write updated code
        self.logger.info("Writing updated code to file...")
        self.file_manager.write_file(module_path, updated_code)
        self.logger.info(f"Module {module_path} has been updated after removal.")

        # If diff is requested, compute and return it
        if return_diff:
            import difflib

            original_lines = original_code.splitlines(keepends=True)
            updated_lines = updated_code.splitlines(keepends=True)
            diff = ''.join(difflib.unified_diff(
                original_lines,
                updated_lines,
                fromfile='original',
                tofile='updated',
                lineterm=''
            ))
            self.logger.debug("Generated diff for the removal block.")
            return True, f"Removed specified elements from {module_path}.", diff

        return True, f"Removed specified elements from {module_path}.", None

    def process_code_block(self, block, return_diff=False):
        """
        Processes a single code block for updates or additions.

        Args:
            block (dict): The code block to process.
            return_diff (bool): Whether to return the diff after processing.

        Returns:
            tuple: (success, message, diff_text) if return_diff is True, else (success, message, None)
        """
        module_path = block.get("module_path")
        new_code_block = block.get("code_block")
        updated_methods = block.get("updated_methods", {})
        imports = block.get("imports", [])

        self.logger.debug(f"Processing module: {module_path}")

        # Validate module path
        if not module_path:
            self.logger.error("Module path is missing in the code block.")
            return False, "Module path is missing in the code block.", None

        # Step 2: Read or Create Module Code
        if not self.file_manager.validate_path(module_path):
            if CONFIG.get("create_missing_modules", True):
                self.logger.warning(
                    f"Module {module_path} does not exist. Creating new module."
                )
                try:
                    self.file_manager.create_module(module_path)
                except Exception as e:
                    self.logger.error(f"Error creating module {module_path}: {e}")
                    return False, f"Error creating module {module_path}: {e}", None
            else:
                self.logger.error(f"Module {module_path} does not exist.")
                return False, f"Module {module_path} does not exist.", None

        original_code = self.file_manager.read_file(module_path)

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
        new_code_nodes = new_tree.body  # Assuming new_tree has the new nodes
        self.integrator.collect_and_merge_imports(existing_tree, new_tree)

        # Integrate new classes/functions
        self.logger.info("Integrating new classes/functions...")
        self.integrator.integrate_nodes(existing_tree, new_code_nodes)

        # Integrate updated methods if any
        if block.get("class_name") and updated_methods:
            class_node = self.parser.find_class(existing_tree, block["class_name"])
            if class_node:
                self.logger.info(f"Integrating updated methods into class {block['class_name']}...")
                self.integrator.integrate_updated_methods(class_node, updated_methods)
            else:
                self.logger.error(
                    f"Class {block['class_name']} not found in existing code."
                )
                return False, f"Class {block['class_name']} not found in existing code.", None

        # Convert AST back to code
        updated_code_body = self.parser.ast_to_code(existing_tree)

        # Re-add initial comments if necessary
        initial_comments, code_body = self.extract_initial_comments(original_code)
        updated_code = self.re_add_initial_comments(initial_comments, updated_code_body)

        # Validate updated code syntax
        self.logger.info("Validating updated code syntax...")
        if not self.validator.validate_syntax(updated_code, module_path):
            return False, "Updated code has syntax errors.", None

        # Format code if required
        if not CONFIG.get("preserve_formatting", True):
            self.logger.info("Formatting the code using Black...")
            updated_code = self.formatter.format_code(updated_code)
        else:
            self.logger.info("Preserving original code formatting.")

        # Write updated code
        self.logger.info("Writing updated code to file...")
        self.file_manager.write_file(module_path, updated_code)
        self.logger.info(f"Module {module_path} has been updated.")

        # If diff is requested, compute and return it
        if return_diff:
            import difflib

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
            return True, f"Updated module {module_path}.", diff

        return True, f"Updated module {module_path}.", None

    def extract_initial_comments(self, code: str):
        """
        Extracts initial comments from the code.
        """
        lines = code.splitlines()
        initial_comments = []
        code_body = []
        comment_pattern = re.compile(r"^#.*")

        # Skip leading blank lines
        started = False
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line == "" and not started:
                continue  # Skip leading blank lines
            if comment_pattern.match(stripped_line):
                initial_comments.append(line)
                started = True
            else:
                code_body = lines[i:]
                break

        remaining_code = "\n".join(code_body)
        self.logger.debug(f"Extracted initial comments: {initial_comments}")
        return initial_comments, remaining_code

    def re_add_initial_comments(self, comments: List[str], code: str) -> str:
        """
        Re-adds the initial comments to the code.
        """
        if comments:
            comments_str = "\n".join(comments) + "\n"
            updated_code = comments_str + code
            self.logger.debug("Re-added initial comments to the updated code.")
            return updated_code
        return code

# Main Execution
if __name__ == "__main__":
    controller = Controller()
    controller.run_step_by_step()

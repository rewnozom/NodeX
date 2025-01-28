# ./src/live/_full_backend_.py


import logging
import os
import sys
import re
import os
import ast
import astor
import difflib
import json
import black
import logging
from typing import List, Tuple, Dict, Optional, Any, Callable
from collections import defaultdict
from PySide6.QtWidgets import QListWidgetItem, QMessageBox
from PySide6.QtCore import Qt, QTimer
from markdown_it import MarkdownIt
from Config.AppConfig.config import *
from Config.AppConfig import config

import os
import sys

def add_project_subdirectories_to_syspath(root_dir):
    """
    Recursively add all subdirectories of the project root to sys.path.
    """
    for dirpath, dirnames, _ in os.walk(root_dir):
        if dirpath not in sys.path:
            sys.path.insert(0, dirpath)

# Automatically detect the project root (adjust the path levels if needed)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
add_project_subdirectories_to_syspath(project_root)


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class ExtractAndRemoveSpecialImports:

    def __init__(self):
        self.logger = logger

    def extract_and_remove_special_imports(self, code: str) -> Tuple[List[str], str]:
        imports = []
        lines = code.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip().startswith('#¤#'):
                imports.append(line.strip()[3:].strip())
            else:
                cleaned_lines.append(line)
        code = '\n'.join(cleaned_lines)
        self.logger.debug(f'Extracted special imports: {imports}')
        return imports, code

class ClassAndMethodNameExtractor:

    def extract_class_and_method_names(self, code: str) -> Tuple[Optional[str], Optional[str]]:
        class_name = None
        method_name = None
        class_match = re.search(r'class\s+(\w+)\s*(\(.*\))?:', code)
        if class_match:
            class_name = class_match.group(1)
            method_pattern = r'def\s+(\w+)\s*\(.*\):'
            method_matches = re.finditer(method_pattern, code)
            for method_match in method_matches:
                method_name = method_match.group(1)
                break
        else:
            function_match = re.search(r'def\s+(\w+)\s*\(.*\):', code)
            if function_match:
                method_name = function_match.group(1)
        return class_name, method_name

class ClassNameExtractor:

    def simple_capitalization(self, file_path: str) -> str:
        base_name = os.path.basename(file_path)
        class_name = os.path.splitext(base_name)[0].capitalize()
        return class_name

    def camel_case_conversion(self, file_path: str) -> str:
        base_name = os.path.basename(file_path)
        class_name = ''.join(word.capitalize() for word in os.path.splitext(base_name)[0].split('_'))
        return class_name

class CodeBlockExtractor:
    """
    Extracts code blocks from LLM outputs and prepares them for integration.
    """
    def __init__(self, config_manager):
        self.logger = logging.getLogger(__name__)
        self.md_parser = MarkdownIt()
        self.config_manager = config_manager
        self.module_path_extractor = ModulePathExtractor(config_manager)
        self.special_imports_extractor = ExtractAndRemoveSpecialImports()

    def extract_code_blocks(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts code blocks using regular expressions first, and falls back to markdown-it if no blocks are found.
        Handles JSON blocks for removal instructions and code blocks for updates.
        """
        code_blocks = []

        # Try to detect code blocks with language identifiers using regex
        code_block_pattern = r"```(?P<language>\w+)\n(?P<code>.*?)```"
        matches = re.finditer(code_block_pattern, text, re.DOTALL)

        for match in matches:
            language = match.group("language")
            code = match.group("code").strip()

            if language.lower() == "json":
                # Parse JSON removal instructions
                removal_instructions = JSONRemovalParser().parse_removal_json(code)
                if removal_instructions:
                    code_blocks.append({
                        "action": "remove",
                        "removal_instructions": removal_instructions
                    })
                continue  # Skip further processing for JSON blocks

            # Extract initial comment for module path
            module_path = self.module_path_extractor.extract_module_path(code)

            # Remove initial comment from code
            if module_path:
                code = InitialCommentRemover().remove_initial_comment(code)

            # Remove code marked for removal
            code = self.remove_marked_code(code)

            # Handle imports
            imports, code = self.special_imports_extractor.extract_and_remove_special_imports(code)

            # Handle class and method extraction
            class_name, method_name = ClassAndMethodNameExtractor().extract_class_and_method_names(code)

            # Handle updated methods
            updated_methods = CodeExtractor().extract_updated_methods(code)

            # Handle unchanged parts marked with ## ...
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

        # If no code blocks were found via regex, fall back to markdown-it
        if not code_blocks:
            self.logger.debug("No code blocks found using regex, falling back to markdown-it.")
            tokens = self.md_parser.parse(text)

            for token in tokens:
                if token.type == 'fence':  # 'fence' token represents a code block in Markdown
                    language = token.info.strip()
                    code = token.content.strip()

                    if language.lower() == "json":
                        # Parse JSON removal instructions
                        removal_instructions = JSONRemovalParser().parse_removal_json(code)
                        if removal_instructions:
                            code_blocks.append({
                                "action": "remove",
                                "removal_instructions": removal_instructions
                            })
                        continue  # Skip further processing for JSON blocks

                    # Extract initial comment for module path
                    module_path = ModulePathExtractor().extract_module_path(code)

                    # Remove initial comment from code
                    if module_path:
                        code = InitialCommentRemover().remove_initial_comment(code)

                    # Remove code marked for removal
                    code = self.remove_marked_code(code)

                    # Handle imports
                    imports, code = ExtractAndRemoveSpecialImports().extract_and_remove_special_imports(code)

                    # Handle class and method extraction
                    class_name, method_name = ClassAndMethodNameExtractor().extract_class_and_method_names(code)

                    # Handle updated methods
                    updated_methods = CodeExtractor().extract_updated_methods(code)

                    # Handle unchanged parts marked with ## ...
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

    def remove_marked_code(self, code: str) -> str:
        """
        Removes code marked for removal, either via JSON blocks or between #""" and """ markers.
        """
        marked_code_pattern = r'#""".*?"""'
        code = re.sub(marked_code_pattern, '', code, flags=re.DOTALL)
        self.logger.debug('Removed code marked for removal between #""" markers.')
        return code

    def handle_unchanged_parts(self, code: str) -> str:
        """
        Removes '## ...' markers to preserve code structure.
        """
        code = code.replace("## ...", "")
        self.logger.debug("Handled unchanged parts marked with ## ...")
        return code

class CommentExtractor:

    def __init__(self):
        self.logger = logger

    def extract_initial_comments(self, code: str) -> Tuple[List[str], str]:
        lines = code.splitlines()
        initial_comments = []
        code_body = []
        comment_pattern = re.compile('^#.*')
        started = False
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line == '' and not started:
                continue
            if comment_pattern.match(stripped_line):
                initial_comments.append(line)
                started = True
            else:
                code_body = lines[i:]
                break
        remaining_code = '\n'.join(code_body)
        self.logger.debug(f'Extracted initial comments: {initial_comments}')
        return initial_comments, remaining_code

class ModulePathExtractor:
    def __init__(self, config_manager):
        self.logger = logger
        self.config_manager = config_manager  # Store the config manager

    def extract_module_path(self, code: str) -> Optional[str]:
        patterns = [
            r'^#+\s*(.*\.py)$',  # Title pattern
            r'^#\s*(.*\.py)$',   # In-code pattern
            r'^["\'](.*\.py)["\']$',  # Quoted path
            r'^.*?[/\\](.*\.py)$'  # Path with directories
        ]

        for pattern in patterns:
            match = re.search(pattern, code, re.MULTILINE)
            if match:
                module_path = match.group(1).strip()
                self.logger.debug(f'Extracted module path: {module_path}')
                return self.process_module_path(module_path)

        self.logger.warning('No module path found')
        return None

    def process_module_path(self, path: str) -> str:
        # Remove any leading ./ or .\
        path = re.sub(r'^\.[\\/]', '', path)
        
        # If use_workspace_root is enabled, prepend the workspace root
        if self.config_manager.get_config_value("use_workspace_root", True):
            workspace_root = self.config_manager.get_config_value("workspace_root", "workspace")
            path = os.path.join(workspace_root, path)

        return os.path.normpath(path)

class CodeExtractor:

    def __init__(self, logger=None):
        self.logger = logger or logger

    def extract_updated_methods(self, code: str) -> Dict[str, str]:
        pattern = '# BEGIN UPDATED METHOD\\n(.*?)\\n# END UPDATED METHOD'
        matches = re.finditer(pattern, code, re.DOTALL)
        updated_methods = {}
        for match in matches:
            method_code = match.group(1).strip()
            method_name_match = re.search('def\\s+(\\w+)\\s*\\(.*\\):', method_code)
            if method_name_match:
                method_name = method_name_match.group(1)
                updated_methods[method_name] = method_code
        if self.logger:
            self.logger.debug(f'Extracted updated methods: {list(updated_methods.keys())}')
        return updated_methods

class FunctionFinder:

    def find_function(self, tree: ast.AST, function_name: str) -> Optional[ast.FunctionDef]:
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                return node
        return None

class MethodFinder:

    def find_method_recursive(self, class_node: ast.ClassDef, method_name: str) -> Optional[ast.FunctionDef]:
        for node in ast.walk(class_node):
            if isinstance(node, ast.FunctionDef) and node.name == method_name:
                return node
        return None

    def find_method_simple(self, class_node: ast.ClassDef, method_name: str) -> Optional[ast.FunctionDef]:
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef) and node.name == method_name:
                return node
        return None

class FindClass:

    def find_class_recursive(self, tree: ast.AST, class_name: str) -> Optional[ast.ClassDef]:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return node
        return None

    def find_class_simple(self, tree: ast.AST, class_name: str) -> Optional[ast.ClassDef]:
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return node
        return None

class RemoveClass:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def remove_class(self, tree: ast.AST, class_name: str):
        original_len = len(tree.body)
        tree.body = [node for node in tree.body if not (isinstance(node, ast.ClassDef) and node.name == class_name)]
        if len(tree.body) < original_len:
            self.logger.debug(f'Removed class: {class_name}')
        else:
            self.logger.warning(f'Class {class_name} not found for removal.')

class RemoveFunction:

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def remove_function(self, tree: ast.AST, function_name: str):
        original_len = len(tree.body)
        tree.body = [node for node in tree.body if not (isinstance(node, ast.FunctionDef) and node.name == function_name)]
        if len(tree.body) < original_len:
            self.logger.debug(f'Removed function: {function_name}')
        else:
            self.logger.warning(f'Function {function_name} not found for removal.')

class CodeFormatter:

    def __init__(self, enable_formatting=True, logger=None):
        self.enable_formatting = enable_formatting
        self.logger = logger or logging.getLogger(__name__)

    def format_code(self, code: str) -> str:
        if not self.enable_formatting:
            self.logger.debug('Code formatting is disabled.')
            return code
        try:
            formatted_code = black.format_str(code, mode=black.FileMode())
            self.logger.debug('Formatted code using Black.')
            return formatted_code
        except Exception as e:
            self.logger.error(f'Error formatting code: {e}')
            return code

class DiffGenerator:

    def generate_diff(self, original_node: ast.AST, new_node: ast.AST) -> str:
        original_code = astor.to_source(original_node)
        new_code = astor.to_source(new_node)
        diff = ''.join(
            difflib.unified_diff(
                original_code.splitlines(keepends=True),
                new_code.splitlines(keepends=True),
                fromfile='original',
                tofile='updated',
            )
        )
        return diff

class CodeParser:

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def parse_code(self, code: str) -> ast.AST:
        """
        Parses code into an AST.
        """
        try:
            tree = ast.parse(code)
            self.logger.debug('Parsed code into AST.')
            return tree
        except SyntaxError as e:
            self.logger.error(f'Syntax error while parsing code: {e}')
            raise

    def ast_to_code(self, tree: ast.AST) -> str:
        """
        Converts an AST back to code.
        """
        try:
            code = ast.unparse(tree) if hasattr(ast, 'unparse') else self._fallback_ast_to_code(tree)
            self.logger.debug("Converted AST back to code.")
            return code
        except Exception as e:
            self.logger.error(f"Error converting AST to code: {e}")
            raise

    def _fallback_ast_to_code(self, tree: ast.AST) -> str:
        """
        Fallback method for converting AST to code if ast.unparse is not available.
        Uses astor as a fallback.
        """
        try:
            code = astor.to_source(tree)
            self.logger.debug("Converted AST back to code using astor.")
            return code
        except Exception as e:
            self.logger.error(f"Error converting AST to code using astor: {e}")
            raise

    def find_class(self, tree: ast.AST, class_name: str) -> Optional[ast.ClassDef]:
        """
        Recursively searches for a class node with the given name.
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return node
        return None

    def find_function(self, tree: ast.AST, function_name: str) -> Optional[ast.FunctionDef]:
        """
        Searches for a function node with the given name.
        """
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                return node
        return None


class SyntaxValidator:

    def __init__(self, logger=None, enable_validation=True):
        self.logger = logger or logging.getLogger(__name__)
        self.enable_validation = enable_validation

    def validate_syntax_strict(self, code: str, filename: str) -> bool:
        try:
            compile(code, filename, 'exec')
            self.logger.debug(f'Code in {filename} passed syntax validation.')
            return True
        except SyntaxError as e:
            self.logger.error(f'Syntax error in code {filename}: {e}')
            return False

    def validate_syntax_optional(self, code: str, filename: str) -> bool:
        if not self.enable_validation:
            self.logger.debug('Code validation is disabled.')
            return True
        return self.validate_syntax_strict(code, filename)

class JSONRemovalParser:

    def __init__(self):
        self.logger = logger

    def parse_removal_json(self, json_code: str) -> Dict[str, Any]:
        """
        Parses the JSON code block to extract removal instructions, handling dirty JSON.
        """
        try:
            removal_data = json.loads(json_code)
            self.logger.debug(f"Parsed removal JSON: {removal_data}")
            return removal_data
        except json.JSONDecodeError as e:
            self.logger.warning(f"Standard JSON parsing failed: {e}")
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
        json_str = json_str.replace("'", '"')
        json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
        json_str = re.sub(r"//.*?\n|/\*.*?\*/", "", json_str, flags=re.DOTALL)
        json_str = json_str.strip()
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
        pattern = re.compile(r'\{.*?\}', re.DOTALL)
        matches = pattern.findall(text)
        return matches[0] if matches else None


class CodeBlockListPopulator:

    def __init__(self, code_blocks_list, left_status_label):
        self.code_blocks_list = code_blocks_list
        self.left_status_label = left_status_label
        self.logger = logger

    def populate_code_blocks_list(self, code_blocks):
        self.code_blocks_list.clear()
        for idx, block in enumerate(code_blocks):
            module_path = block.get('module_path', 'Unknown Module')
            class_name = block.get('class_name', '')
            method_name = block.get('method_name', '')
            action = block.get('action', 'update')
            item_text = f'[{action.capitalize()}] {module_path}'
            if class_name:
                item_text += f' | Class: {class_name}'
            if method_name:
                item_text += f' | Method: {method_name}'
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, block)
            self.code_blocks_list.addItem(item)
        self.left_status_label.setText(f'Loaded {len(code_blocks)} code blocks.')
        QTimer.singleShot(2000, lambda: self.left_status_label.setText(''))
        self.logger.info(f'Populated code blocks list with {len(code_blocks)} items.')

class ReAddInitialComments:

    def re_add_initial_comments(self, comments: List[str], code: str) -> str:
        if comments:
            comments_str = '\n'.join(comments) + '\n'
            updated_code = comments_str + code
            logger.debug('Re-added initial comments to the updated code.')
            return updated_code
        return code

class InitialCommentRemover:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def remove_initial_comment(self, code: str) -> str:
        code = re.sub('^#\\s*.*\\.py$', '', code, count=1, flags=re.MULTILINE).lstrip()
        self.logger.debug('Removed initial module path comment from code.')
        return code

class PathValidator:

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def exists_only(self, file_path: str) -> bool:
        exists = os.path.isfile(file_path)
        self.logger.debug(f'Validating path {file_path}: Exists={exists}')
        return exists

    def exists_readable_writable(self, file_path: str) -> bool:
        exists = os.path.isfile(file_path)
        readable = os.access(file_path, os.R_OK)
        writable = os.access(file_path, os.W_OK)
        self.logger.debug(
            f'Validating path {file_path}: Exists={exists}, Readable={readable}, Writable={writable}'
        )
        return exists and readable and writable

class DirectoryProcessor:

    def __init__(self):
        pass

    def process_directory(self, root_dir: str, output_dir: str):
        function_dict = defaultdict(list)
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    functions = self.extract_functions(file_path)
                    for func_name, func_def in functions:
                        function_dict[func_name].append((file_path, func_def))
        os.makedirs(output_dir, exist_ok=True)
        for func_name, occurrences in function_dict.items():
            output_file = os.path.join(output_dir, f'{func_name}.md')
            with open(output_file, 'w') as out_file:
                for file_path, func_def in occurrences:
                    out_file.write(f'### {file_path}\n\n')
                    out_file.write(f'```python\n{func_def}\n```\n\n')

    def extract_functions(self, file_path: str) -> List[Tuple[str, str]]:
        pass

class ImportMerger:
    def __init__(self):
        self.logger = logger

    def merge_imports(self, original_tree: ast.AST, new_tree: ast.AST):
        original_imports = [node for node in original_tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
        new_imports = [node for node in new_tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
        existing_imports_set = set(ast.dump(node) for node in original_imports)
        for new_import in new_imports:
            if ast.dump(new_import) not in existing_imports_set:
                original_tree.body.insert(0, new_import)
                self.logger.debug(f'Added import: {astor.to_source(new_import).strip()}')


class ProcessCodeBlocks:

    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def process_code_blocks(self, code_blocks: List[Dict[str, str]]):
        filename_count = {}
        for idx, block in enumerate(code_blocks):
            language = block.get('language', 'code')
            code = block['code']
            lines = code.splitlines()
            filename = None
            if lines:
                first_line = lines[0].strip()
                if first_line.startswith('#') and first_line.endswith(('.py', '.txt', '.md')):
                    filename = first_line.lstrip('#').strip()
                    code = '\n'.join(lines[1:]).strip()
            if not filename:
                filename = f'{language}_code_block_{idx + 1}.txt'
            filename = filename.replace('../', '').replace('..\\', '')
            if filename in filename_count:
                filename_count[filename] += 1
                name, ext = os.path.splitext(filename)
                filename = f'{name}_{filename_count[filename]}{ext}'
            else:
                filename_count[filename] = 1
            output_path = os.path.join(self.output_dir, filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                print(f'Saved code block to {output_path}')
            except Exception as e:
                print(f'Error saving code block to {output_path}: {e}')

class ProcessCodeBlock:

    def __init__(self, logger, file_manager, parser, integrator, validator, formatter, config):
        self.logger = logger
        self.file_manager = file_manager
        self.parser = parser
        self.integrator = integrator
        self.validator = validator
        self.formatter = formatter
        self.config = config
        self.extractor = ExtractAndRemoveSpecialImports()
        self.path_extractor = ModulePathExtractor()
        self.code_processor = CodeBlockProcessor()

    def implementation_version1(self, block: Dict, return_diff: bool = False) -> Tuple[bool, str, Optional[str]]:
        try:
            new_code_block = block.get('code_block')
            if not new_code_block:
                raise ValueError("Code block is empty or missing")

            # Extract module path
            module_path = self.path_extractor.extract_module_path(new_code_block)
            if not module_path:
                raise ValueError("Module path is missing in the code block")

            # Process the code block
            processed_block = self.code_processor.process_code_block(new_code_block)
            
            # Extract special imports and removals
            imports, cleaned_code, removals = self.extractor.extract_and_remove_special_imports(processed_block['code'])

            # Handle file operations
            if not self.file_manager.validate_path(module_path):
                if self.config.get_config_value('create_missing_modules', True):
                    self.file_manager.create_module(module_path)
                else:
                    raise FileNotFoundError(f"Module {module_path} does not exist")

            original_code = self.file_manager.read_file(module_path)
            
            # Parse and update the AST
            tree = self.parser.parse_code(original_code)
            
            # Handle removals
            for removal in removals:
                self.integrator.remove_node(tree, removal)
            
            # Handle additions
            for addition in processed_block['additions']:
                self.integrator.add_node(tree, self.parser.parse_code(addition).body[0])
            
            # Handle modifications
            for modification in processed_block['modifications']:
                self.integrator.modify_node(tree, self.parser.parse_code(modification).body[0])
            
            # Integrate the cleaned code
            self.integrator.integrate_nodes(tree, self.parser.parse_code(cleaned_code).body)
            
            # Add special imports
            for import_stmt in imports:
                self.integrator.add_import(tree, import_stmt)
            
            updated_code = self.parser.ast_to_code(tree)

            # Validate and format
            if not self.validator.validate_syntax(updated_code, module_path):
                raise SyntaxError("Updated code has syntax errors")

            if not self.config.get_config_value('preserve_formatting', True):
                updated_code = self.formatter.format_code(updated_code)

            # Write updated code
            self.file_manager.write_file(module_path, updated_code)

            if return_diff:
                diff = ''.join(difflib.unified_diff(
                    original_code.splitlines(keepends=True),
                    updated_code.splitlines(keepends=True),
                    fromfile='original',
                    tofile='updated',
                    lineterm=''
                ))
                return True, f'Updated module {module_path}.', diff

            return True, f'Updated module {module_path}.', None

        except Exception as e:
            error_msg = f"Error processing code block: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg, None

    def extract_initial_comments(self, code: str) -> Tuple[str, str]:
        lines = code.split('\n')
        initial_comments = []
        code_body = []
        for line in lines:
            if line.strip().startswith('#'):
                initial_comments.append(line)
            else:
                code_body.append(line)
        return '\n'.join(initial_comments), '\n'.join(code_body)

    def re_add_initial_comments(self, comments: str, code_body: str) -> str:
        return f"{comments}\n{code_body}" if comments else code_body


class LlmProcessor:
    """
    Handles LLM output processing and integrates it with the backend controller.
    This version is designed to work without GUI elements.
    """

    def __init__(self, backend_controller):
        """
        Initialize the LlmProcessor with the backend controller.

        :param backend_controller: The controller instance responsible for handling backend processes.
        """
        self.backend_controller = backend_controller
        self.logger = logging.getLogger(__name__)

    def process_llm_output(self, text: str, auto_run: bool = False) -> List[Dict[str, Any]]:
        """
        Process LLM output, extract code blocks, and optionally process them automatically.

        :param text: The LLM output text to process.
        :param auto_run: If True, all code blocks are processed automatically.
        :return: List of extracted code blocks.
        """
        if not text:
            self.logger.warning('No text provided for processing.')
            return []

        # Extract code blocks from the LLM output text
        code_blocks = self.extract_code_blocks_from_text(text)
        if not code_blocks:
            self.logger.warning('No valid code blocks found in the input.')
            return []

        self.logger.info(
            f"Processing {'all' if auto_run else 'selected'} {len(code_blocks)} code blocks."
        )

        # Automatically process code blocks if auto_run is True
        if auto_run:
            self.process_code_blocks(code_blocks)

        return code_blocks

    def extract_code_blocks_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract code blocks from the provided text.

        :param text: The input text containing potential code blocks.
        :return: A list of dictionaries representing extracted code blocks.
        """
        return self.backend_controller.extractor.extract_code_blocks(text)

    def process_code_blocks(self, code_blocks: List[Dict[str, Any]]):
        """
        Process each code block and handle the backend controller logic.

        :param code_blocks: List of code blocks to process.
        """
        for idx, block in enumerate(code_blocks):
            self.logger.info(f"Processing code block {idx + 1}...")
            self.process_code_block(block)

    def process_code_block(self, block: Dict[str, Any]):
        """
        Process an individual code block by passing it to the backend controller.

        :param block: The code block to process.
        """
        success, message, diff = self.backend_controller.process_code_block(block)
        if success:
            self.logger.info(message)
            if diff:
                self.logger.debug(f'Diff:\n{diff}')
        else:
            self.logger.error(message)
            if diff:
                self.logger.debug(f'Diff:\n{diff}')

class CodeRemovalProcessor:

    def __init__(self, file_manager, parser, code_remover, validator, formatter, config_manager, logger):
        self.file_manager = file_manager
        self.parser = parser
        self.code_remover = code_remover
        self.validator = validator
        self.formatter = formatter
        self.config_manager = config_manager
        self.logger = logger

    def process_removal_block(self, block: Dict[str, Any], return_diff: bool = False) -> Tuple[bool, str, Optional[str]]:
        removal_instructions = block.get('removal_instructions', {})
        module_path = removal_instructions.get('module_path')
        if not module_path:
            self.logger.error('Module path is missing in the removal instructions.')
            return False, 'Module path is missing in the removal instructions.', None

        if not self.file_manager.validate_path(module_path):
            self.logger.error(f'Module {module_path} does not exist.')
            return False, f'Module {module_path} does not exist.', None

        original_code = self.file_manager.read_file(module_path)
        self.logger.info(f'Module ready for removal: {module_path}')

        try:
            existing_tree = self.parser.parse_code(original_code)
        except SyntaxError as e:
            self.logger.error(f'Syntax error in existing code: {e}')
            return False, f'Syntax error in existing code: {e}', None

        self.logger.info('Removing specified code elements...')
        existing_tree = self.code_remover.remove_code(existing_tree, removal_instructions)

        try:
            updated_code = astor.to_source(existing_tree)
            self.logger.debug('Converted updated AST back to source code.')
        except Exception as e:
            self.logger.error(f'Error converting AST to source code: {e}')
            return False, f'Error converting AST to source code: {e}', None

        self.logger.info('Validating updated code syntax...')
        if not self.validator.validate_syntax_optional(updated_code, module_path):
            self.logger.error('Updated code has syntax errors.')
            return False, 'Updated code has syntax errors.', None

        if not self.config_manager.get_config_value('preserve_formatting', True):
            self.logger.info('Formatting the code using Black...')
            updated_code = self.formatter.format_code(updated_code)
        else:
            self.logger.info('Preserving original code formatting.')

        self.logger.info('Writing updated code to file...')
        try:
            self.file_manager.write_file(module_path, updated_code)
            self.logger.info(f'Module {module_path} has been updated after removal.')
        except Exception as e:
            self.logger.error(f'Error writing updated code to {module_path}: {e}')
            return False, f'Error writing updated code to {module_path}: {e}', None

        if return_diff:
            original_lines = original_code.splitlines(keepends=True)
            updated_lines = updated_code.splitlines(keepends=True)
            try:
                diff = ''.join(
                    difflib.unified_diff(
                        original_lines,
                        updated_lines,
                        fromfile='original',
                        tofile='updated',
                        lineterm=''
                    )
                )
                self.logger.debug('Generated diff for the removal block.')
                return True, f'Removed specified elements from {module_path}.', diff
            except Exception as e:
                self.logger.error(f'Error generating diff: {e}')
                return False, f'Removed specified elements from {module_path}, but failed to generate diff: {e}', None
        else:
            return True, f'Removed specified elements from {module_path}.', None

    def remove_code(self, tree: ast.AST, removal_instructions: Dict[str, Any]) -> ast.AST:
        return self.code_remover.remove_code(tree, removal_instructions)

class CodeBlockProcessor:

    def __init__(self):
        self.logger = logger

    def process_code_block(self, code: str) -> Dict[str, Any]:
        lines = code.split('\n')
        result = {
            'additions': [],
            'modifications': [],
            'code': []
        }
        current_action = None
        for line in lines:
            if line.strip() == '#ADD':
                current_action = 'additions'
            elif line.strip() == '#MODIFY':
                current_action = 'modifications'
            elif current_action:
                result[current_action].append(line)
            else:
                result['code'].append(line)

        result['code'] = '\n'.join(result['code'])
        self.logger.debug(f"Processed code block: {len(result['additions'])} additions, {len(result['modifications'])} modifications")
        return result

class FileManager:

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def validate_path(self, file_path: str) -> bool:
        exists = os.path.isfile(file_path)
        self.logger.debug(f'Validating file path {file_path}: Exists={exists}')
        return exists

    def create_module(self, module_path: str):
        os.makedirs(os.path.dirname(module_path), exist_ok=True)
        with open(module_path, 'w') as f:
            f.write('')
        self.logger.info(f'Created new module at {module_path}')

    def read_file(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.logger.debug(f'Read content from {file_path}')
        return content

    def write_file(self, file_path: str, content: str):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        self.logger.debug(f'Wrote updated content to {file_path}')

class CodeRemover:

    def __init__(self, logger=None, parser=None, enable_removal=True):
        self.logger = logger or logging.getLogger(__name__)
        self.parser = parser or CodeParser(logger=self.logger)
        self.enable_removal = enable_removal

    def remove_code(self, tree: ast.AST, removal_instructions: Dict[str, Any]) -> ast.AST:
        """
        Removes code elements specified in the removal_instructions from the AST if enabled.
        """
        if not self.enable_removal:
            self.logger.debug("Code removal is disabled.")
            return tree

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
            elif target_type == "method":
                class_name = target.get("class_name")
                if class_name:
                    self.remove_method(tree, class_name, name)
                else:
                    self.logger.warning(f"Class name is missing for method removal: {name}")
            else:
                self.logger.warning(f"Unknown target type: {target_type}")

        return tree

    def remove_class(self, tree: ast.AST, class_name: str) -> ast.AST:
        original_len = len(tree.body)
        tree.body = [
            node for node in tree.body
            if not (isinstance(node, ast.ClassDef) and node.name == class_name)
        ]
        if len(tree.body) < original_len:
            self.logger.debug(f"Removed class: {class_name}")
        else:
            self.logger.warning(f"Class {class_name} not found for removal.")
        return tree

    def remove_function(self, tree: ast.AST, function_name: str) -> ast.AST:
        original_len = len(tree.body)
        tree.body = [
            node for node in tree.body
            if not (isinstance(node, ast.FunctionDef) and node.name == function_name)
        ]
        if len(tree.body) < original_len:
            self.logger.debug(f"Removed function: {function_name}")
        else:
            self.logger.warning(f"Function {function_name} not found for removal.")
        return tree

    def remove_method(self, tree: ast.AST, class_name: str, method_name: str) -> ast.AST:
        class_node = self.parser.find_class(tree, class_name)
        if class_node:
            original_len = len(class_node.body)
            class_node.body = [
                item for item in class_node.body
                if not (isinstance(item, ast.FunctionDef) and item.name == method_name)
            ]
            if len(class_node.body) < original_len:
                self.logger.debug(f"Removed method: {method_name} from class {class_name}")
            else:
                self.logger.warning(f"Method {method_name} not found in class {class_name}")
        else:
            self.logger.warning(f"Class {class_name} not found while attempting to remove method {method_name}")
        return tree

    def remove_assignments(self, tree: ast.AST, variable_names: List[str]) -> ast.AST:
        """
        Removes variable assignments from the AST.
        """
        original_len = len(tree.body)
        tree.body = [
            node
            for node in tree.body
            if not (
                isinstance(node, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id in variable_names
                    for t in node.targets
                )
            )
        ]
        if len(tree.body) < original_len:
            self.logger.debug(f"Removed assignments for variables: {', '.join(variable_names)}")
        else:
            self.logger.warning(f"Assignments for variables {', '.join(variable_names)} not found for removal.")
        return tree


class CodeIntegrator:
    def __init__(self, logger=None, parser=None, enable_integration: bool = True):
        self.logger = logger or logging.getLogger(__name__)
        self.parser = parser or CodeParser(logger=self.logger)
        self.enable_integration = enable_integration
        
        # Initialize ImportMerger
        self.import_merger = ImportMerger()

    def collect_and_merge_imports(self, original_tree: ast.AST, new_tree: ast.AST):
        """
        Collects and merges import statements from the new_tree into the original_tree.
        
        Args:
            original_tree (ast.AST): The AST of the existing module.
            new_tree (ast.AST): The AST of the new code block.
        """
        if not self.enable_integration:
            self.logger.debug("Import merging is disabled.")
            return
        
        self.logger.info("Merging imports from new code into existing module...")
        self.import_merger.merge_imports(original_tree, new_tree)
        self.logger.info("Import merging completed.")

    def integrate_nodes(self, original_tree: ast.AST, new_nodes: List[ast.AST]):
        """
        Integrates a list of new_nodes into the original_tree, handling each node appropriately.
        """
        if not self.enable_integration:
            self.logger.debug("Code integration is disabled.")
            return

        for new_node in new_nodes:
            self.integrate_node(original_tree, new_node)

    def integrate_node(self, original_tree: ast.AST, new_node: ast.AST):
        """
        Determines the type of new_node and delegates to the appropriate integration method.
        """
        if isinstance(new_node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            self.integrate_definition(original_tree, new_node)
        elif isinstance(new_node, ast.Assign):
            self.integrate_assignment(original_tree, new_node)
        elif isinstance(new_node, (ast.Import, ast.ImportFrom)):
            self.integrate_import(original_tree, new_node)
        else:
            original_tree.body.append(new_node)
            self.logger.debug(f"Added new node: {type(new_node).__name__}")

    def integrate_definition(self, original_tree: ast.AST, new_node: ast.AST):
        """
        Integrates function, async function, or class definitions into the original_tree.
        """
        for i, node in enumerate(original_tree.body):
            if isinstance(node, type(new_node)) and getattr(node, 'name', None) == getattr(new_node, 'name', None):
                original_tree.body[i] = new_node
                self.logger.debug(f"Updated existing {type(new_node).__name__}: {new_node.name}")
                return
        original_tree.body.append(new_node)
        self.logger.debug(f"Added new {type(new_node).__name__}: {new_node.name}")

    def integrate_assignment(self, original_tree: ast.AST, new_node: ast.Assign):
        """
        Integrates assignment statements into the original_tree, replacing existing assignments with the same targets.
        """
        new_targets = [t.id for t in new_node.targets if isinstance(t, ast.Name)]
        for i, node in enumerate(original_tree.body):
            if isinstance(node, ast.Assign):
                existing_targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
                if set(new_targets) == set(existing_targets):
                    original_tree.body[i] = new_node
                    self.logger.debug(f"Updated existing assignment: {', '.join(new_targets)}")
                    return
        original_tree.body.append(new_node)
        self.logger.debug(f"Added new assignment: {', '.join(new_targets)}")

    def integrate_import(self, original_tree: ast.AST, new_node: ast.AST):
        """
        Integrates import statements into the original_tree, avoiding duplicates.
        """
        for node in original_tree.body:
            if isinstance(node, type(new_node)) and ast.dump(node) == ast.dump(new_node):
                self.logger.debug(f"Import already exists: {ast.dump(new_node)}")
                return
        original_tree.body.insert(0, new_node)
        self.logger.debug(f"Added new import: {ast.dump(new_node)}")

    def remove_node(self, tree: ast.AST, node_name: str):
        """
        Removes a node from the tree based on its name.
        """
        original_len = len(tree.body)
        tree.body = [node for node in tree.body if not (hasattr(node, 'name') and node.name == node_name)]
        if len(tree.body) < original_len:
            self.logger.debug(f"Removed node: {node_name}")
        else:
            self.logger.warning(f"Node {node_name} not found for removal")

    def add_node(self, tree: ast.AST, node: ast.AST):
        """
        Adds a new node to the tree.
        """
        tree.body.append(node)
        self.logger.debug(f"Added new node: {type(node).__name__}")

    def modify_node(self, tree: ast.AST, new_node: ast.AST):
        """
        Modifies an existing node in the tree with new_node.
        """
        for i, node in enumerate(tree.body):
            if isinstance(node, type(new_node)) and hasattr(node, 'name') and node.name == new_node.name:
                tree.body[i] = new_node
                self.logger.debug(f"Modified node: {new_node.name}")
                return
        self.logger.warning(f"Node {new_node.name} not found for modification")

    def add_import(self, tree: ast.AST, import_stmt: str):
        """
        Parses and adds an import statement to the tree.
        """
        new_import = self.parser.parse_code(import_stmt).body[0]
        self.integrate_import(tree, new_import)


class SyntaxValidator:

    def __init__(self, logger=None, enable_validation=True):
        self.logger = logger or logging.getLogger(__name__)
        self.enable_validation = enable_validation

    def validate_syntax_strict(self, code: str, filename: str) -> bool:
        try:
            compile(code, filename, 'exec')
            self.logger.debug(f'Code in {filename} passed syntax validation.')
            return True
        except SyntaxError as e:
            self.logger.error(f'Syntax error in code {filename}: {e}')
            return False

    def validate_syntax_optional(self, code: str, filename: str) -> bool:
        if not self.enable_validation:
            self.logger.debug('Code validation is disabled.')
            return True
        return self.validate_syntax_strict(code, filename)

class ConfigManager:
    """
    Manages application configuration by interfacing directly with the config module's attributes.
    Provides a dictionary-like interface for easy access and modification of configuration settings.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        self.validate_config()

    def setup_logging(self):
        """
        Sets up the logging configuration based on LOGGING_LEVEL and LOG_FILE.
        """
        logging.basicConfig(
            level=self.get_config_value('LOGGING_LEVEL', logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.get_config_value('LOG_FILE', 'app.log')),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger.debug("Logging has been configured.")

    def get_config_value(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Retrieves a configuration value from config.py, with an optional default.

        Args:
            key (str): The configuration key to retrieve.
            default (Optional[Any]): The default value if the key is not found.

        Returns:
            Any: The value of the configuration key.
        """
        value = getattr(config, key, default)
        self.logger.debug(f'Config value for "{key}": {value}')
        return value

    def set_config_value(self, key: str, value: Any):
        """
        Updates a configuration value in config.py by setting the module's attribute.

        Args:
            key (str): The configuration key to update.
            value (Any): The new value for the configuration key.

        Note:
            This modifies the module-level variable, which affects all imports.
        """
        if hasattr(config, key):
            setattr(config, key, value)
            self.logger.debug(f"Set config value for '{key}' to '{value}'")
        else:
            self.logger.warning(f"Key '{key}' not found in config.")

    def all_config(self) -> Dict[str, Any]:
        """
        Returns all configuration settings from config.py as a dictionary.

        Returns:
            Dict[str, Any]: A dictionary of all configuration settings.
        """
        return {
            attr: getattr(config, attr)
            for attr in dir(config)
            if not attr.startswith("__") and not callable(getattr(config, attr))
        }

    def validate_config(self):
        """
        Validates configuration settings against expected types.
        Logs any discrepancies and ensures each setting is correctly typed.
        """
        default_config = self.default_config()
        for key, default_value in default_config.items():
            current_value = getattr(config, key, None)
            if current_value is None:
                setattr(config, key, default_value)
                self.logger.warning(f"Missing config key '{key}'. Using default value: {default_value}")
            elif not isinstance(current_value, type(default_value)):
                self.logger.warning(
                    f"Invalid type for config key '{key}'. Expected {type(default_value).__name__}, "
                    f"got {type(current_value).__name__}. Using default value: {default_value}"
                )
                setattr(config, key, default_value)

    def default_config(self) -> Dict[str, Any]:
        """
        Provides a dictionary of default configuration values based on the existing config.py values.

        Returns:
            Dict[str, Any]: A dictionary of default configuration values.
        """
        return {
            "APP_NAME": config.APP_NAME,
            "APPLICATION_NAME": config.APPLICATION_NAME,
            "COMPANY_NAME": config.COMPANY_NAME,
            "VERSION": config.VERSION,
            "DEBUG_MODE": config.DEBUG_MODE,
            "WINDOW_WIDTH": config.WINDOW_WIDTH,
            "WINDOW_HEIGHT": config.WINDOW_HEIGHT,
            "DEFAULT_WINDOW_SIZE": config.DEFAULT_WINDOW_SIZE,
            "ENABLE_PHONE_LAYOUT": config.ENABLE_PHONE_LAYOUT,
            "THEME_DARK": config.THEME_DARK,
            "THEME_LIGHT": config.THEME_LIGHT,
            "THEME_OPTIONS": config.THEME_OPTIONS,
            "DEFAULT_THEME": config.DEFAULT_THEME,
            "CURRENT_THEME": config.CURRENT_THEME,
            "DESKTOP_PAGES_DIR": config.DESKTOP_PAGES_DIR,
            "PHONE_PAGES_DIR": config.PHONE_PAGES_DIR,
            "SYSTEM_PROMPTS_PATH": config.SYSTEM_PROMPTS_PATH,
            "OUTPUT_DIRECTORY": config.OUTPUT_DIRECTORY,
            "LOG_DIR": config.LOG_DIR,
            "LOG_FILE": config.LOG_FILE,
            "INPUT_FILE": config.INPUT_FILE,
            "LOGGING_LEVEL": config.LOGGING_LEVEL,
            "MAX_LOG_FILE_SIZE": config.MAX_LOG_FILE_SIZE,
            "BACKUP_COUNT": config.BACKUP_COUNT,
            "ERROR_MESSAGES": config.ERROR_MESSAGES,
            "SENSITIVE_PATTERNS": config.SENSITIVE_PATTERNS,
            "LAST_PAGE_KEY": config.LAST_PAGE_KEY,
            "DEFAULT_LAST_PAGE": config.DEFAULT_LAST_PAGE,
            "DEBUG_WORKFLOW": config.DEBUG_WORKFLOW,
            "ENABLE_BACKUP": config.ENABLE_BACKUP,
            "ENABLE_FORMATTING": config.ENABLE_FORMATTING,
            "ENABLE_INTEGRATION": config.ENABLE_INTEGRATION,
            "ENABLE_REMOVAL": config.ENABLE_REMOVAL,
            "ENABLE_VALIDATION": config.ENABLE_VALIDATION,
            "ENABLE_VERSION_CONTROL": config.ENABLE_VERSION_CONTROL,
            "STRICT_PARSING": config.STRICT_PARSING,
            "CREATE_MISSING_MODULES": config.CREATE_MISSING_MODULES,
            "PRESERVE_FORMATTING": config.PRESERVE_FORMATTING,
            "USE_WORKSPACE_ROOT": config.USE_WORKSPACE_ROOT,
            "WORKSPACE_ROOT": config.WORKSPACE_ROOT
        }

    @property
    def config(self):
        """
        Provides a dictionary-like interface to the configuration.
        Allows getting and setting configuration values like a dict.

        Returns:
            ConfigDict: An instance that behaves like a dictionary for configuration access.
        """
        manager = self

        class ConfigDict:
            def __getitem__(self, key):
                return manager.get_config_value(key)

            def __setitem__(self, key, value):
                manager.set_config_value(key, value)

            def get(self, key, default=None):
                return manager.get_config_value(key, default)

            def items(self):
                return manager.all_config().items()

            def __contains__(self, key):
                return hasattr(config, key)

            def __repr__(self):
                return f"ConfigDict({manager.all_config()})"

        return ConfigDict()
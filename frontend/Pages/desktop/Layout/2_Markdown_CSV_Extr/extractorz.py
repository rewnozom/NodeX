# -*- coding: utf-8 -*-
# ./frontend/Pages/desktop/Layout/Markdown_CSV_Extr/Extractorz.py

from PySide6.QtCore import QObject, Signal, Slot

import os
import pandas as pd

import os
import pandas as pd
import os
import re
import toml
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any

import os
import re
import toml
import zipfile
import shutil
import pandas as pd
from pathlib import Path
import os
import re
import toml
import zipfile
import shutil
import pandas as pd
from pathlib import Path



class MarkdownEx:
    def __init__(self, base_dir, output_dir, settings_path):
        self.base_dir = os.path.normpath(base_dir).replace('\\', '/')
        self.output_dir = os.path.normpath(output_dir).replace('\\', '/')
        self.extract_dir = os.path.normpath(os.path.join(base_dir, 'extract')).replace('\\', '/')
        self.settings_path = os.path.normpath(settings_path).replace('\\', '/')
        self.settings = self.load_settings()
        self.update_progress = None  # For GUI progress
        self.update_status = None    # For GUI status messages
        self._is_running = True
        os.makedirs(self.output_dir, exist_ok=True)

    def stop(self):
        """Stop the extraction process gracefully."""
        self._is_running = False

    def load_settings(self):
        """Load TOML settings and normalize paths."""
        try:
            settings = toml.load(self.settings_path)
            self.normalize_paths(settings)
            
            # Ensure paths section exists
            if 'paths' not in settings:
                settings['paths'] = {}
            
            # Always set Windows as default path style if not specified
            settings['paths']['path_style'] = settings['paths'].get('path_style', 'windows')
            
            return settings
        except toml.TomlDecodeError as e:
            print(f"Error loading settings: {e}")
            raise

    def normalize_paths(self, settings_dict):
        """Recursively normalize all paths in the loaded settings."""
        for section in settings_dict:
            for key, value in settings_dict[section].items():
                if isinstance(value, str) and ('/' in value or '\\' in value):
                    settings_dict[section][key] = os.path.normpath(value).replace('\\', '/')
                elif isinstance(value, list):
                    settings_dict[section][key] = [
                        os.path.normpath(item).replace('\\', '/') 
                        if isinstance(item, str) and ('/' in item or '\\' in item) else item
                        for item in value
                    ]
                elif isinstance(value, dict):
                    self.normalize_paths(value)

    def save_settings(self):
        """If your app needs to write updated settings, implement here."""
        with open(self.settings_path, 'w') as settings_file:
            toml.dump(self.settings, settings_file)

    def should_skip_directory(self, dir_path):
        """Check if directory should be skipped based on 'skip_paths' or ignored dirs."""
        for skip_path in self.settings['paths'].get('skip_paths', []):
            if dir_path.startswith(skip_path) or os.path.basename(dir_path) in self.settings['directories']['ignored_directories']:
                return True
        return False

    def format_path(self, relative_path):
        """Format the path based on the selected path style."""
        path = relative_path.replace('/', os.sep)
        # Default to windows style if path_style is not set or is invalid
        path_style = self.settings.get('paths', {}).get('path_style', 'windows')
        if path_style.lower() != 'unix':  # If not explicitly unix, use windows
            formatted_path = os.path.join('..', path).replace('/', '\\')
        else:
            formatted_path = os.path.join('.', path).replace('\\', '/')
        return formatted_path

    def get_files_in_directory(self, directory):
        """
        Collect all eligible files in 'directory' unless
        'use_file_specific' is True, in which case only use 'specific_files'.
        """
        if self.settings['file_specific']['use_file_specific']:
            return [
                os.path.normpath(os.path.join(directory, file))
                for file in self.settings['file_specific']['specific_files']
            ]

        file_paths = []
        ignored_extensions = set(self.settings['files']['ignored_extensions'])
        ignored_files = set(self.settings['files']['ignored_files'])

        for root, dirs, files in os.walk(directory):
            if not self._is_running:
                if self.update_status:
                    self.update_status("Markdown extraction stopped by user.")
                break

            # Skip directories if needed
            if self.should_skip_directory(os.path.relpath(root, directory)):
                dirs[:] = []
                continue

            # Filter out ignored directories
            dirs[:] = [d for d in dirs if d not in self.settings['directories']['ignored_directories']]

            for file in files:
                if not self._is_running:
                    if self.update_status:
                        self.update_status("Markdown extraction stopped by user.")
                    break

                if file in ignored_files:
                    continue
                if os.path.splitext(file)[1].lower() in ignored_extensions:
                    continue
                file_paths.append(os.path.normpath(os.path.join(root, file)))

        return file_paths

    @staticmethod
    def is_binary_file(file_path):
        """Heuristic check if a file is binary by looking for NULL bytes."""
        try:
            file_path = os.path.normpath(file_path)
            with open(file_path, 'rb') as file:
                data = file.read(1024)
            if not data:
                return False
            if b'\0' in data:
                return True
            return False
        except Exception as e:
            print(f"Error checking if file is binary: {str(e)}")
            return True

    def create_table_of_contents(self, file_paths):
        """Generate a simple Table of Contents with links referencing local anchors."""
        toc = "# Table of Contents\n"
        for file_path in file_paths:
            if not self._is_running:
                if self.update_status:
                    self.update_status("Markdown extraction stopped by user.")
                break
            relative_path = os.path.relpath(file_path, self.extract_dir)
            # Make anchor-friendly
            anchor = relative_path.replace(' ', '-').replace('.', '').replace('\\', '-').replace('/', '-')
            toc += f"- [{relative_path}](#{anchor})\n"
        return toc

    def create_where_file_lines(self, file_lines_info):
        """
        Create a helper section documenting start/end lines for each file block,
        plus an example snippet for re-extracting code blocks from the final Markdown.
        """
        content = (
            "## Where each File line for each ## File: ..\\filename: \n\n"
            "## To extract code blocks from this markdown file, use the following Python script:\n\n"
            "```python\n"
            "def extract_code_blocks(file_path, instructions):\n"
            "    with open(file_path, 'r') as file:\n"
            "        lines = file.readlines()\n"
            "    for instruction in instructions:\n"
            "        file_name = instruction['file']\n"
            "        start_line = instruction['start_line'] - 1\n"
            "        end_line = instruction['end_line']\n"
            "        code = ''.join(lines[start_line:end_line])\n"
            "        print(f\"## Extracted Code from {file_name}\")\n"
            "        print(code)\n"
            "        print(\"#\" * 80)\n\n"
            "# Example instructions\n"
            "instructions = [\n"
            "    {'file': '../example.py', 'start_line': 1, 'end_line': 10},\n"
            "]\n\n"
            "file_path = 'Full_Project_00.md'\n"
            "extract_code_blocks(file_path, instructions)\n"
            "```\n\n"
        )

        for file_path, (start_line, end_line) in file_lines_info.items():
            if not self._is_running:
                if self.update_status:
                    self.update_status("Markdown extraction stopped by user.")
                break
            content += f"## File: {file_path}\n"
            content += f"Line = {start_line}, Starts = {start_line + 2}, Ends = {end_line + 1}\n\n"

        return content

    def create_markdown_for_files(self, file_paths: List[str]) -> Tuple[str, str]:
        """
        Enhanced markdown creation supporting multiple format styles.
        """
        toc = self.create_table_of_contents(file_paths) + "\n\n"
        markdown_content = "# Project Details\n\n" + toc
        file_lines_info = {}
        line_counter = markdown_content.count('\n') + 1
        
        total_files = len(file_paths)
        for idx, file_path in enumerate(file_paths, 1):
            if not self._is_running:
                if self.update_status:
                    self.update_status("Markdown extraction stopped by user.")
                break
                
            try:
                file_path = os.path.normpath(file_path)
                relative_path = os.path.relpath(file_path, self.extract_dir)
                formatted_path = self.format_path(relative_path)
                
                # Determine comment style based on file type
                comment_prefix = self._get_comment_prefix(file_path)
                
                if self.is_binary_file(file_path):
                    markdown_content += (
                        f"# File: {formatted_path}\n\n"
                        f"**Binary file cannot be displayed.**\n\n"
                        "---\n\n"
                    )
                    line_counter += 5
                else:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    file_extension = os.path.splitext(file_path)[1].lower().lstrip('.')
                    
                    # Create section with multiple reference formats
                    section_content = (
                        f"# {formatted_path}\n"
                        f"## File: {formatted_path}\n\n"
                        f"```{file_extension}\n"
                        f"{comment_prefix} {formatted_path}\n"
                        f"{content}\n"
                        "```\n\n"
                        "---\n\n"
                    )
                    
                    start_line = line_counter
                    line_counter += section_content.count('\n')
                    end_line = line_counter - 1
                    
                    file_lines_info[formatted_path] = (start_line, end_line)
                    markdown_content += section_content
                    
            except Exception as e:
                print(f"Error processing file {file_path}: {str(e)}")
                if self.update_status:
                    self.update_status(f"Error processing file: {os.path.basename(file_path)}")
                continue
                
            if self.update_progress:
                self.update_progress(int(idx * 100 / total_files))
                
        where_file_lines = self.create_where_file_lines(file_lines_info)
        return markdown_content, where_file_lines

    def _get_comment_prefix(self, file_path: str) -> str:
        """
        Get appropriate comment prefix based on file type.
        """
        comment_styles = {
            '.py': '#',
            '.rb': '#',
            '.sh': '#',
            '.yml': '#',
            '.yaml': '#',
            '.js': '//',
            '.jsx': '//',
            '.ts': '//',
            '.tsx': '//',
            '.java': '//',
            '.cpp': '//',
            '.c': '//',
            '.cs': '//',
            '.php': '//',
            '.go': '//',
            '.swift': '//',
            '.kt': '//',
            '.rs': '//',
            '.dart': '//',
            '.lua': '--',
            '.sql': '--',
            '.hs': '--',
            '.elm': '--',
            '.vim': '"',
            '.r': '#',
            '.ps1': '#',
            '.matlab': '%',
            '.octave': '%',
        }
        
        ext = os.path.splitext(file_path)[1].lower()
        return comment_styles.get(ext, '#')

    def save_markdown(self, markdown_content, where_file_lines, output_dir):
        """
        Create or increment the markdown file name and
        create a companion file with line references.
        """
        prefix = self.settings['output']['markdown_file_prefix']
        existing_files = [
            f for f in os.listdir(output_dir)
            if f.startswith(prefix) and f.endswith('.md')
        ]
        existing_files = [
            f for f in existing_files
            if re.match(rf'{prefix}_\d{{2}}\.md', f)
        ]

        if not existing_files:
            main_output_path = os.path.join(output_dir, f'{prefix}_00.md')
            where_file_lines_path = os.path.join(output_dir, f'{prefix}_00_where_each_file_line_is.md')
        else:
            existing_files.sort()
            last_file = existing_files[-1]
            last_index = int(last_file.split('_')[-1].split('.')[0])
            next_index = last_index + 1
            main_output_path = os.path.join(output_dir, f'{prefix}_{next_index:02d}.md')
            where_file_lines_path = os.path.join(output_dir, f'{prefix}_{next_index:02d}_where_each_file_line_is.md')

        # Write main markdown
        with open(main_output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        # Write reference file
        with open(where_file_lines_path, 'w', encoding='utf-8') as f:
            f.write(where_file_lines)

        return main_output_path, where_file_lines_path

    def run(self):
        """Main entry point for running the Markdown extraction."""
        if not os.path.exists(self.settings_path):
            raise FileNotFoundError(f"Settings file not found: {self.settings_path}")

        output_dir = self.settings['paths']['output_dir']
        presets = self.settings.get('presets', {})
        total_presets = len(presets)

        if total_presets == 0:
            if self.update_status:
                self.update_status("No presets found in settings")
            return

        for idx, preset_name in enumerate(presets, 1):
            if not self._is_running:
                if self.update_status:
                    self.update_status("Markdown extraction stopped by user.")
                break

            if self.update_status:
                self.update_status(f"Processing preset {idx}/{total_presets}: {preset_name}")

            try:
                preset_output_dir = os.path.normpath(os.path.join(output_dir, preset_name)).replace('\\', '/')
                os.makedirs(preset_output_dir, exist_ok=True)

                specific_files = presets[preset_name]
                file_paths = [
                    os.path.normpath(os.path.join(self.base_dir, file)).replace('\\', '/')
                    for file in specific_files
                ]

                if not file_paths:
                    if self.update_status:
                        self.update_status(f"No files found for preset: {preset_name}")
                    continue

                markdown_content, where_file_lines = self.create_markdown_for_files(file_paths)
                main_output_path, where_file_lines_path = self.save_markdown(
                    markdown_content,
                    where_file_lines,
                    preset_output_dir
                )

                if self.update_status:
                    self.update_status(f"Created files:\n{main_output_path}\n{where_file_lines_path}")

                if self.update_progress:
                    self.update_progress(int(idx * 100 / total_presets))

            except Exception as e:
                error_message = f"Error processing preset {preset_name}: {str(e)}"
                print(error_message)
                if self.update_status:
                    self.update_status(error_message)
                continue

        if self.update_status and self._is_running:
            self.update_status("Markdown extraction complete for all presets")



class CSVEx:
    def __init__(self, base_dir, output_dir, settings_path):
        self.base_dir = os.path.normpath(base_dir).replace('\\', '/')
        self.output_dir = os.path.normpath(output_dir).replace('\\', '/')
        self.extracted_dir = os.path.normpath(os.path.join(base_dir, 'extracted')).replace('\\', '/')
        self.settings_path = os.path.normpath(settings_path).replace('\\', '/')
        self.settings = self.load_settings()
        self.update_progress = None  # For GUI progress
        self.update_status = None    # For GUI status messages
        self._is_running = True
        os.makedirs(self.output_dir, exist_ok=True)

    def stop(self):
        """Stop the extraction process gracefully."""
        self._is_running = False

    def load_settings(self):
        """Load TOML settings for CSV extraction."""
        try:
            settings = toml.load(self.settings_path)
            self.normalize_paths(settings)
            return settings
        except toml.TomlDecodeError as e:
            print(f"Error loading settings: {e}")
            raise

    def normalize_paths(self, settings_dict):
        """Normalize all string paths in the loaded CSV settings."""
        for section in settings_dict:
            for key, value in settings_dict[section].items():
                if isinstance(value, str) and ('/' in value or '\\' in value):
                    settings_dict[section][key] = os.path.normpath(value).replace('\\', '/')
                elif isinstance(value, list):
                    settings_dict[section][key] = [
                        os.path.normpath(item).replace('\\', '/') 
                        if isinstance(item, str) and ('/' in item or '\\' in item) else item
                        for item in value
                    ]
                elif isinstance(value, dict):
                    self.normalize_paths(value)

    def save_settings(self):
        """If your app needs to write updated settings, implement here."""
        with open(self.settings_path, 'w') as settings_file:
            toml.dump(self.settings, settings_file)

    @staticmethod
    def extract_zip(zip_path, extract_to):
        """
        Simple static method to extract a ZIP file.
        If you need progress or cancellation checks, do them here.
        """
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

    @staticmethod
    def count_file_metrics(file_path):
        """Count basic metrics: total chars, total words, total lines."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                char_count = len(content)
                word_count = len(content.split())
                line_count = content.count("\n") + 1
            return char_count, word_count, line_count
        except Exception as e:
            print(f"Error counting metrics for {file_path}: {str(e)}")
            return 0, 0, 0

    @staticmethod
    def count_classes_functions_variables(file_path):
        """
        Count naive occurrences of 'class', 'def', and simple 'variable = ' patterns.
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                class_count = len(re.findall(r'\bclass\b', content))
                function_count = len(re.findall(r'\bdef\b', content))
                variable_count = len(re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\s*=\s*', content))
            return class_count, function_count, variable_count
        except Exception as e:
            print(f"Error counting code elements for {file_path}: {str(e)}")
            return 0, 0, 0

    def should_skip_directory(self, dir_path):
        """Check if a directory should be skipped based on settings."""
        skip_paths = self.settings['paths'].get('skip_paths', [])
        for skip_path in skip_paths:
            if dir_path.startswith(skip_path) or os.path.basename(dir_path) in self.settings['directories']['ignored_directories']:
                return True
        return False

    def generate_directory_tree_with_detailed_metrics(self):
        """Traverse files and build a list of [Path, Metrics, Code] for each."""
        if self.update_status:
            self.update_status("Gathering file list...")

        if self.settings['file_specific']['use_file_specific']:
            # If only using specific files
            file_paths = [
                os.path.join(self.base_dir, file)
                for file in self.settings['file_specific']['specific_files']
            ]
        else:
            file_paths = []
            ignored_extensions = set(self.settings['files']['ignored_extensions'])
            ignored_files = set(self.settings['files']['ignored_files'])

            for root_dir, dirs, files in os.walk(self.base_dir):
                if not self._is_running:
                    if self.update_status:
                        self.update_status("CSV extraction stopped by user.")
                    break

                if self.should_skip_directory(os.path.relpath(root_dir, self.base_dir)):
                    dirs[:] = []
                    continue

                dirs[:] = [d for d in dirs if d not in self.settings['directories']['ignored_directories']]

                for file in files:
                    if not self._is_running:
                        if self.update_status:
                            self.update_status("CSV extraction stopped by user.")
                        break

                    if file in ignored_files:
                        continue

                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in ignored_extensions:
                        continue

                    file_path = os.path.join(root_dir, file)
                    file_paths.append(file_path)

        if not file_paths:
            if self.update_status:
                self.update_status("No files found to process")
            return []

        directory_tree = []
        total_files = len(file_paths)

        for idx, file_path in enumerate(file_paths, 1):
            if not self._is_running:
                if self.update_status:
                    self.update_status("CSV extraction stopped by user.")
                break

            if self.update_status:
                self.update_status(f"Processing file {idx}/{total_files}: {os.path.basename(file_path)}")

            try:
                relative_path = os.path.relpath(file_path, self.base_dir)
                size_kb = os.path.getsize(file_path) / 1024

                char_count, word_count, line_count = self.count_file_metrics(file_path)
                class_count, function_count, variable_count = self.count_classes_functions_variables(file_path)

                metrics = (
                    f"{size_kb:.2f}{self.settings['metrics']['size_unit']},"
                    f"C{char_count},W{word_count},L{line_count},"
                    f"CL{class_count},F{function_count},V{variable_count}"
                )

                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                directory_tree.append([relative_path, metrics, content])

            except Exception as e:
                print(f"Error processing file {file_path}: {str(e)}")
                if self.update_status:
                    self.update_status(f"Error processing file: {os.path.basename(file_path)}")
                continue

            if self.update_progress:
                self.update_progress(int(idx * 100 / total_files))

        return directory_tree

    def get_next_output_file_path(self, preset_output_dir):
        """
        Find an Excel filename that follows the pattern Detailed_Project_XX.xlsx,
        incrementing the index if previous files exist.
        """
        prefix = self.settings['output']['csv_file_prefix']
        existing_files = [
            f for f in os.listdir(preset_output_dir)
            if f.startswith(prefix) and f.endswith('.xlsx')
        ]

        if not existing_files:
            return os.path.join(preset_output_dir, f'{prefix}_00.xlsx')

        existing_files.sort()
        last_file = existing_files[-1]
        last_index = int(last_file.split('_')[-1].split('.')[0])
        next_index = last_index + 1
        next_file_name = f'{prefix}_{next_index:02d}.xlsx'
        return os.path.join(preset_output_dir, next_file_name)

    @staticmethod
    def clear_extracted_directory(extracted_dir):
        """Utility to clear out the extracted directory if needed."""
        if not os.path.exists(extracted_dir):
            return
        try:
            for root_dir, dirs, files in os.walk(extracted_dir):
                for file in files:
                    os.remove(os.path.join(root_dir, file))
                for d in dirs:
                    shutil.rmtree(os.path.join(root_dir, d))
        except Exception as e:
            print(f"Error clearing extracted directory: {str(e)}")

    def save_to_excel(self, data, file_path):
        """
        Convert the data list [[Path, Metrics, Code], ...] to a DataFrame
        and save it to an .xlsx file with auto-adjusted column widths.
        """
        if not data:
            if self.update_status:
                self.update_status("No data to save to Excel")
            return

        try:
            if self.update_status:
                self.update_status("Creating Excel workbook...")

            df = pd.DataFrame(data, columns=["Path", "Metrics", "Code"])
            writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name='Sheet1')

            if self.update_status:
                self.update_status("Adjusting column widths...")

            worksheet = writer.sheets['Sheet1']
            for idx, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).map(len).max(), len(col))
                worksheet.set_column(idx, idx, max_length)

            writer.close()

            if self.update_status:
                self.update_status(f"Excel file saved successfully: {os.path.basename(file_path)}")

        except Exception as e:
            print(f"Error saving Excel file: {str(e)}")
            if self.update_status:
                self.update_status(f"Error saving Excel file: {str(e)}")
            raise

    def run(self):
        """Main entry point for CSV extraction, saving results to Excel."""
        if not os.path.exists(self.settings_path):
            raise FileNotFoundError(f"Settings file not found: {self.settings_path}")

        try:
            if self.update_status:
                self.update_status("Starting extraction process...")

            presets = self.settings.get('presets', {})
            total_presets = len(presets)

            if total_presets == 0:
                if self.update_status:
                    self.update_status("No presets found in settings")
                return

            for idx, preset_name in enumerate(presets, 1):
                if not self._is_running:
                    if self.update_status:
                        self.update_status("CSV extraction stopped by user.")
                    break

                if self.update_status:
                    self.update_status(f"Processing preset {idx}/{total_presets}: {preset_name}")

                try:
                    preset_output_dir = os.path.normpath(os.path.join(self.output_dir, preset_name))
                    os.makedirs(preset_output_dir, exist_ok=True)

                    specific_files = presets[preset_name]
                    file_paths = [
                        os.path.normpath(os.path.join(self.base_dir, file))
                        for file in specific_files
                    ]

                    if not file_paths:
                        if self.update_status:
                            self.update_status(f"No files found for preset: {preset_name}")
                        continue

                    if self.update_status:
                        self.update_status(f"Generating directory tree for preset: {preset_name}")

                    directory_tree_with_detailed_metrics = self.generate_directory_tree_with_detailed_metrics()

                    if self.update_status:
                        self.update_status(f"Saving to Excel file for preset: {preset_name}")

                    output_file_path = self.get_next_output_file_path(preset_output_dir)
                    self.save_to_excel(directory_tree_with_detailed_metrics, output_file_path)

                    if self.update_status:
                        self.update_status(
                            f"Extraction complete for preset: {preset_name}. File saved: {output_file_path}"
                        )

                except Exception as e:
                    error_message = f"Error processing preset {preset_name}: {str(e)}"
                    print(error_message)
                    if self.update_status:
                        self.update_status(error_message)
                    continue

            if self.update_status and self._is_running:
                self.update_status("CSV extraction complete for all presets")

        except Exception as e:
            error_message = f"Error during CSV extraction: {str(e)}"
            print(error_message)
            if self.update_status:
                self.update_status(error_message)
            raise


@dataclass
class CodeBlock:
    path: str
    language: str
    content: str
    style: str
    update_class: Optional[str] = None

class ReverseMarkdownEx:
    def __init__(self, markdown_path: str, output_dir: str, settings_path: Optional[str] = None):
        """Initialize the markdown extractor with enhanced update capabilities."""
        self.markdown_path = markdown_path
        self.output_dir = os.path.normpath(output_dir).replace('\\', '/')
        self.settings_path = os.path.normpath(settings_path).replace('\\', '/') if settings_path else None
        self.settings = self.load_settings() if settings_path else {'paths': {'path_style': 'windows'}}
        self.update_progress = None  # For GUI progress
        self.update_status = None    # For GUI status messages
        self._is_running = True
        
        # Initialize regex patterns for class handling
        self.class_pattern = re.compile(
            r'class\s+(?P<class_name>\w+)[\s\(].*?(?=\n\s*(?:class|$))', 
            re.DOTALL
        )

    def stop(self):
        """Stop the reverse extraction process gracefully."""
        self._is_running = False

    def load_settings(self) -> Dict[str, Any]:
        """Load TOML settings and normalize paths."""
        try:
            if self.settings_path:
                settings = toml.load(self.settings_path)
                # Ensure we have the required structure
                if not isinstance(settings, dict):
                    settings = {'paths': {'path_style': 'windows'}}
                elif 'paths' not in settings:
                    settings['paths'] = {'path_style': 'windows'}
                elif 'path_style' not in settings['paths']:
                    settings['paths']['path_style'] = 'windows'
                
                self.normalize_paths(settings)
                return settings
            return {'paths': {'path_style': 'windows'}}
        except Exception as e:
            print(f"Error loading settings: {e}")
            return {'paths': {'path_style': 'windows'}}

    def normalize_paths(self, settings_dict: Dict[str, Any]) -> None:
        """Recursively normalize all paths in the loaded settings."""
        for section in settings_dict:
            for key, value in settings_dict[section].items():
                if isinstance(value, str) and ('/' in value or '\\' in value):
                    settings_dict[section][key] = os.path.normpath(value).replace('\\', '/')
                elif isinstance(value, list):
                    settings_dict[section][key] = [
                        os.path.normpath(item).replace('\\', '/') 
                        if isinstance(item, str) and ('/' in item or '\\' in item) else item
                        for item in value
                    ]
                elif isinstance(value, dict):
                    self.normalize_paths(value)

    def format_path(self, relative_path: str) -> str:
        """Format the path based on the selected path style."""
        path = relative_path.replace('\\', '/')
        if self.settings['paths']['path_style'] == 'windows':
            formatted_path = os.path.join('..', path).replace('/', '\\')
        else:
            formatted_path = os.path.join('.', path).replace('\\', '/')
        return formatted_path

    def extract_code_blocks(self, content: str) -> List[CodeBlock]:
        """
        Enhanced extraction of code blocks supporting multiple formats.
        Handles various path locations and formats.
        """
        code_blocks = []
        
        # Define all pattern sets
        header_patterns = [
            (r'^#\s*(?:title\s*=\s*)(.*?\.[\w]+)$', False),
            (r'^#+\s*(?:File|Path|Location|Source|Module Path|Container Path):\s*(.*?\.[\w]+)$', False),
            (r'^#\s*\[(.*?\.[\w]+)\]$', False),
            (r'^#\s*(.*?\.[\w]+)$', False),
        ]
        
        code_comment_patterns = [
            (r'^(?://|#)\s*(.*?\.[\w]+)$', False),
            (r'^(?://|#)\s*\[(.*?\.[\w]+)\]$', False),
            (r'^(?://|#)\s*(?:File|Path|Location|Source):\s*(.*?\.[\w]+)$', False),
        ]
        
        section_patterns = [
            r'^\s*---\s*$',
            r'^\s*\*\*\*\s*$',
            r'^\s*___\s*$',
            r'^#+\s*.*$'
        ]
        
        # Split content into sections using any delimiter
        sections = self._split_into_sections(content, section_patterns)
        
        for section in sections:
            try:
                # Extract path from section header or content
                file_path = None
                code_content = None
                language = None
                
                # Try header patterns first
                for pattern, is_update in header_patterns:
                    matches = re.finditer(pattern, section, re.MULTILINE)
                    for match in matches:
                        file_path = match.group(1)
                        break
                    if file_path:
                        break
                
                # Look for code blocks
                code_block_pattern = r'```(\w+)\n(.*?)```'
                code_matches = list(re.finditer(code_block_pattern, section, re.DOTALL))
                
                if code_matches:
                    for code_match in code_matches:
                        language = code_match.group(1)
                        code_content = code_match.group(2).strip()
                        
                        # If no path found in header, try code comments
                        if not file_path:
                            code_lines = code_content.split('\n')
                            if code_lines:
                                for pattern, is_update in code_comment_patterns:
                                    comment_match = re.match(pattern, code_lines[0])
                                    if comment_match:
                                        file_path = comment_match.group(1)
                                        # Remove the comment line if path was found there
                                        code_content = '\n'.join(code_lines[1:]).strip()
                                        break
                
                if file_path and code_content:
                    normalized_path = self._normalize_path(file_path)
                    code_blocks.append(CodeBlock(
                        path=normalized_path,
                        language=language or self._detect_language(normalized_path),
                        content=code_content,
                        style='windows' if '\\' in file_path else 'unix'
                    ))
                    
            except Exception as e:
                print(f"Error processing section: {str(e)}")
                continue
                
        return code_blocks

    def _split_into_sections(self, content: str, section_patterns: List[str]) -> List[str]:
        """
        Split content into sections based on various delimiter patterns.
        """
        # Combine all patterns into one
        combined_pattern = '|'.join(f'({pattern})' for pattern in section_patterns)
        
        # Split content
        sections = []
        current_section = []
        
        for line in content.split('\n'):
            if any(re.match(pattern, line) for pattern in section_patterns):
                if current_section:
                    sections.append('\n'.join(current_section))
                    current_section = []
            current_section.append(line)
            
        if current_section:
            sections.append('\n'.join(current_section))
            
        return sections if sections else [content]

    def _detect_language(self, file_path: str) -> str:
        """
        Detect programming language from file extension.
        """
        ext_to_language = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.html': 'html',
            '.css': 'css',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.m': 'objective-c',
            '.sh': 'bash',
            '.ps1': 'powershell',
            '.sql': 'sql',
            '.r': 'r',
            '.dart': 'dart',
            '.vue': 'vue',
            '.elm': 'elm',
            '.ex': 'elixir',
            '.erl': 'erlang',
            '.fs': 'fsharp',
            '.hs': 'haskell',
            '.jl': 'julia',
            '.lua': 'lua',
            '.ml': 'ocaml',
            '.pl': 'perl',
            '.rkt': 'racket',
        }
        
        ext = os.path.splitext(file_path)[1].lower()
        return ext_to_language.get(ext, 'text')

    def _normalize_path(self, path: str) -> str:
        """
        Normalize file paths to a consistent format.
        Handles various path formats and styles.
        """
        # Remove brackets, parentheses, etc.
        path = re.sub(r'[\[\]()]', '', path)
        
        # Remove common prefixes
        path = re.sub(r'^(?:file://|path:|source:|location:)\s*', '', path, flags=re.IGNORECASE)
        
        # Normalize separators
        path = path.replace('\\', '/').strip()
        
        # Handle relative paths
        if not path.startswith(('.', '/', '\\')):
            path = './' + path
            
        return path

    def update_class_in_file(self, file_path: str, class_name: str, new_content: str) -> bool:
        """Update a specific class in a file while preserving all other content."""
        try:
            # Read existing file content
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return False

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find the target class using improved pattern
            class_pattern = re.compile(
                f'class\\s+{re.escape(class_name)}\\s*(?:\\([^)]*\\))?\\s*:\\s*[^#]*?(?=\\s*class\\s+|$)',
                re.DOTALL | re.MULTILINE
            )

            match = class_pattern.search(content)
            if not match:
                print(f"Class {class_name} not found in {file_path}")
                return False

            # Get the full match and its position
            start = match.start()
            end = match.end()

            # Print debug info
            print(f"Found class {class_name} at position {start}-{end}")
            print("Original content around match:")
            context_before = content[max(0, start-50):start]
            context_after = content[end:min(len(content), end+50)]
            print(f"Before: {context_before}")
            print(f"After: {context_after}")

            # Construct updated content
            updated = content[:start] + new_content + content[end:]

            # Write the updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated)

            print(f"Successfully updated class {class_name} in {file_path}")
            return True

        except Exception as e:
            print(f"Error updating class {class_name} in {file_path}: {str(e)}")
            return False

    def run(self) -> None:
        """Process the markdown content and create/update files."""
        try:
            print("1. Starting ReverseMarkdownEx.run()")

            if not os.path.exists(self.markdown_path):
                print(f"Error: Markdown file not found at {self.markdown_path}")
                raise FileNotFoundError(f"Markdown file not found: {self.markdown_path}")

            print("2. Loading Markdown file...")
            if self.update_status:
                self.update_status("Loading Markdown file...")

            with open(self.markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"3. Read {len(content)} bytes from file")

            # Extract all code blocks
            print("4. Extracting code blocks...")
            code_blocks = self.extract_code_blocks(content)
            print(f"5. Found {len(code_blocks)} code blocks")
            total_blocks = len(code_blocks)

            if total_blocks == 0:
                print("6. No code blocks found")
                if self.update_status:
                    self.update_status("No valid code blocks found to extract.")
                return

            processed_count = 0
            for idx, block in enumerate(code_blocks, 1):
                if not self._is_running:
                    print("Process stopped by user")
                    if self.update_status:
                        self.update_status("Extraction stopped by user.")
                    return

                try:
                    print(f"7. Processing block {idx}/{total_blocks}: {block.path}")
                    file_path = block.path
                    relative_path = file_path.replace('\\', '/').replace('../', '').replace('./', '')
                    full_path = os.path.join(self.output_dir, relative_path).replace('\\', '/')
                    
                    # Create directory
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    print(f"8. Created directory: {os.path.dirname(full_path)}")

                    if block.update_class:
                        # Handle class update
                        if os.path.exists(full_path):
                            success = self.update_class_in_file(full_path, block.update_class, block.content)
                            if success:
                                processed_count += 1
                    else:
                        # Handle full file creation/update
                        print(f"9. Writing to file: {full_path}")
                        with open(full_path, 'w', encoding='utf-8') as out_file:
                            cleaned_content = block.content.strip()
                            out_file.write(cleaned_content)
                            processed_count += 1
                            print(f"10. Successfully wrote file {processed_count}")

                    if self.update_progress:
                        progress = int(idx * 100 / total_blocks)
                        print(f"11. Progress: {progress}%")
                        self.update_progress(progress)

                except Exception as e:
                    print(f"Error processing file {file_path}: {str(e)}")
                    continue

            print(f"12. Extraction complete. Processed {processed_count} files")
            if self.update_status and self._is_running:
                if processed_count > 0:
                    self.update_status(f"Successfully processed {processed_count} files in: {self.output_dir}")
                else:
                    self.update_status("No files were processed.")

        except Exception as e:
            print(f"Fatal error during extraction: {str(e)}")
            if self.update_status:
                self.update_status(f"Error during extraction: {str(e)}")
            raise


def reverse_markdown_extraction(markdown_path: str, output_dir: str, settings_path: Optional[str] = None) -> None:
    """Convenience function for reversing markdown -> files."""
    extractor = ReverseMarkdownEx(markdown_path, output_dir, settings_path)
    extractor.run()

class ReverseCSVEx:
    def __init__(self, file_path, output_dir):
        self.file_path = file_path
        self.output_dir = os.path.normpath(output_dir).replace('\\', '/')
        self.update_progress = None  # For GUI progress
        self.update_status = None    # For GUI status messages
        self._is_running = True

    def stop(self):
        """Stop the reverse extraction process gracefully."""
        self._is_running = False

    def run(self):
        """Reverse the CSV extraction process by recreating files from an Excel sheet."""
        try:
            if self.update_status:
                self.update_status("Loading Excel file...")

            df = pd.read_excel(self.file_path)
            total_files = len(df)

            if total_files == 0:
                if self.update_status:
                    self.update_status("No records found in the Excel file.")
                return

            for idx, row in df.iterrows():
                if not self._is_running:
                    if self.update_status:
                        self.update_status("Reverse CSV extraction stopped by user.")
                    break

                try:
                    out_path = os.path.join(self.output_dir, row['Path'])
                    os.makedirs(os.path.dirname(out_path), exist_ok=True)

                    with open(out_path, 'w', encoding='utf-8') as f:
                        f.write(row['Code'])

                    if self.update_progress:
                        self.update_progress(int((idx + 1) * 100 / total_files))

                except Exception as e:
                    print(f"Error processing file {row['Path']}: {str(e)}")
                    if self.update_status:
                        self.update_status(f"Error processing {row['Path']}: {str(e)}")
                    continue

            if self.update_status and self._is_running:
                self.update_status(f"Files have been recreated in: {self.output_dir}")

        except Exception as e:
            print(f"Error during reverse CSV extraction: {str(e)}")
            if self.update_status:
                self.update_status(f"Error during reverse CSV extraction: {str(e)}")
            raise


def reverse_csv_extraction(file_path, output_dir):
    """Convenience function for reversing Excel -> files."""
    extractor = ReverseCSVEx(file_path, output_dir)
    extractor.run()




# Generic worker class for extractions
class ExtractorWorker(QObject):
    finished = Signal()
    error = Signal(str)
    progress = Signal(int)
    status = Signal(str)

    def __init__(self, extractor):
        super().__init__()
        self.extractor = extractor
        self._is_running = True

        # Connect extractor's updates to worker signals
        if hasattr(self.extractor, "update_progress"):
            self.extractor.update_progress = self.progress.emit
        if hasattr(self.extractor, "update_status"):
            self.extractor.update_status = self.status.emit

    @Slot()
    def run(self):
        try:
            if self._is_running:
                self.extractor.run()
                self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        """Stop the extraction process."""
        self._is_running = False
        if hasattr(self.extractor, "stop"):
            self.extractor.stop()

# Re-export publicly so the GUI or other code can import from here
__all__ = [
    "MarkdownEx",
    "CSVEx",
    "ReverseMarkdownEx",
    "reverse_markdown_extraction",
    "ReverseCSVEx",
    "reverse_csv_extraction",
    "ExtractorWorker",  # Add ExtractorWorker to exports
]

# ./summerize_extract/Extractorz.py

import os
import re
import pandas as pd
import zipfile
import shutil
import toml
from pathlib import Path

class MarkdownEx:
    def __init__(self, base_dir, output_dir, settings_path):
        self.base_dir = os.path.normpath(base_dir).replace('\\', '/')
        self.output_dir = os.path.normpath(output_dir).replace('\\', '/')
        self.extract_dir = os.path.normpath(os.path.join(base_dir, 'extract')).replace('\\', '/')
        self.settings_path = os.path.normpath(settings_path).replace('\\', '/')
        self.settings = self.load_settings()
        self.update_progress = None  # Will be set by worker
        self.update_status = None    # Will be set by worker
        os.makedirs(self.output_dir, exist_ok=True)

    def load_settings(self):
        try:
            settings = toml.load(self.settings_path)
            self.normalize_paths(settings)
            return settings
        except toml.TomlDecodeError as e:
            print(f"Error loading settings: {e}")
            raise

    def normalize_paths(self, settings_dict):
        for section in settings_dict:
            for key, value in settings_dict[section].items():
                if isinstance(value, str) and ('/' in value or '\\' in value):
                    settings_dict[section][key] = os.path.normpath(value).replace('\\', '/')
                elif isinstance(value, list):
                    settings_dict[section][key] = [os.path.normpath(item).replace('\\', '/') if isinstance(item, str) and ('/' in item or '\\' in item) else item for item in value]
                elif isinstance(value, dict):
                    self.normalize_paths(value) 

    def save_settings(self):
        with open(self.settings_path, 'w') as settings_file:
            toml.dump(self.settings, settings_file)

    def should_skip_directory(self, dir_path):
        for skip_path in self.settings['paths'].get('skip_paths', []):
            if dir_path.startswith(skip_path) or os.path.basename(dir_path) in self.settings['directories']['ignored_directories']:
                return True
        return False

    def get_files_in_directory(self, directory):
        if self.settings['file_specific']['use_file_specific']:
            return [os.path.normpath(os.path.join(directory, file)) for file in self.settings['file_specific']['specific_files']]
        
        file_paths = []
        ignored_extensions = set(self.settings['files']['ignored_extensions'])
        ignored_files = set(self.settings['files']['ignored_files'])

        for root, dirs, files in os.walk(directory):
            if self.should_skip_directory(os.path.relpath(root, directory)):
                dirs[:] = []
                continue

            dirs[:] = [d for d in dirs if d not in self.settings['directories']['ignored_directories']]

            for file in files:
                if file in ignored_files:
                    continue
                if not os.path.splitext(file)[1].lower() in ignored_extensions:
                    file_paths.append(os.path.normpath(os.path.join(root, file)))
        return file_paths

    @staticmethod
    def is_binary_file(file_path):
        try:
            file_path = os.path.normpath(file_path)
            text_characters = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)))
            with open(file_path, 'rb') as file:
                data = file.read(1024)
            return bool(data.translate(None, text_characters))
        except Exception as e:
            print(f"Error checking if file is binary: {str(e)}")
            return True

    def create_table_of_contents(self, file_paths):
        toc = "# Table of Contents\n"
        for file_path in file_paths:
            relative_path = os.path.relpath(file_path, self.extract_dir)
            toc += f"- [{relative_path}](#{relative_path.replace(' ', '-').replace('.', '')})\n"
        return toc

    def create_where_file_lines(self, file_lines_info):
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
            content += f"## File: {file_path}\n"
            content += f"Line = {start_line}, Starts = {start_line + 2}, Ends = {end_line + 1}\n\n"
        
        return content

    def create_markdown_for_files(self, file_paths):
        toc = self.create_table_of_contents(file_paths) + "\n\n"
        markdown_content = "# Project Details\n\n" + toc
        file_lines_info = {}
        line_counter = markdown_content.count('\n') + 1

        total_files = len(file_paths)
        for idx, file_path in enumerate(file_paths, 1):
            if hasattr(self, 'update_status'):
                self.update_status(f"Processing file {idx}/{total_files}: {os.path.basename(file_path)}")

            try:
                file_path = os.path.normpath(file_path)
                relative_path = os.path.relpath(file_path, self.extract_dir)
                description = f"// {relative_path}\n"
                
                if self.is_binary_file(file_path):
                    markdown_content += f"## File: {relative_path}\n\n**Binary file cannot be displayed.**\n\n"
                    line_counter += 3
                else:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                    file_extension = os.path.splitext(file_path)[1].lower().lstrip('.')
                    start_line = line_counter
                    line_counter += content.count('\n') + 5
                    end_line = line_counter - 1
                    file_lines_info[relative_path] = (start_line, end_line)
                    markdown_content += f"## File: {relative_path}\n\n```{file_extension}\n{description}{content}\n```\n\n"

                line_counter += 2

                if hasattr(self, 'update_progress'):
                    self.update_progress(int(idx * 100 / total_files))

            except Exception as e:
                print(f"Error processing file {file_path}: {str(e)}")
                continue

        where_file_lines = self.create_where_file_lines(file_lines_info)
        return markdown_content, where_file_lines

    def save_markdown(self, markdown_content, where_file_lines, output_dir):
        prefix = self.settings['output']['markdown_file_prefix']
        existing_files = [f for f in os.listdir(output_dir) if f.startswith(prefix) and f.endswith('.md')]
        existing_files = [f for f in existing_files if re.match(rf'{prefix}_\d{{2}}\.md', f)]
        
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

        with open(main_output_path, 'w', encoding='utf-8') as file:
            file.write(markdown_content)

        with open(where_file_lines_path, 'w', encoding='utf-8') as file:
            file.write(where_file_lines)

        return main_output_path, where_file_lines_path

    def run(self):
        if not os.path.exists(self.settings_path):
            raise FileNotFoundError(f"Settings file not found: {self.settings_path}")

        output_dir = self.settings['paths']['output_dir']
        presets = self.settings.get('presets', {})
        total_presets = len(presets)

        if total_presets == 0:
            if hasattr(self, 'update_status'):
                self.update_status("No presets found in settings")
            return

        for idx, preset_name in enumerate(presets, 1):
            if hasattr(self, 'update_status'):
                self.update_status(f"Processing preset {idx}/{total_presets}: {preset_name}")

            try:
                preset_output_dir = os.path.normpath(os.path.join(output_dir, preset_name))
                os.makedirs(preset_output_dir, exist_ok=True)

                specific_files = presets[preset_name]
                file_paths = [os.path.normpath(os.path.join(self.base_dir, file)) for file in specific_files]

                if not file_paths:
                    if hasattr(self, 'update_status'):
                        self.update_status(f"No files found for preset: {preset_name}")
                    continue

                markdown_content, where_file_lines = self.create_markdown_for_files(file_paths)
                main_output_path, where_file_lines_path = self.save_markdown(
                    markdown_content, 
                    where_file_lines, 
                    preset_output_dir
                )

                if hasattr(self, 'update_status'):
                    self.update_status(f"Created files:\n{main_output_path}\n{where_file_lines_path}")

                if hasattr(self, 'update_progress'):
                    self.update_progress(int(idx * 100 / total_presets))

            except Exception as e:
                print(f"Error processing preset {preset_name}: {str(e)}")
                if hasattr(self, 'update_status'):
                    self.update_status(f"Error in preset {preset_name}: {str(e)}")
                continue

        if hasattr(self, 'update_status'):
            self.update_status("Markdown extraction complete")

class CSVEx:
    def __init__(self, base_dir, output_dir, settings_path):
        self.base_dir = os.path.normpath(base_dir).replace('\\', '/')
        self.output_dir = os.path.normpath(output_dir).replace('\\', '/')
        self.extracted_dir = os.path.normpath(os.path.join(base_dir, 'extracted')).replace('\\', '/')
        self.settings_path = os.path.normpath(settings_path).replace('\\', '/')
        self.settings = self.load_settings()
        self.update_progress = None  # Will be set by worker
        self.update_status = None    # Will be set by worker
        os.makedirs(self.output_dir, exist_ok=True)

    def load_settings(self):
        try:
            settings = toml.load(self.settings_path)
            self.normalize_paths(settings)
            return settings
        except toml.TomlDecodeError as e:
            print(f"Error loading settings: {e}")
            raise

    def normalize_paths(self, settings_dict):
        for section in settings_dict:
            for key, value in settings_dict[section].items():
                if isinstance(value, str) and ('/' in value or '\\' in value):
                    settings_dict[section][key] = os.path.normpath(value).replace('\\', '/')
                elif isinstance(value, list):
                    settings_dict[section][key] = [os.path.normpath(item).replace('\\', '/') if isinstance(item, str) and ('/' in item or '\\' in item) else item for item in value]
                elif isinstance(value, dict):
                    self.normalize_paths(value) 

    def save_settings(self):
        with open(self.settings_path, 'w') as settings_file:
            toml.dump(self.settings, settings_file)

    @staticmethod
    def extract_zip(zip_path, extract_to):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            total_files = len(zip_ref.filelist)
            for index, member in enumerate(zip_ref.filelist, 1):
                zip_ref.extract(member, extract_to)

    @staticmethod
    def count_file_metrics(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                char_count = len(content)
                word_count = len(content.split())
                line_count = content.count("\n") + 1
            return char_count, word_count, line_count
        except Exception as e:
            print(f"Error counting metrics for {file_path}: {str(e)}")
            return 0, 0, 0

    @staticmethod
    def count_classes_functions_variables(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                class_count = len(re.findall(r'\bclass\b', content))
                function_count = len(re.findall(r'\bdef\b', content))
                variable_count = len(re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\s*=\s*', content))
            return class_count, function_count, variable_count
        except Exception as e:
            print(f"Error counting code elements for {file_path}: {str(e)}")
            return 0, 0, 0

    def should_skip_directory(self, dir_path):
        skip_paths = self.settings['paths'].get('skip_paths', [])
        for skip_path in skip_paths:
            if dir_path.startswith(skip_path) or os.path.basename(dir_path) in self.settings['directories']['ignored_directories']:
                return True
        return False

    def generate_directory_tree_with_detailed_metrics(self):
        if hasattr(self, 'update_status'):
            self.update_status("Gathering file list...")

        if self.settings['file_specific']['use_file_specific']:
            file_paths = [os.path.join(self.base_dir, file) for file in self.settings['file_specific']['specific_files']]
        else:
            file_paths = []
            ignored_extensions = set(self.settings['files']['ignored_extensions'])
            ignored_files = set(self.settings['files']['ignored_files'])

            for root_dir, dirs, files in os.walk(self.base_dir):
                if self.should_skip_directory(os.path.relpath(root_dir, self.base_dir)):
                    dirs[:] = []
                    continue

                dirs[:] = [d for d in dirs if d not in self.settings['directories']['ignored_directories']]

                for file in files:
                    if file in ignored_files:
                        continue
                    file_path = os.path.join(root_dir, file)
                    if os.path.splitext(file)[1].lower() in ignored_extensions:
                        continue
                    file_paths.append(file_path)

        if not file_paths:
            if hasattr(self, 'update_status'):
                self.update_status("No files found to process")
            return []

        directory_tree = []
        total_files = len(file_paths)
        
        for idx, file_path in enumerate(file_paths, 1):
            if hasattr(self, 'update_status'):
                self.update_status(f"Processing file {idx}/{total_files}: {os.path.basename(file_path)}")
            
            try:
                relative_path = os.path.relpath(file_path, self.base_dir)
                size_kb = os.path.getsize(file_path) / 1024
                
                char_count, word_count, line_count = self.count_file_metrics(file_path)
                class_count, function_count, variable_count = self.count_classes_functions_variables(file_path)
                
                metrics = (
                    f"{size_kb:.2f}{self.settings['metrics']['size_unit']},C{char_count},"
                    f"W{word_count},L{line_count},CL{class_count},F{function_count},V{variable_count}"
                )
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()
                
                directory_tree.append([relative_path, metrics, content])
            except Exception as e:
                print(f"Error processing file {file_path}: {str(e)}")
                if hasattr(self, 'update_status'):
                    self.update_status(f"Error processing file: {os.path.basename(file_path)}")
                continue
            
            if hasattr(self, 'update_progress'):
                self.update_progress(int(idx * 100 / total_files))

        return directory_tree

    def get_next_output_file_path(self):
        prefix = self.settings['output']['csv_file_prefix']
        existing_files = [f for f in os.listdir(self.output_dir) if f.startswith(prefix) and f.endswith('.xlsx')]
        
        if not existing_files:
            return os.path.join(self.output_dir, f'{prefix}_00.xlsx')

        existing_files.sort()
        last_file = existing_files[-1]
        last_index = int(last_file.split('_')[-1].split('.')[0])
        next_index = last_index + 1
        next_file_name = f'{prefix}_{next_index:02d}.xlsx'
        return os.path.join(self.output_dir, next_file_name)

    @staticmethod
    def clear_extracted_directory(extracted_dir):
        if not os.path.exists(extracted_dir):
            return
            
        try:
            for root_dir, dirs, files in os.walk(extracted_dir):
                for file in files:
                    os.remove(os.path.join(root_dir, file))
                for dir in dirs:
                    shutil.rmtree(os.path.join(root_dir, dir))
        except Exception as e:
            print(f"Error clearing extracted directory: {str(e)}")

    def save_to_excel(self, data, file_path):
        if not data:
            if hasattr(self, 'update_status'):
                self.update_status("No data to save to Excel")
            return

        try:
            if hasattr(self, 'update_status'):
                self.update_status("Creating Excel workbook...")

            df = pd.DataFrame(data, columns=["Path", "Metrics", "Code"])
            writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name='Sheet1')

            if hasattr(self, 'update_status'):
                self.update_status("Adjusting column widths...")

            worksheet = writer.sheets['Sheet1']
            for idx, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).map(len).max(), len(col))
                worksheet.set_column(idx, idx, max_length)

            writer.close()

            if hasattr(self, 'update_status'):
                self.update_status(f"Excel file saved successfully: {os.path.basename(file_path)}")

        except Exception as e:
            print(f"Error saving Excel file: {str(e)}")
            if hasattr(self, 'update_status'):
                self.update_status(f"Error saving Excel file: {str(e)}")
            raise

    def run(self):
        if not os.path.exists(self.settings_path):
            raise FileNotFoundError(f"Settings file not found: {self.settings_path}")

        try:
            if hasattr(self, 'update_status'):
                self.update_status("Starting extraction process...")

            output_file_path = self.get_next_output_file_path()

            # Handle ZIP files if present
            for file_name in os.listdir(self.base_dir):
                if file_name.endswith('.zip'):
                    if hasattr(self, 'update_status'):
                        self.update_status(f"Extracting ZIP file: {file_name}")
                    zip_path = os.path.join(self.base_dir, file_name)
                    self.extract_zip(zip_path, self.extracted_dir)
                    root_dir = self.extracted_dir
                    break
            else:
                root_dir = self.base_dir

            if hasattr(self, 'update_status'):
                self.update_status("Generating directory tree with metrics...")
            
            directory_tree_with_detailed_metrics = self.generate_directory_tree_with_detailed_metrics()

            if hasattr(self, 'update_status'):
                self.update_status("Saving to Excel file...")
            
            self.save_to_excel(directory_tree_with_detailed_metrics, output_file_path)
            
            if hasattr(self, 'update_status'):
                self.update_status("Cleaning up extracted files...")
            
            self.clear_extracted_directory(self.extracted_dir)

            if hasattr(self, 'update_status'):
                self.update_status(f"Extraction complete. File saved to: {os.path.basename(output_file_path)}")

        except Exception as e:
            error_message = f"Error during extraction: {str(e)}"
            print(error_message)
            if hasattr(self, 'update_status'):
                self.update_status(error_message)
            raise


# Function to handle reverse operations
def reverse_csv_extraction(file_path, output_dir):
    """Reverse the CSV extraction process"""
    try:
        df = pd.read_excel(file_path)
        os.makedirs(output_dir, exist_ok=True)
        
        for _, row in df.iterrows():
            file_path = os.path.join(output_dir, row['Path'])
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(row['Code'])
                
        print(f"Files have been recreated in: {output_dir}")
        
    except Exception as e:
        print(f"Error during reverse CSV extraction: {str(e)}")
        raise

def reverse_markdown_extraction(markdown_path, output_dir):
    """Reverse the Markdown extraction process"""
    try:
        with open(markdown_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        pattern = re.compile(r'## File: (.*?)\n\n```.*?\n(.*?)\n```\n\n', re.DOTALL)
        matches = pattern.findall(content)
        
        os.makedirs(output_dir, exist_ok=True)
        
        for file_path, file_content in matches:
            if "Binary file cannot be displayed." in file_content:
                continue
                
            full_path = os.path.join(output_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Remove the file path comment if present
            file_content = re.sub(r'^// .*?\n', '', file_content, flags=re.MULTILINE)
            
            with open(full_path, 'w', encoding='utf-8') as file:
                file.write(file_content)
                
        print(f"Files have been recreated in: {output_dir}")
        
    except Exception as e:
        print(f"Error during reverse Markdown extraction: {str(e)}")
        raise
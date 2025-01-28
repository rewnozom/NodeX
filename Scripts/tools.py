import os
import sys
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Tuple

###############################################
# Global Configuration and Logging
###############################################

CONFIG = {
    'SHOW_ONLY_DIRECTORIES': True,        # Show only directories when generating directory tree markdown
    'USE_TABS_FOR_INDENTATION': False,    # Use tabs for indentation in generated directory tree markdown
    'EXCLUDE_PATTERNS': ["__pycache__", "node_modules", "env", "_Build_","DynamicPyside6.egg-info", "markdown_tree_generated", "setting",],
    'FILE_EXTENSION': '.py',              # Default file extension filter for certain operations
    'TIMESTAMP_FORMAT': "%Y%m%d_%H%M%S",
    'ENCODING': 'utf-8',
    'SEARCH_DIRECTORY': './llm_util/',    # Default search directory for the import extraction functionality
    'MARKDOWN_STRINGS': [
        """
from ui.main_window import MainWindow
""",
        """
from LLMPathway.src.live.logging_manager.logger import logger, qt_message_handler
""",
        # ... (alla andra markdown-strängar)
    ],
    'MARKDOWN_OUTPUT_PATH': './markdown_tree_generated/generated_tree.md',  # Ny inställning för output path
    'MAX_DEPTH': 5,                      # Ny inställning för max djup
    'LIMIT_DEPTH': True,                 # Ny inställning för att begränsa djupet
}

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

###############################################
# Directory Structure Creation
###############################################
class DirectoryStructureManager:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
        logging.info(f"Base directory set to: {self.base_dir}")

    def parse_line(self, line: str) -> Tuple[int, str, bool]:
        stripped_line = line.lstrip()
        original_line = stripped_line

        indent_level = 0
        while stripped_line.startswith('│   ') or stripped_line.startswith('    '):
            indent_level += 1
            stripped_line = stripped_line[4:]

        if stripped_line.startswith('├── '):
            stripped_line = stripped_line[4:]
        elif stripped_line.startswith('└── '):
            stripped_line = stripped_line[4:]

        is_directory = stripped_line.endswith('/')
        item_name = stripped_line.rstrip('/').strip()

        logging.debug(f"Parsed line '{original_line}': Indent Level={indent_level}, Name='{item_name}', Is Directory={is_directory}")

        return indent_level, item_name, is_directory

    def build_directory_map(self, tree_text: str) -> Dict[str, List[str]]:
        directory_map = {}
        current_path = []
        previous_indent = -1

        for line_number, line in enumerate(tree_text.strip().splitlines(), start=1):
            if not line.strip():
                continue

            indent_level, item_name, is_directory = self.parse_line(line)

            if not item_name:
                continue

            if indent_level > previous_indent:
                # Going deeper
                if indent_level - previous_indent > 1:
                    logging.warning(f"Unexpected indentation at line {line_number}.")
            else:
                # Going back or same level
                while len(current_path) > indent_level:
                    popped = current_path.pop()
                    logging.debug(f"Popped '{popped}' from current path.")

            previous_indent = indent_level

            if is_directory:
                current_path.append(item_name)
                dir_path = '/'.join(current_path)
                directory_map[dir_path] = []
                logging.info(f"Added directory: {dir_path}")
            else:
                dir_path = '/'.join(current_path) if current_path else ''
                if dir_path not in directory_map:
                    directory_map[dir_path] = []
                    logging.debug(f"Created new directory entry in map: {dir_path}")
                directory_map[dir_path].append(item_name)
                logging.info(f"Added file: {os.path.join(dir_path, item_name)}")

        logging.debug(f"Final directory map: {directory_map}")
        return directory_map

    def create_file(self, path: Path, filename: str):
        try:
            file_path = path / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open('w', encoding='utf-8') as f:
                if filename.endswith('.py'):
                    if filename == '__init__.py':
                        f.write('"""Package initialization."""\n')
                    else:
                        module_name = filename[:-3].replace('_', ' ').title().replace(' ', '')
                        f.write(f'"""\n{module_name} module.\n\nAutomatically generated.\n"""\n\n')
                        f.write(f'class {module_name}:\n    pass\n')
                else:
                    f.write('')
            logging.info(f"Created file: {file_path}")
        except Exception as e:
            logging.error(f"Error creating file {filename} in {path}: {e}")

    def create_structure(self, directory_map: Dict[str, List[str]]):
        project_root = self.base_dir

        for directory in sorted(directory_map.keys(), key=lambda x: x.count('/')):
            dir_path = project_root / directory if directory else project_root
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logging.info(f"Created directory: {dir_path}")
            except Exception as e:
                logging.error(f"Error creating directory {dir_path}: {e}")

        for directory, files in directory_map.items():
            dir_path = project_root / directory if directory else project_root
            for file in files:
                self.create_file(dir_path, file)

###############################################
# Directory Tree Markdown Generation
###############################################

def should_exclude_path(name: str, exclude_patterns: List[str]) -> bool:
    return any(pattern in name for pattern in exclude_patterns)

def generate_directory_tree_md(root_dir: str, max_depth: int = None, limit_depth: bool = False):
    exclude_patterns = CONFIG['EXCLUDE_PATTERNS']
    show_only_dirs = CONFIG['SHOW_ONLY_DIRECTORIES']
    use_tabs = CONFIG['USE_TABS_FOR_INDENTATION']

    visited = set()

    root_path = Path(root_dir).resolve()
    root_basename = root_path.name
    tree = f"{root_basename}/\n"

    def add_dir_to_tree(path: Path, prefix: str, tree_lines: List[str], current_depth: int):
        # Respektera LIMIT_DEPTH och MAX_DEPTH
        if limit_depth and max_depth is not None and current_depth > max_depth:
            return

        real_path = path.resolve()
        if real_path in visited:
            logging.debug(f"Skipping already visited directory: {real_path}")
            return
        visited.add(real_path)

        # Hoppa över länkade filer/mappar
        if path.is_symlink():
            logging.debug(f"Skipping symlink: {path}")
            return

        try:
            entries = list(path.iterdir())
        except PermissionError:
            logging.warning(f"Permission denied: {path}")
            return

        # Filtrera bort exkluderade mönster
        entries = [e for e in entries if not should_exclude_path(e.name, exclude_patterns)]

        directories = sorted([e for e in entries if e.is_dir()])
        files = sorted([e for e in entries if e.is_file()])

        if show_only_dirs:
            files = []

        items = directories + files
        item_count = len(items)

        for idx, item in enumerate(items):
            is_last = (idx == item_count - 1)
            if use_tabs:
                # Endast tab-indentering
                indent = "\t" * current_depth
                if item.is_dir():
                    tree_lines.append(f"{indent}{item.name}/")
                    add_dir_to_tree(item, prefix, tree_lines, current_depth + 1)
                else:
                    tree_lines.append(f"{indent}{item.name}")
            else:
                connector = "└── " if is_last else "├── "
                line = f"{prefix}{connector}{item.name}{'/' if item.is_dir() else ''}"
                tree_lines.append(line)
                if item.is_dir():
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    add_dir_to_tree(item, new_prefix, tree_lines, current_depth + 1)

    tree_lines = []
    add_dir_to_tree(root_path, "", tree_lines, 1)
    tree += "\n".join(tree_lines)
    tree += "\n"

    return tree

def save_markdown_tree(md_tree: str, output_path: str):
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open('w', encoding=CONFIG['ENCODING']) as f:
            f.write(md_tree)
        logging.info(f"Markdown-trädet har sparats till: {output_path}")
    except Exception as e:
        logging.error(f"Fel vid sparande av Markdown-trädet till {output_path}: {e}")

###############################################
# Extract and Rewrite Imports
###############################################
def normalize_whitespace(s):
    return ' '.join(s.split())

def check_file_contents(file_path, search_string, use_normalized=False):
    try:
        with open(file_path, 'r', encoding=CONFIG['ENCODING']) as file:
            content = file.read()
            if use_normalized:
                normalized_content = normalize_whitespace(content)
                normalized_search = normalize_whitespace(search_string)
                return normalized_search in normalized_content
            else:
                return search_string.strip() in content
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return False

def find_matching_modules(directory, search_strings, use_normalized=False):
    matching_files_dict = {index: [] for index in range(len(search_strings))}

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(CONFIG['FILE_EXTENSION']):
                file_path = os.path.join(root, file)
                for idx, search_string in enumerate(search_strings):
                    if check_file_contents(file_path, search_string, use_normalized):
                        matching_files_dict[idx].append(file_path)

    matching_files_dict = {k: v for k, v in matching_files_dict.items() if v}
    return matching_files_dict

def extract_specific_imports(file_path, search_string, use_normalized=False):
    try:
        with open(file_path, 'r', encoding=CONFIG['ENCODING']) as file:
            content = file.read()
            if use_normalized:
                normalized_content = normalize_whitespace(content)
                normalized_search = normalize_whitespace(search_string)
                if normalized_search not in normalized_content:
                    return None
                original_import = search_string.strip()
            else:
                if search_string.strip() not in content:
                    return None
                original_import = search_string.strip()

            lines = original_import.splitlines()
            import_line = lines[0]
            if 'import (' in original_import:
                # Multi-line import
                imported_items = ''.join(lines[1:]).strip().rstrip(')')
            else:
                # Single-line import
                imported_items = import_line.split('import', 1)[1].strip()

            relative_path = os.path.relpath(file_path, os.getcwd())
            module_path = os.path.splitext(relative_path)[0].replace(os.sep, '.')
            rewritten_import = f"from {module_path} import (\n    {imported_items}\n)"
            return rewritten_import
    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")
        return None

def save_results_separately(matching_files_dict, search_strings, use_normalized=False):
    timestamp = datetime.datetime.now().strftime(CONFIG['TIMESTAMP_FORMAT'])
    result_dir = os.path.join(os.getcwd(), 'llm_util', f'_new_{timestamp}_')
    os.makedirs(result_dir, exist_ok=True)

    for idx, files in matching_files_dict.items():
        search_string = search_strings[idx]
        output_filename = f"extracted_imports_{idx+1}.md"
        result_file = os.path.join(result_dir, output_filename)

        with open(result_file, 'w', encoding=CONFIG['ENCODING']) as f:
            f.write(f"# Extracted Specific Imports for Search String #{idx + 1}\n\n")
            f.write(f"## Search String:\n```python\n{search_string.strip()}\n```\n\n")
            for file_path in files:
                f.write(f"### {os.path.basename(file_path)}\n\n")
                rewritten_import = extract_specific_imports(file_path, search_string, use_normalized)
                if rewritten_import:
                    f.write("**Rewritten Import Statement:**\n")
                    f.write(f"```python\n{rewritten_import}\n```\n\n")
                else:
                    f.write("No matching import found.\n\n")
                f.write("---\n\n")

        logging.info(f"Results for Search String #{idx + 1} saved to: {result_file}")

def run_import_extraction():
    directory = CONFIG['SEARCH_DIRECTORY']
    search_strings = CONFIG['MARKDOWN_STRINGS']
    use_normalized = False

    if not os.path.isdir(directory):
        logging.error(f"Invalid directory path: {directory}")
        return

    matching_files_dict = find_matching_modules(directory, search_strings, use_normalized)

    if matching_files_dict:
        total_matches = sum(len(files) for files in matching_files_dict.values())
        logging.info(f"Found {total_matches} matching instances across {len(matching_files_dict)} search strings.")
        save_results_separately(matching_files_dict, search_strings, use_normalized)
    else:
        logging.info("No matching files found.")

###############################################
# Remove __pycache__ Directories
###############################################
def remove_pycache_directories(start_path="."):
    removed_count = 0
    for root, dirs, files in os.walk(start_path):
        for d in dirs:
            if d == "__pycache__":
                full_path = os.path.join(root, d)
                try:
                    for subroot, subdirs, subfiles in os.walk(full_path, topdown=False):
                        for sf in subfiles:
                            os.remove(os.path.join(subroot, sf))
                        for sd in subdirs:
                            os.rmdir(os.path.join(subroot, sd))
                    os.rmdir(full_path)
                    logging.info(f"Removed: {full_path}")
                    removed_count += 1
                except Exception as e:
                    logging.error(f"Could not remove {full_path}: {e}")
    if removed_count == 0:
        logging.info("No __pycache__ directories found.")
    else:
        logging.info("Done! All __pycache__ directories have been removed.")

###############################################
# User Interaction (Menu)
###############################################
def create_directory_structure():
    tree_structure = """
├── applications/
│   ├── dynamic-main/
│   │   ├── archive/
│   │   ├── current/
│   │   └── docs/
│
├── tools/
│   ├── scripts/
│   └── utilities/
│
└── workspace/
    ├── experiments/
    ├── prototypes/
    └── temp/
"""
    base_dir = "./"
    manager = DirectoryStructureManager(base_dir)
    directory_map = manager.build_directory_map(tree_structure)
    manager.create_structure(directory_map)
    logging.info("Directory structure created successfully!")

def generate_directory_tree():
    root_dir = input("Ange rotkatalog för trädgenerering (standard '.'): ") or "."
    md_tree = generate_directory_tree_md(
        root_dir,
        max_depth=CONFIG['MAX_DEPTH'] if CONFIG['LIMIT_DEPTH'] else None,
        limit_depth=CONFIG['LIMIT_DEPTH']
    )
    print("Genererad Mappstruktur:\n")
    print(md_tree)

    output_path = CONFIG['MARKDOWN_OUTPUT_PATH']
    save_markdown_tree(md_tree, output_path)

def change_settings():
    while True:
        print("\n\n========== Aktuella Inställningar ==========")
        for k, v in CONFIG.items():
            print(f"{k}: {v}")
        print("\n1) Växla SHOW_ONLY_DIRECTORIES")
        print("2) Växla USE_TABS_FOR_INDENTATION")
        print("3) Lägg till/ta bort EXCLUDE_PATTERNS")
        print("4) Ändra SEARCH_DIRECTORY")
        print("5) Ändra MARKDOWN_OUTPUT_PATH")
        print("6) Ändra LIMIT_DEPTH")
        print("7) Ändra MAX_DEPTH")
        print("8) Återgå till huvudmenyn")

        choice = input("Välj ett alternativ: ")
        if choice == '1':
            CONFIG['SHOW_ONLY_DIRECTORIES'] = not CONFIG['SHOW_ONLY_DIRECTORIES']
            print(f"SHOW_ONLY_DIRECTORIES satt till {CONFIG['SHOW_ONLY_DIRECTORIES']}")
        elif choice == '2':
            CONFIG['USE_TABS_FOR_INDENTATION'] = not CONFIG['USE_TABS_FOR_INDENTATION']
            print(f"USE_TABS_FOR_INDENTATION satt till {CONFIG['USE_TABS_FOR_INDENTATION']}")
        elif choice == '3':
            print("Aktuella exkluderingsmönster:", CONFIG['EXCLUDE_PATTERNS'])
            print("1) Lägg till ett mönster")
            print("2) Ta bort ett mönster")
            print("3) Avbryt")
            sub_choice = input("Välj ett alternativ: ")
            if sub_choice == '1':
                p = input("Ange mönster att lägga till: ")
                if p and p not in CONFIG['EXCLUDE_PATTERNS']:
                    CONFIG['EXCLUDE_PATTERNS'].append(p)
                    print("Mönster tillagt.")
            elif sub_choice == '2':
                p = input("Ange mönster att ta bort: ")
                if p in CONFIG['EXCLUDE_PATTERNS']:
                    CONFIG['EXCLUDE_PATTERNS'].remove(p)
                    print("Mönster borttaget.")
            elif sub_choice == '3':
                continue
            else:
                print("Ogiltigt val.")
        elif choice == '4':
            ndir = input("Ange ny SEARCH_DIRECTORY: ")
            if ndir:
                CONFIG['SEARCH_DIRECTORY'] = ndir
                print(f"SEARCH_DIRECTORY satt till {ndir}")
        elif choice == '5':
            new_path = input("Ange ny MARKDOWN_OUTPUT_PATH (t.ex. './markdown_tree_generated/generated_tree.md'): ")
            if new_path:
                CONFIG['MARKDOWN_OUTPUT_PATH'] = new_path
                print(f"MARKDOWN_OUTPUT_PATH satt till {new_path}")
        elif choice == '6':
            CONFIG['LIMIT_DEPTH'] = not CONFIG['LIMIT_DEPTH']
            print(f"LIMIT_DEPTH satt till {CONFIG['LIMIT_DEPTH']}")
        elif choice == '7':
            if CONFIG['LIMIT_DEPTH']:
                try:
                    new_depth = int(input("Ange nytt MAX_DEPTH (heltal): "))
                    if new_depth >= 0:
                        CONFIG['MAX_DEPTH'] = new_depth
                        print(f"MAX_DEPTH satt till {new_depth}")
                    else:
                        print("MAX_DEPTH måste vara ett positivt heltal.")
                except ValueError:
                    print("Ogiltigt värde. Ange ett heltal.")
            else:
                print("LIMIT_DEPTH är inaktiverat. Aktivera först LIMIT_DEPTH för att ändra MAX_DEPTH.")
        elif choice == '8':
            break
        else:
            print("Ogiltigt val, försök igen.")

def main_menu():
    while True:
        print("\n========== Verktygsmeny ==========")
        print("1) Skapa Mappstruktur (från fördefinierat träd)")
        print("2) Generera Mappstruktur Markdown")
        print("3) Extrahera och Omskriv Imports")
        print("4) Ta bort __pycache__ Mappar")
        print("5) Inställningar")
        print("6) Avsluta")

        choice = input("Välj ett alternativ: ")
        if choice == '1':
            create_directory_structure()
        elif choice == '2':
            generate_directory_tree()
        elif choice == '3':
            run_import_extraction()
        elif choice == '4':
            remove_pycache_directories(".")
        elif choice == '5':
            change_settings()
        elif choice == '6':
            print("Avslutar...")
            break
        else:
            print("Ogiltigt val, försök igen.")

if __name__ == '__main__':
    main_menu()

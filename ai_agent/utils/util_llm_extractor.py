# ./version/shared/utils/util_llm_extractor.py


import os

import markdown
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout, QLineEdit, QTabWidget, QFileDialog, QCheckBox, QListWidget, QListWidgetItem, QScrollArea

from log.logger import logger
from Styles.theme_manager import ThemeManager


class LLMExtractorUtils:
    def __init__(self, config, controller):
        """
        Initializes the utility class with configuration and backend controller.

        Args:
            config (dict): Configuration dictionary.
            controller (Controller): Backend controller instance.
        """
        self.config = config
        self.backend_controller = controller

    def apply_current_theme(self, main_window):
        """
        Apply the current theme to the application.

        Args:
            main_window (QWidget): The main window of the application.
        """
        theme = self.config.get('theme', 'Light')
        ThemeManager.apply_theme(theme)
        ThemeManager.apply_widget_theme(main_window, theme)
        logger.info(f"Theme '{theme}' applied to the application.")

    def init_sidebar(self, side: str, parent: QWidget) -> QWidget:
        """
        Initialize a sidebar (left or right) with controls.

        Args:
            side (str): 'left' or 'right' to determine sidebar position.
            parent (QWidget): The parent widget for the sidebar.

        Returns:
            QWidget: The initialized sidebar widget.
        """
        sidebar = QWidget(parent)
        sidebar.setObjectName(f"{side}_sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        if side == 'left':
            # Configuration Settings (for both desktop and phone settings tab)
            config_label = QLabel("Configuration Settings")
            config_label.setObjectName("config_label")
            config_label.setStyleSheet("font-weight: bold; font-size: 18px;")
            layout.addWidget(config_label)

            # Input File Selection
            input_file_label = QLabel("LLM Output File:")
            input_file_label.setStyleSheet("font-size: 16px;")
            self.input_file_lineedit = QLineEdit()
            self.input_file_lineedit.setPlaceholderText("Select LLM output file...")
            browse_input_file_button = QPushButton("Browse")
            browse_input_file_button.clicked.connect(parent.browse_input_file)
            input_file_layout = QHBoxLayout()
            input_file_layout.addWidget(self.input_file_lineedit)
            input_file_layout.addWidget(browse_input_file_button)
            layout.addWidget(input_file_label)
            layout.addLayout(input_file_layout)

            # Output Directory Selection
            output_dir_label = QLabel("Output Directory:")
            output_dir_label.setStyleSheet("font-size: 16px;")
            self.output_dir_lineedit = QLineEdit()
            self.output_dir_lineedit.setPlaceholderText("Select output directory...")
            browse_output_dir_button = QPushButton("Browse")
            browse_output_dir_button.clicked.connect(parent.browse_output_directory)
            output_dir_layout = QHBoxLayout()
            output_dir_layout.addWidget(self.output_dir_lineedit)
            output_dir_layout.addWidget(browse_output_dir_button)
            layout.addWidget(output_dir_label)
            layout.addLayout(output_dir_layout)

            # Enable Backup Checkbox
            self.enable_backup_checkbox = QCheckBox("Enable Backup")
            self.enable_backup_checkbox.setChecked(self.config.get('enable_backup', True))
            layout.addWidget(self.enable_backup_checkbox)

            # Strict Parsing Checkbox
            self.strict_parsing_checkbox = QCheckBox("Strict Parsing")
            self.strict_parsing_checkbox.setChecked(self.config.get('strict_parsing', True))
            layout.addWidget(self.strict_parsing_checkbox)

        elif side == 'right':
            # Code Blocks List
            code_blocks_label = QLabel("Extracted Code Blocks")
            code_blocks_label.setObjectName("code_blocks_label")
            code_blocks_label.setStyleSheet("font-weight: bold; font-size: 18px;")
            layout.addWidget(code_blocks_label)

            self.code_blocks_list = QListWidget()
            self.code_blocks_list.setSelectionMode(QListWidget.MultiSelection)
            self.code_blocks_list.setToolTip("Select code blocks to process.")
            layout.addWidget(self.code_blocks_list)

        return sidebar

    def init_main_content_tab(self, parent):
        """
        Initialize the main content area for phone layout.

        Args:
            parent (QWidget): Parent widget of the main content tab.
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        main_content = QWidget()
        layout = QVBoxLayout(main_content)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Diff Viewer
        parent.diff_viewer_label = QLabel("Diff Viewer")
        layout.addWidget(parent.diff_viewer_label)

        parent.diff_viewer = QTabWidget()
        parent.diff_viewer.setTabsClosable(True)
        parent.diff_viewer.tabCloseRequested.connect(parent.close_diff_tab)
        layout.addWidget(parent.diff_viewer)

        # Logs Display
        parent.logs_display_label = QLabel("Logs")
        layout.addWidget(parent.logs_display_label)

        parent.logs_display = QTextEdit()
        parent.logs_display.setReadOnly(True)
        layout.addWidget(parent.logs_display)

        scroll.setWidget(main_content)
        parent.main_content_tab.setLayout(QVBoxLayout())
        parent.main_content_tab.layout().addWidget(scroll)

    def init_code_blocks_tab(self, parent):
        """
        Initialize the code blocks area for phone layout.

        Args:
            parent (QWidget): Parent widget of the code blocks tab.
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        code_blocks_content = QWidget()
        layout = QVBoxLayout(code_blocks_content)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Code Blocks List
        parent.code_blocks_list = QListWidget()
        layout.addWidget(parent.code_blocks_list)

        # Run Button
        parent.run_process_button = QPushButton("Run")
        parent.run_process_button.clicked.connect(parent.run_process)
        layout.addWidget(parent.run_process_button)

        scroll.setWidget(code_blocks_content)
        parent.code_blocks_tab.setLayout(QVBoxLayout())
        parent.code_blocks_tab.layout().addWidget(scroll)

    def init_system_prompt_tab(self, parent):
        """
        Initialize the system prompt area for phone layout.

        Args:
            parent (QWidget): Parent widget of the system prompt tab.
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        system_prompt_content = QWidget()
        layout = QVBoxLayout(system_prompt_content)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # System Prompt Display
        parent.system_prompt_display = QTextEdit()
        parent.system_prompt_display.setReadOnly(True)
        layout.addWidget(parent.system_prompt_display)

        scroll.setWidget(system_prompt_content)
        parent.system_prompt_tab.setLayout(QVBoxLayout())
        parent.system_prompt_tab.layout().addWidget(scroll)






    # File Browsing Utilities
    def browse_input_file(self, parent_widget):
        """
        Open a dialog to browse for the LLM output file.

        Args:
            parent_widget (QWidget): The parent widget for the dialog.

        Returns:
            str: The selected file path or an empty string if canceled.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            parent_widget,
            "Select LLM Output File",
            "",
            "Markdown Files (*.md);;All Files (*)"
        )
        if file_path:
            self.config['input_file'] = file_path
            logger.debug(f"Selected input file: {file_path}")
            return file_path
        return ""

    def browse_output_directory(self, parent_widget):
        """
        Open a dialog to browse for the output directory.

        Args:
            parent_widget (QWidget): The parent widget for the dialog.

        Returns:
            str: The selected directory path or an empty string if canceled.
        """
        directory = QFileDialog.getExistingDirectory(
            parent_widget,
            "Select Output Directory"
        )
        if directory:
            self.config['output_directory'] = directory
            logger.debug(f"Selected output directory: {directory}")
            return directory
        return ""

    # Code Blocks Loading and Population

    def load_code_blocks(self, input_file):
        """
        Load code blocks from the LLM output file.

        Args:
            input_file (str): Path to the LLM output file.

        Returns:
            list: List of extracted code blocks.
        """
        if not os.path.isfile(input_file):
            logger.warning("Input file does not exist.")
            return []

        self.backend_controller.extractor.input_file = input_file
        code_blocks = self.backend_controller.extractor.get_code_blocks()
        logger.info(f"Extracted {len(code_blocks)} code blocks from {input_file}.")
        return code_blocks

    def extract_code_blocks_from_text(self, text):
        """
        Extract code blocks from the given text.

        Args:
            text (str): Text containing LLM output.

        Returns:
            list: List of extracted code blocks.
        """
        code_blocks = self.backend_controller.extractor.extract_code_blocks(text)
        logger.info(f"Extracted {len(code_blocks)} code blocks from pasted text.")
        return code_blocks

    def populate_code_blocks_list(self, code_blocks_list, code_blocks):
        """
        Populate the code blocks list widget with extracted code blocks.

        Args:
            code_blocks_list (QListWidget): The QListWidget to populate.
            code_blocks (list): List of code block dictionaries.
        """
        code_blocks_list.clear()

        for block in code_blocks:
            action = block.get('action', 'update')
            if action == 'update':
                module_path = block.get('module_path', 'Unknown Module')
                class_name = block.get('class_name', '')
                method_name = block.get('method_name', '')
                # Build a descriptive item text
                item_text = f"[Update] {module_path}"
                if class_name:
                    item_text += f" | Class: {class_name}"
                if method_name:
                    item_text += f" | Method: {method_name}"
            elif action == 'remove':
                removal_instructions = block.get('removal_instructions', {})
                module_path = removal_instructions.get('module_path', 'Unknown Module')
                targets = removal_instructions.get('targets', [])
                target_descriptions = ', '.join([
                    f"{t.get('type', 'unknown')} {t.get('name', '')}" for t in targets
                ])
                item_text = f"[Remove] {module_path} | Targets: {target_descriptions}"
            else:
                item_text = f"[Unknown Action]"

            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, block)
            code_blocks_list.addItem(item)

        logger.info(f"Populated code blocks list with {len(code_blocks)} items.")

    def populate_phone_code_blocks_list(self, code_blocks_list, code_blocks):
        """
        Populate the code blocks list widget in phone layout with extracted code blocks.

        Args:
            code_blocks_list (QListWidget): The QListWidget to populate.
            code_blocks (list): List of code block dictionaries.
        """
        self.populate_code_blocks_list(code_blocks_list, code_blocks)
        logger.info(f"Populated phone code blocks list with {len(code_blocks)} items.")

    # Code Block Processing

    def process_code_block(self, block, diff_callback=None):
        """
        Process a single code block using the backend controller.

        Args:
            block (dict): The code block dictionary.
            diff_callback (function, optional): Callback function to handle diffs.

        Returns:
            bool: True if processing was successful, False otherwise.
        """
        action = block.get('action', 'update')

        try:
            if action == 'update':
                result = self.backend_controller.process_code_block(
                    block,
                    return_diff=True,
                    diff_callback=diff_callback
                )
            elif action == 'remove':
                result = self.backend_controller.process_removal_block(
                    block,
                    return_diff=True,
                    diff_callback=diff_callback
                )
            else:
                logger.warning(f"Unknown action '{action}' for code block.")
                return False

            if isinstance(result, tuple):
                success, _ = result
            else:
                success = result

            module_path = block.get('module_path') or block.get('removal_instructions', {}).get('module_path', 'Unknown Module')
            if success:
                logger.info(f"Successfully processed {action} for module: {module_path}")
            else:
                logger.error(f"Failed to process {action} for module: {module_path}")

            return success

        except Exception as e:
            logger.error(f"Exception while processing code block: {e}")
            return False

    def process_pasted_llm_output(self, text, auto_run=False):
        """
        Process the LLM output pasted into the text edit.

        Args:
            text (str): The pasted LLM output.
            auto_run (bool): Whether to automatically run processing on extracted code blocks.

        Returns:
            list: List of extracted code blocks.
        """
        if not text:
            logger.warning("No text provided for processing.")
            return []

        code_blocks = self.extract_code_blocks_from_text(text)
        if not code_blocks:
            logger.warning("No valid code blocks found in the input.")
            return []

        logger.info(f"Processing {'all' if auto_run else 'selected'} {len(code_blocks)} code blocks.")
        if auto_run:
            for block in code_blocks:
                self.process_code_block(block)

        return code_blocks

    def run_all_code_blocks(self, code_blocks):
        """
        Automatically process all extracted code blocks.

        Args:
            code_blocks (list): List of code block dictionaries.
        """
        logger.info(f"Running all {len(code_blocks)} code blocks.")
        for block in code_blocks:
            self.process_code_block(block)

    # Diff Display

    def display_diff(self, diff_viewer, module_path, diff_text):
        """
        Display the diff in the diff viewer.

        Args:
            diff_viewer (QTabWidget): The tab widget to display diffs.
            module_path (str): The path of the module.
            diff_text (str): The diff text to display.
        """
        if not diff_viewer:
            logger.warning("Diff viewer widget is not provided.")
            return

        diff_widget = QTextEdit()
        diff_widget.setReadOnly(True)
        diff_widget.setPlainText(diff_text)
        diff_widget.setStyleSheet("font-size: 16px;")

        tab_index = diff_viewer.addTab(diff_widget, os.path.basename(module_path))
        diff_viewer.setCurrentIndex(tab_index)
        logger.info(f"Displayed diff for module: {module_path}")

    # System Prompt Management

    def load_all_system_prompts(self, system_prompt_dir='./System_Prompts/'):
        """
        Load all available system prompts from the specified directory.

        Args:
            system_prompt_dir (str, optional): Directory containing system prompt files.

        Returns:
            dict: Dictionary mapping prompt names to their content.
        """
        system_prompts = {}
        if not os.path.exists(system_prompt_dir):
            logger.warning(f"System prompts directory not found: {system_prompt_dir}")
            return system_prompts

        for filename in os.listdir(system_prompt_dir):
            if filename.endswith(('.md', '.txt')):
                file_path = os.path.join(system_prompt_dir, filename)
                prompt_name = os.path.splitext(filename)[0]
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    system_prompts[prompt_name] = content
                    logger.info(f"Loaded system prompt: {prompt_name}")
                except Exception as e:
                    logger.error(f"Failed to load system prompt '{filename}': {e}")

        if not system_prompts:
            logger.warning("No system prompts found in the directory.")

        return system_prompts

    def update_system_prompt_display(self, prompt_name, system_prompts, system_prompt_display):
        """
        Update the system prompt display based on the selected prompt.

        Args:
            prompt_name (str): The name of the selected system prompt.
            system_prompts (dict): Dictionary of system prompts.
            system_prompt_display (QTextEdit): The QTextEdit widget to display the prompt.
        """
        content = system_prompts.get(prompt_name, "")
        if not content:
            system_prompt_display.setPlainText("Selected prompt not found.")
            logger.warning(f"System prompt '{prompt_name}' not found.")
            return

        if prompt_name.endswith('.md'):
            html_content = markdown.markdown(content)
            system_prompt_display.setHtml(html_content)
            logger.info(f"Displayed markdown system prompt: {prompt_name}")
        else:
            system_prompt_display.setPlainText(content)
            logger.info(f"Displayed plain text system prompt: {prompt_name}")

    # Settings Management

    def load_settings(self, config, ui_elements):
        """
        Load settings from the backend and update the UI accordingly.

        Args:
            config (dict): Configuration dictionary.
            ui_elements (dict): Dictionary of UI elements to update.
        """
        ui_elements['input_file_lineedit'].setText(config.get('input_file', ''))
        ui_elements['output_dir_lineedit'].setText(config.get('output_directory', ''))

        ui_elements['enable_backup_checkbox'].setChecked(config.get('enable_backup', True))
        ui_elements['strict_parsing_checkbox'].setChecked(config.get('strict_parsing', True))
        ui_elements['create_missing_modules_checkbox'].setChecked(config.get('create_missing_modules', True))
        ui_elements['logging_level_combobox'].setCurrentText(config.get('logging_level', 'DEBUG'))
        ui_elements['theme_combobox'].setCurrentText(config.get('theme', 'Light'))
        ui_elements['debug_workflow_checkbox'].setChecked(config.get('DEBUG_WORKFLOW', False))
        ui_elements['preserve_formatting_checkbox'].setChecked(config.get('preserve_formatting', True))
        ui_elements['auto_run_checkbox'].setChecked(config.get('auto_run', True))

        logger.info("Settings loaded and UI updated accordingly.")

    def save_settings(self, config, ui_elements, logger_instance, theme_manager):
        """
        Save settings from the UI to the backend configuration.

        Args:
            config (dict): Configuration dictionary to update.
            ui_elements (dict): Dictionary of UI elements to read from.
            logger_instance (Logger): Logger instance to update log level.
            theme_manager (ThemeManager): Theme manager instance to apply themes.
        """
        config['input_file'] = ui_elements['input_file_lineedit'].text().strip()
        config['output_directory'] = ui_elements['output_dir_lineedit'].text().strip()
        config['enable_backup'] = ui_elements['enable_backup_checkbox'].isChecked()
        config['strict_parsing'] = ui_elements['strict_parsing_checkbox'].isChecked()
        config['create_missing_modules'] = ui_elements['create_missing_modules_checkbox'].isChecked()
        config['logging_level'] = ui_elements['logging_level_combobox'].currentText()
        config['theme'] = ui_elements['theme_combobox'].currentText()
        config['DEBUG_WORKFLOW'] = ui_elements['debug_workflow_checkbox'].isChecked()
        config['preserve_formatting'] = ui_elements['preserve_formatting_checkbox'].isChecked()
        config['auto_run'] = ui_elements['auto_run_checkbox'].isChecked()

        # Update logger level
        logger_instance.setLevel(config['logging_level'])
        logger.info(f"Logging level set to {config['logging_level']}")

        # Apply theme
        theme_manager.apply_theme(config['theme'])
        theme_manager.apply_widget_theme(ui_elements['main_window'], config['theme'])
        logger.info(f"Theme '{config['theme']}' applied to the application.")

        logger.info("Settings saved successfully.")

    # Toggle Settings

    def toggle_setting(self, config, setting_key, state):
        """
        Generic method to toggle a boolean setting.

        Args:
            config (dict): Configuration dictionary.
            setting_key (str): The key of the setting to toggle.
            state (int): The state of the checkbox (Qt.Checked or Qt.Unchecked).
        """
        config[setting_key] = state == Qt.Checked
        logger.info(f"Setting '{setting_key}' toggled to {config[setting_key]}.")

    # Theme and Logging Level

    def change_theme(self, config, new_theme, theme_manager):
        """
        Change the application theme.

        Args:
            config (dict): Configuration dictionary.
            new_theme (str): The new theme to apply.
            theme_manager (ThemeManager): Theme manager instance to apply themes.
        """
        config['theme'] = new_theme
        theme_manager.apply_theme(new_theme)
        theme_manager.apply_widget_theme(None, new_theme)  # Assuming 'None' applies to all widgets
        logger.info(f"Theme changed to {new_theme}.")

    def change_logging_level(self, config, new_level, logger_instance):
        """
        Change the logging level.

        Args:
            config (dict): Configuration dictionary.
            new_level (str): The new logging level.
            logger_instance (Logger): Logger instance to update.
        """
        config['logging_level'] = new_level
        logger_instance.setLevel(new_level)
        logger.info(f"Logging level changed to {new_level}.")

    # System Prompt Management

    def copy_system_prompt(self, system_prompt_display):
        """
        Copy the system prompt content to the clipboard.

        Args:
            system_prompt_display (QTextEdit): The QTextEdit widget containing the system prompt.
        """
        clipboard = system_prompt_display.clipboard()
        clipboard.setText(system_prompt_display.toPlainText())
        logger.info("System prompt copied to clipboard.")

    # Cleanup

    def close_event_cleanup(self, backend_controller):
        """
        Handle application exit to ensure proper cleanup.

        Args:
            backend_controller (Controller): Backend controller instance.
        """
        backend_controller.logger.close_handlers()
        logger.info("Application is closing. Cleaned up backend resources.")


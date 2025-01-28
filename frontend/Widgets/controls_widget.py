from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox, QSlider, QDoubleSpinBox, QSpinBox, QCheckBox, QVBoxLayout
from PySide6.QtCore import Qt
from ai_agent.chat_manager.chat_manager import load_all_system_prompts

class ControlsWidget(QWidget):
    def __init__(self, parent=None, models=None, config=None, icons=None):
        super().__init__(parent)
        self.models = models
        self.config = config
        self.icons = icons

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(15)

        # Model Selection
        model_label = QLabel("Model:")
        model_label.setToolTip("Select the AI model to use")
        model_label.setObjectName("modelLabel")  # For theming
        self.model_combobox = QComboBox()
        available_models = [model_name for company_models in self.models.values() for model_name in company_models.keys()]
        self.model_combobox.addItems(available_models)
        self.model_combobox.setCurrentText(self.config.CHAT_MODEL)
        self.model_combobox.setMinimumWidth(150)
        self.model_combobox.setObjectName("modelComboBox")  # For theming
        layout.addWidget(model_label)
        layout.addWidget(self.model_combobox)

        # System Prompt Label and ComboBox
        system_prompt_label = QLabel("System Prompt:")
        system_prompt_label.setToolTip("Select the system prompt for the AI")
        system_prompt_label.setObjectName("systemPromptLabel")  # For theming
        self.system_prompt_combobox = QComboBox()
        self.system_prompt_combobox.setObjectName("systemPromptComboBox")  # For theming
        system_prompts = load_all_system_prompts()
        self.system_prompt_combobox.addItems(system_prompts)
        self.system_prompt_combobox.setMinimumWidth(150)
        layout.addWidget(system_prompt_label)
        layout.addWidget(self.system_prompt_combobox)

        # Temperature Label and Controls
        temperature_label = QLabel("Temp.:")
        temperature_label.setToolTip("Controls the randomness of the AI's output")
        temperature_label.setObjectName("temperatureLabel")  # For theming

        self.temperature_slider = QSlider(Qt.Horizontal)
        self.temperature_slider.setRange(0, 200)
        self.temperature_slider.setValue(int(self.config.CHAT_TEMPERATURE * 100))
        self.temperature_slider.setTickInterval(10)
        self.temperature_slider.setTickPosition(QSlider.TicksBelow)
        self.temperature_slider.setObjectName("temperatureSlider")  # For theming

        self.temperature_spinbox = QDoubleSpinBox()
        self.temperature_spinbox.setRange(0.0, 2.0)
        self.temperature_spinbox.setSingleStep(0.01)
        self.temperature_spinbox.setDecimals(2)
        self.temperature_spinbox.setValue(self.config.CHAT_TEMPERATURE)
        self.temperature_spinbox.setMinimumWidth(80)
        self.temperature_spinbox.setToolTip("Temperature value (0.0 - 2.0)")
        self.temperature_spinbox.setObjectName("temperatureSpinBox")  # For theming

        temperature_layout = QVBoxLayout()
        temperature_layout.addWidget(temperature_label)
        temperature_layout.addWidget(self.temperature_slider)
        temperature_layout.addWidget(self.temperature_spinbox)
        layout.addLayout(temperature_layout)

        # Max Tokens Label and Controls
        max_tokens_label = QLabel("Max Tokens:")
        max_tokens_label.setToolTip("Maximum number of tokens in the AI's response")
        max_tokens_label.setObjectName("maxTokensLabel")  # For theming

        self.max_tokens_slider = QSlider(Qt.Horizontal)
        self.max_tokens_slider.setRange(0, 16384)
        self.max_tokens_slider.setValue(self.config.MAX_TOKENS)
        self.max_tokens_slider.setTickInterval(1024)
        self.max_tokens_slider.setTickPosition(QSlider.TicksBelow)
        self.max_tokens_slider.setObjectName("maxTokensSlider")  # For theming

        self.max_tokens_spinbox = QSpinBox()
        self.max_tokens_spinbox.setRange(0, 16384)
        self.max_tokens_spinbox.setValue(self.config.MAX_TOKENS)
        self.max_tokens_spinbox.setMinimumWidth(100)
        self.max_tokens_spinbox.setToolTip("Max tokens (0 - 16384)")
        self.max_tokens_spinbox.setObjectName("maxTokensSpinBox")  # For theming

        max_tokens_layout = QVBoxLayout()
        max_tokens_layout.addWidget(max_tokens_label)
        max_tokens_layout.addWidget(self.max_tokens_slider)
        max_tokens_layout.addWidget(self.max_tokens_spinbox)
        layout.addLayout(max_tokens_layout)

        # AutoG Checkbox
        self.autog_var = QCheckBox("AutoG")
        self.autog_var.setObjectName("autogCheckBox")  # For theming
        layout.addWidget(self.autog_var)

        # Prefix Checkboxes
        self.use_prefix_vars = []
        self.prefix_position_vars = []
        for i in range(6):
            prefix_layout = QVBoxLayout()
            use_prefix_checkbox = QCheckBox(f"Pre {i+1}")
            use_prefix_checkbox.setObjectName(f"usePrefixCheckBox{i+1}")  # For theming
            self.use_prefix_vars.append(use_prefix_checkbox)
            prefix_layout.addWidget(use_prefix_checkbox)
            prefix_position_checkbox = QCheckBox("First")
            prefix_position_checkbox.setChecked(True)
            prefix_position_checkbox.setObjectName(f"prefixPositionCheckBox{i+1}")  # For theming
            self.prefix_position_vars.append(prefix_position_checkbox)
            prefix_layout.addWidget(prefix_position_checkbox)
            layout.addLayout(prefix_layout)

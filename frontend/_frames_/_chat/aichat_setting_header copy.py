# ./frontend/pages/qframes/chat/aichat_setting_header.py

from typing import List, Tuple, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, 
    QComboBox, QSlider, QDoubleSpinBox, QSpinBox,
    QCheckBox, QMessageBox
)

from log.logger import logger
from ai_agent.config.ai_config import Config
from ai_agent.config.prompt_manager import load_all_system_prompts
from ai_agent.models.models import get_model, MODELS


class AIChatSettingsHeader(QFrame):
    """
    QFrame widget for AI chat settings controls.
    Handles model selection, system prompt, temperature, and max tokens settings.
    """
    
    # Define signals
    temperatureChanged = Signal(float)
    maxTokensChanged = Signal(int)
    modelChanged = Signal(str)
    systemPromptChanged = Signal(str)
    stateChanged = Signal(dict)  # New signal for overall state changes
    
    def __init__(self, parent=None):
        """Initialize the settings header frame."""
        super().__init__(parent)
        self.config = Config()
        self.temperature = self.config.CHAT_TEMPERATURE
        self.max_tokens = self.config.MAX_TOKENS
        
        # Set frame properties
        self.setObjectName("settingsHeaderFrame")
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        
        self._init_ui()
        self._connect_signals()
        self._load_saved_state()  # Load any saved state
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main horizontal layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(15)
        
        # Add model selection
        self._init_model_selection(layout)
        
        # Add system prompt selection
        self._init_system_prompt(layout)
        
        # Add temperature controls
        self._init_temperature_controls(layout)
        
        # Add max tokens controls
        self._init_max_tokens_controls(layout)
        
        # Add auto-G checkbox
        self._init_auto_g(layout)
        
        # Add prefix checkboxes
        self._init_prefix_controls(layout)
        
        layout.addStretch()
    
    def _init_model_selection(self, layout):
        """Initialize the model selection combobox."""
        model_label = QLabel("Model:")
        model_label.setToolTip("Select the AI model to use")
        model_label.setObjectName("modelLabel")
        
        self.model_combobox = QComboBox()
        available_models = [model_name for company_models in MODELS.values() 
                          for model_name in company_models.keys()]
        self.model_combobox.addItems(available_models)
        self.model_combobox.setCurrentText(self.config.CHAT_MODEL)
        self.model_combobox.setMinimumWidth(150)
        self.model_combobox.setObjectName("modelComboBox")
        
        layout.addWidget(model_label)
        layout.addWidget(self.model_combobox)
    
    def _init_system_prompt(self, layout):
        """Initialize the system prompt selection."""
        system_prompt_label = QLabel("System Prompt:")
        system_prompt_label.setToolTip("Select the system prompt for the AI")
        system_prompt_label.setObjectName("systemPromptLabel")
        
        self.system_prompt_combobox = QComboBox()
        self.system_prompt_combobox.setObjectName("systemPromptComboBox")
        system_prompts = load_all_system_prompts()
        self.system_prompt_combobox.addItems(system_prompts)
        self.system_prompt_combobox.setMinimumWidth(150)
        
        layout.addWidget(system_prompt_label)
        layout.addWidget(self.system_prompt_combobox)
    
    def _init_temperature_controls(self, layout):
        """Initialize the temperature control slider and spinbox."""
        temperature_label = QLabel("Temp.:")
        temperature_label.setToolTip("Controls the randomness of the AI's output")
        temperature_label.setObjectName("temperatureLabel")
        
        temp_layout = QVBoxLayout()
        
        self.temperature_slider = QSlider(Qt.Horizontal)
        self.temperature_slider.setRange(0, 200)
        self.temperature_slider.setValue(int(self.config.CHAT_TEMPERATURE * 100))
        self.temperature_slider.setTickInterval(10)
        self.temperature_slider.setTickPosition(QSlider.TicksBelow)
        self.temperature_slider.setObjectName("temperatureSlider")
        
        self.temperature_spinbox = QDoubleSpinBox()
        self.temperature_spinbox.setRange(0.0, 2.0)
        self.temperature_spinbox.setSingleStep(0.01)
        self.temperature_spinbox.setDecimals(2)
        self.temperature_spinbox.setValue(self.config.CHAT_TEMPERATURE)
        self.temperature_spinbox.setMinimumWidth(80)
        self.temperature_spinbox.setObjectName("temperatureSpinBox")
        
        temp_layout.addWidget(temperature_label)
        temp_layout.addWidget(self.temperature_slider)
        temp_layout.addWidget(self.temperature_spinbox)
        
        layout.addLayout(temp_layout)
    
    def _init_max_tokens_controls(self, layout):
        """Initialize the max tokens control slider and spinbox."""
        max_tokens_label = QLabel("Max Tokens:")
        max_tokens_label.setToolTip("Maximum number of tokens in the AI's response")
        max_tokens_label.setObjectName("maxTokensLabel")
        
        tokens_layout = QVBoxLayout()
        
        self.max_tokens_slider = QSlider(Qt.Horizontal)
        self.max_tokens_slider.setRange(0, 16384)
        self.max_tokens_slider.setValue(self.config.MAX_TOKENS)
        self.max_tokens_slider.setTickInterval(1024)
        self.max_tokens_slider.setTickPosition(QSlider.TicksBelow)
        self.max_tokens_slider.setObjectName("maxTokensSlider")
        
        self.max_tokens_spinbox = QSpinBox()
        self.max_tokens_spinbox.setRange(0, 16384)
        self.max_tokens_spinbox.setValue(self.config.MAX_TOKENS)
        self.max_tokens_spinbox.setMinimumWidth(100)
        self.max_tokens_spinbox.setObjectName("maxTokensSpinBox")
        
        tokens_layout.addWidget(max_tokens_label)
        tokens_layout.addWidget(self.max_tokens_slider)
        tokens_layout.addWidget(self.max_tokens_spinbox)
        
        layout.addLayout(tokens_layout)
    
    def _init_auto_g(self, layout):
        """Initialize the Auto-G checkbox."""
        self.autog_var = QCheckBox("AutoG")
        self.autog_var.setObjectName("autogCheckBox")
        layout.addWidget(self.autog_var)
    
    def _init_prefix_controls(self, layout):
        """Initialize the prefix checkboxes."""
        self.use_prefix_vars = []
        self.prefix_position_vars = []
        
        for i in range(6):
            prefix_layout = QVBoxLayout()
            
            use_prefix_checkbox = QCheckBox(f"Pre {i+1}")
            use_prefix_checkbox.setObjectName(f"usePrefixCheckBox{i+1}")
            self.use_prefix_vars.append(use_prefix_checkbox)
            prefix_layout.addWidget(use_prefix_checkbox)
            
            prefix_position_checkbox = QCheckBox("First")
            prefix_position_checkbox.setChecked(True)
            prefix_position_checkbox.setObjectName(f"prefixPositionCheckBox{i+1}")
            self.prefix_position_vars.append(prefix_position_checkbox)
            prefix_layout.addWidget(prefix_position_checkbox)
            
            layout.addLayout(prefix_layout)
    
    def _connect_signals(self):
        """Connect all signals to their respective slots."""
        # Model selection
        self.model_combobox.currentTextChanged.connect(self._on_model_changed)
        
        # System prompt
        self.system_prompt_combobox.currentTextChanged.connect(self._on_system_prompt_changed)
        
        # Temperature controls
        self.temperature_slider.valueChanged.connect(self._on_temperature_slider_changed)
        self.temperature_spinbox.valueChanged.connect(self._on_temperature_spinbox_changed)
        
        # Max tokens controls
        self.max_tokens_slider.valueChanged.connect(self._on_max_tokens_slider_changed)
        self.max_tokens_spinbox.valueChanged.connect(self._on_max_tokens_spinbox_changed)
    
    def _on_model_changed(self, model_name: str):
        """Handle model selection changes."""
        try:
            get_model(model_name)  # Validate model exists
            self.modelChanged.emit(model_name)
        except ValueError as e:
            logger.error(f"Model change error: {str(e)}")
            self._show_error("Model Error", str(e))
    
    def _on_system_prompt_changed(self, prompt_name: str):
        """Handle system prompt selection changes."""
        self.systemPromptChanged.emit(prompt_name)
    
    def _on_temperature_slider_changed(self, value: int):
        """Handle temperature slider changes."""
        temperature = value / 100
        self.temperature_spinbox.blockSignals(True)
        self.temperature_spinbox.setValue(temperature)
        self.temperature_spinbox.blockSignals(False)
        self._update_temperature(temperature)
    
    def _on_temperature_spinbox_changed(self, value: float):
        """Handle temperature spinbox changes."""
        self.temperature_slider.blockSignals(True)
        self.temperature_slider.setValue(int(value * 100))
        self.temperature_slider.blockSignals(False)
        self._update_temperature(value)
    
    def _update_temperature(self, temperature: float):
        """Update the temperature value and emit signal."""
        if self.validate_temperature(temperature):
            self.temperature = temperature
            self.config.CHAT_TEMPERATURE = temperature
            self.temperatureChanged.emit(temperature)
            self.save_state()
    
    def _on_max_tokens_slider_changed(self, value: int):
        """Handle max tokens slider changes."""
        self.max_tokens_spinbox.blockSignals(True)
        self.max_tokens_spinbox.setValue(value)
        self.max_tokens_spinbox.blockSignals(False)
        self._update_max_tokens(value)
    
    def _on_max_tokens_spinbox_changed(self, value: int):
        """Handle max tokens spinbox changes."""
        self.max_tokens_slider.blockSignals(True)
        self.max_tokens_slider.setValue(value)
        self.max_tokens_slider.blockSignals(False)
        self._update_max_tokens(value)
    
    def _update_max_tokens(self, value: int):
        """Update the max tokens value and emit signal."""
        if self.validate_max_tokens(value):
            self.max_tokens = value
            self.config.MAX_TOKENS = value
            self.maxTokensChanged.emit(value)
            self.save_state()


    def validate_temperature(self, temperature: float) -> bool:
        """Validate temperature value."""
        try:
            if not 0 <= temperature <= 2:
                raise ValueError("Temperature must be between 0 and 2")
            return True
        except ValueError as e:
            logger.error(f"Temperature validation error: {str(e)}")
            self._show_error("Validation Error", str(e))
            return False

    def validate_max_tokens(self, tokens: int) -> bool:
        """Validate max tokens value."""
        try:
            if not 0 <= tokens <= 16384:
                raise ValueError("Max tokens must be between 0 and 16384")
            return True
        except ValueError as e:
            logger.error(f"Max tokens validation error: {str(e)}")
            self._show_error("Validation Error", str(e))
            return False

    def save_state(self) -> None:
        """Save current state to configuration."""
        try:
            state = self.get_all_settings()
            self.config.save_chat_settings(state)
            self.stateChanged.emit(state)
            
        except Exception as e:
            logger.error(f"Error saving state: {str(e)}")
            self._show_error("Save Error", f"Failed to save settings: {str(e)}")

    def _load_saved_state(self) -> None:
        """Load saved state from configuration."""
        try:
            state = self.config.load_chat_settings()
            if state:
                self._apply_state(state)
        except Exception as e:
            logger.error(f"Error loading saved state: {str(e)}")
            self._show_error("Load Error", f"Failed to load settings: {str(e)}")

    def _apply_state(self, state: dict) -> None:
        """Apply a saved state to the UI."""
        try:
            if 'temperature' in state:
                self._update_temperature(state['temperature'])
            if 'max_tokens' in state:
                self._update_max_tokens(state['max_tokens'])
            if 'model' in state:
                self.model_combobox.setCurrentText(state['model'])
            if 'system_prompt' in state:
                self.system_prompt_combobox.setCurrentText(state['system_prompt'])
            if 'autog' in state:
                self.autog_var.setChecked(state['autog'])
            if 'prefix_states' in state:
                self._apply_prefix_states(state['prefix_states'])
        except Exception as e:
            logger.error(f"Error applying state: {str(e)}")
            self._show_error("State Error", f"Failed to apply settings: {str(e)}")

    def _apply_prefix_states(self, states: List[Tuple[bool, bool]]) -> None:
        """Apply saved prefix states."""
        for (use_checkbox, pos_checkbox), (use_state, pos_state) in zip(
            zip(self.use_prefix_vars, self.prefix_position_vars), states):
            use_checkbox.setChecked(use_state)
            pos_checkbox.setChecked(pos_state)


    def _show_error(self, title: str, message: str) -> None:
        """Show error message to user."""
        logger.error(f"{title}: {message}")
        QMessageBox.critical(self, title, message)

    # Getter methods with type hints
    def get_temperature(self) -> float:
        """Get the current temperature value."""
        return self.temperature
    
    def get_max_tokens(self) -> int:
        """Get the current max tokens value."""
        return self.max_tokens
    
    def get_model(self) -> str:
        """Get the currently selected model."""
        return self.model_combobox.currentText()
    
    def get_system_prompt(self) -> str:
        """Get the currently selected system prompt."""
        return self.system_prompt_combobox.currentText()
    
    def get_autog_state(self) -> bool:
        """Get the Auto-G checkbox state."""
        return self.autog_var.isChecked()
    
    def get_prefix_states(self) -> List[Tuple[bool, bool]]:
        """Get the states of all prefix checkboxes."""
        return [(use.isChecked(), pos.isChecked()) 
                for use, pos in zip(self.use_prefix_vars, self.prefix_position_vars)]
    
    def get_all_settings(self) -> dict:
        """Get all current settings as a dictionary."""
        return {
            'temperature': self.get_temperature(),
            'max_tokens': self.get_max_tokens(),
            'model': self.get_model(),
            'system_prompt': self.get_system_prompt(),
            'autog': self.get_autog_state(),
            'prefix_states': self.get_prefix_states()
        }

    def reset_to_defaults(self) -> None:
        """Reset all settings to default values."""
        try:
            # Reset temperature
            self._update_temperature(self.config.DEFAULT_CHAT_TEMPERATURE)
            self.temperature_slider.setValue(int(self.config.DEFAULT_CHAT_TEMPERATURE * 100))
            self.temperature_spinbox.setValue(self.config.DEFAULT_CHAT_TEMPERATURE)
            
            # Reset max tokens
            self._update_max_tokens(self.config.DEFAULT_MAX_TOKENS)
            self.max_tokens_slider.setValue(self.config.DEFAULT_MAX_TOKENS)
            self.max_tokens_spinbox.setValue(self.config.DEFAULT_MAX_TOKENS)
            
            # Reset model
            self.model_combobox.setCurrentText(self.config.DEFAULT_CHAT_MODEL)
            
            # Reset AutoG
            self.autog_var.setChecked(False)
            
            # Reset prefix checkboxes
            for use_var, pos_var in zip(self.use_prefix_vars, self.prefix_position_vars):
                use_var.setChecked(False)
                pos_var.setChecked(True)
                
            self.save_state()
            
        except Exception as e:
            logger.error(f"Error resetting to defaults: {str(e)}")
            self._show_error("Reset Error", f"Failed to reset settings: {str(e)}")

    def validate_settings(self) -> bool:
        """Validate all current settings."""
        try:
            # Validate temperature
            if not self.validate_temperature(self.temperature):
                return False
            
            # Validate max tokens
            if not self.validate_max_tokens(self.max_tokens):
                return False
            
            # Validate model
            try:
                get_model(self.get_model())
            except ValueError as e:
                self._show_error("Model Error", str(e))
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Settings validation error: {str(e)}")
            self._show_error("Validation Error", str(e))
            return False
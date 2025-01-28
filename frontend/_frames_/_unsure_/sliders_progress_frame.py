


from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QButtonGroup, QCheckBox
)
from ui.widgets.custom_slider import CustomSlider
from ui.widgets.custom_progress_bar import CustomProgressBar
from ui.widgets import SegmentedButton
from ui.widgets.scrollable_frame import ScrollableFrame
from frontend.Theme.fonts import Fonts
from Utils.Enums.enums import ThemeColors


class SliderProgressbarFrame(QFrame):
    progress_changed = Signal(float)  # Value between 0 and 1
    segment_changed = Signal(str)     # Selected segment value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
        
        # Start indeterminate progress
        self.start_progress_animation()

    def setup_ui(self):
        """Initialize the UI components"""
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # Segmented button group
        self.button_layout = QHBoxLayout()
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        
        segments = ["Value 1", "Value 2", "Value 3"]
        for i, text in enumerate(segments):
            btn = SegmentedButton(text)
            self.button_layout.addWidget(btn)
            self.button_group.addButton(btn, i)
            if i == 1:  # Set default selection to "Value 2"
                btn.setChecked(True)
        
        self.layout.addLayout(self.button_layout)
        
        # Progress bars
        self.progress_bar1 = CustomProgressBar()
        self.progress_bar2 = CustomProgressBar()
        self.layout.addWidget(self.progress_bar1)
        self.layout.addWidget(self.progress_bar2)
        
        # Horizontal slider
        self.slider_h = CustomSlider(Qt.Horizontal)
        self.slider_h.setRange(0, 100)
        self.slider_h.setValue(50)
        self.layout.addWidget(self.slider_h)
        
        # Integrate ScrollableFrame with "99" switches
        self.scrollable_switches = ScrollableFrame(self)
        self.layout.addWidget(self.scrollable_switches)
        
        # Vertical slider and vertical progress bar
        self.vertical_layout = QHBoxLayout()
        
        self.slider_v = CustomSlider(Qt.Vertical)
        self.slider_v.setRange(0, 100)
        self.slider_v.setValue(50)
        self.vertical_layout.addWidget(self.slider_v)
        
        self.progress_bar3 = CustomProgressBar(orientation=Qt.Vertical)
        self.progress_bar3.setTextVisible(False)
        self.vertical_layout.addWidget(self.progress_bar3)
        
        self.layout.addLayout(self.vertical_layout)
        
        # Apply frame styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.PRIMARY.value};
                border: none;
            }}
        """)

    def setup_connections(self):
        """Setup signal connections"""
        self.button_group.buttonClicked.connect(self.handle_segment_changed)
        self.slider_h.valueChanged.connect(self.handle_horizontal_slider)
        self.slider_v.valueChanged.connect(self.handle_vertical_slider)
        
        # Connect switch state changes if needed
        for switch in self.scrollable_switches.switches:
            switch.stateChanged.connect(self.handle_switch_state_change)

    def handle_segment_changed(self, button: SegmentedButton):
        """Handle segment button selection"""
        self.segment_changed.emit(button.text())

    def handle_horizontal_slider(self, value: int):
        """Handle horizontal slider value change"""
        normalized_value = value / 100.0
        self.progress_bar2.setValue(value)
        self.progress_changed.emit(normalized_value)

    def handle_vertical_slider(self, value: int):
        """Handle vertical slider value change"""
        self.progress_bar3.setValue(value)

    def handle_switch_state_change(self, state: int):
        """Handle switch (checkbox) state changes"""
        sender = self.sender()
        if isinstance(sender, QCheckBox):
            print(f"{sender.text()} toggled to {'Checked' if state == Qt.Checked else 'Unchecked'}")
            # Implement any additional logic based on switch state

    def start_progress_animation(self):
        """Start the indeterminate progress animation"""
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_indeterminate_progress)
        self.progress_timer.start(50)  # Update every 50ms
        self.progress_value = 0

    def stop_progress_animation(self):
        """Stop the indeterminate progress animation"""
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()

    def update_indeterminate_progress(self):
        """Update the indeterminate progress bar"""
        self.progress_value = (self.progress_value + 2) % 100
        self.progress_bar1.setValue(self.progress_value)

    def set_progress(self, value: float):
        """Set the progress bar values externally"""
        int_value = int(value * 100)
        self.progress_bar2.setValue(int_value)
        self.slider_h.setValue(int_value)
        
    def get_current_segment(self) -> str:
        """Get the currently selected segment"""
        button = self.button_group.checkedButton()
        return button.text() if button else ""


# ./shared/utils/phone_functions.py


from PySide6.QtCore import (
    Qt, Signal, QRect, QPropertyAnimation, 
    QEasingCurve, QSize, QPoint, QEvent, QTimer
)
from PySide6.QtGui import (
    QIcon, QPainter, QColor, QBrush, QPen,
    QGradient, QLinearGradient
)
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QScrollArea, QSlider,
    QStyledItemDelegate, QAbstractItemView,
    QAbstractScrollArea, QMessageBox, QGestureEvent,
    QSwipeGesture, QPinchGesture, QPanGesture,
    QGraphicsDropShadowEffect
)

from Config.AppConfig.icon_config import ICONS
from log.logger import logger
from Styles.theme_manager import ThemeManager

# Base Classes
class MobileBase:
    """Base class with common mobile functionality."""
    def setup_touch_handling(self):
        self.setAttribute(Qt.WA_AcceptTouchEvents, True)
        self.setMouseTracking(True)

    def apply_mobile_optimizations(self):
        MobileOptimizations.apply_optimizations(self)


class QPullToRefreshWidget(QScrollArea):
    """
    A custom widget to implement pull-to-refresh functionality for lists or content.
    Optimized for mobile UI for a smooth and intuitive experience.
    """
    refreshTriggered = Signal()  # Signal emitted when refresh is triggered

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.refresh_threshold = 80  # Pixels to pull down before triggering refresh
        self.start_drag_position = None
        self.is_refreshing = False

        # Add a refresh indicator
        self.refresh_label = QLabel("Pull to refresh...", self)
        self.refresh_label.setAlignment(Qt.AlignCenter)
        self.refresh_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #757575;
                background-color: #E0E0E0;
                border-radius: 10px;
                padding: 5px 10px;
            }
        """)
        self.refresh_label.hide()

    def touchEvent(self, event):
        if event.type() == QEvent.TouchBegin:
            self.start_drag_position = event.pos().y()
        elif event.type() == QEvent.TouchUpdate:
            if self.start_drag_position and not self.is_refreshing:
                distance = event.pos().y() - self.start_drag_position
                if distance > 0:
                    self.refresh_label.show()
                    self.refresh_label.move(self.width() // 2 - 50, int(distance / 2))
                    if distance > self.refresh_threshold:
                        self.refresh_label.setText("Release to refresh")
        elif event.type() == QEvent.TouchEnd:
            if self.start_drag_position:
                distance = event.pos().y() - self.start_drag_position
                self.start_drag_position = None
                if distance > self.refresh_threshold and not self.is_refreshing:
                    self.trigger_refresh()

    def trigger_refresh(self):
        """Trigger the refresh action."""
        self.is_refreshing = True
        self.refresh_label.setText("Refreshing...")
        self.refreshTriggered.emit()

        # Simulate a refresh delay (this should be replaced with actual data loading)
        QTimer.singleShot(1500, self.complete_refresh)

    def complete_refresh(self):
        """Complete the refresh action and reset UI."""
        self.is_refreshing = False
        self.refresh_label.hide()


class HapticFeedback:
    """
    A utility class for triggering haptic feedback on mobile devices.
    Optimized to provide seamless vibration feedback for various interactions.
    """
    def __init__(self):
        self.available = True  # Simulate availability of haptic feedback
        # Replace this with actual haptic feedback setup if supported on the platform.

    def trigger(self, feedback_type):
        """
        Trigger haptic feedback of a specific type.

        Args:
            feedback_type (str): Type of feedback, e.g., 'light', 'medium', 'heavy', or 'success'.
        """
        if not self.available:
            print("Haptic feedback not available on this device.")
            return

        if feedback_type == 'light':
            self._simulate_haptic(50)
        elif feedback_type == 'medium':
            self._simulate_haptic(100)
        elif feedback_type == 'heavy':
            self._simulate_haptic(200)
        elif feedback_type == 'success':
            self._simulate_haptic(100, 50, 100)  # Example: success vibration pattern
        else:
            print(f"Unknown haptic feedback type: {feedback_type}")

    def _simulate_haptic(self, *durations):
        """
        Simulate haptic feedback for testing purposes.

        Args:
            durations (int): Vibration durations in milliseconds.
        """
        print(f"Haptic feedback triggered with durations: {durations}")
        # Replace this with actual platform-dependent vibration API.

class MobileBottomSheet(QWidget):
    """Base class for all mobile bottom sheets in the chat interface."""
    
    dismissed = Signal()  # Emitted when sheet is dismissed
    
    def __init__(self, parent=None, height_ratio=0.7):
        super().__init__(parent)
        self.height_ratio = height_ratio
        self.drag_start = None
        self.setup_touch_handling()
        self.setup_base_ui()
        self.setup_sheet_style()
        
    def setup_base_ui(self):
        """Setup basic bottom sheet UI elements."""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 10, 0, 0)
        
        # Handle bar
        self.handle = QFrame()
        self.handle.setObjectName("bottomSheetHandle")
        self.handle.setFixedSize(40, 4)
        handle_layout = QHBoxLayout()
        handle_layout.addWidget(self.handle)
        handle_layout.setAlignment(Qt.AlignCenter)
        self.layout.addLayout(handle_layout)
        
        # Content area
        self.content = QScrollArea()
        self.content.setWidgetResizable(True)
        self.content.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content.setWidget(self.content_widget)
        self.layout.addWidget(self.content)
        
    def setup_sheet_style(self):
        """Apply consistent styling across all bottom sheets."""
        self.setStyleSheet("""
            QWidget#mobileBottomSheet {
                background: white;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                box-shadow: 0px -2px 10px rgba(0, 0, 0, 0.1);
            }
            QFrame#bottomSheetHandle {
                background: #E0E0E0;
                border-radius: 2px;
            }
            QPushButton {
                min-height: 48px;
                border: none;
                border-radius: 24px;
                padding: 0 20px;
                background: #F5F5F5;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
            QLabel {
                font-size: 14px;
            }
            QTextEdit, QLineEdit {
                padding: 10px;
                border: 1px solid #E0E0E0;
                border-radius: 12px;
                background: white;
            }
        """)

    def show_with_animation(self):
        """Show bottom sheet with smooth animation."""
        self.show()
        animation = QPropertyAnimation(self, b"geometry", self)
        animation.setDuration(300)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        
        parent_height = self.parent().height()
        sheet_height = int(parent_height * self.height_ratio)
        
        start_rect = QRect(0, parent_height, self.parent().width(), sheet_height)
        end_rect = QRect(0, parent_height - sheet_height, self.parent().width(), sheet_height)
        
        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.start()
        
    def hide_with_animation(self):
        """Hide bottom sheet with smooth animation."""
        animation = QPropertyAnimation(self, b"geometry", self)
        animation.setDuration(300)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        
        start_rect = self.geometry()
        end_rect = QRect(0, self.parent().height(), self.width(), self.height())
        
        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.finished.connect(self.hide)
        animation.finished.connect(lambda: self.dismissed.emit())
        animation.start()




class MobileStyles:
    """Common styles for mobile chat interface."""
    
    COMMON_STYLES = """
        /* Common Button Styles */
        QPushButton.mobileActionButton {
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 24px;
            min-height: 48px;
            padding: 0 20px;
            font-size: 14px;
        }
        QPushButton.mobileActionButton:pressed {
            background-color: #1976D2;
        }
        
        /* Common Input Styles */
        QTextEdit.mobileInput, QLineEdit.mobileInput {
            border: 1px solid #E0E0E0;
            border-radius: 12px;
            padding: 10px;
            background: white;
            font-size: 14px;
        }
        
        /* Common List Styles */
        QListWidget.mobileList {
            border: none;
            border-radius: 12px;
            background: white;
        }
        QListWidget.mobileList::item {
            padding: 15px;
            border-bottom: 1px solid #E0E0E0;
        }
        QListWidget.mobileList::item:selected {
            background: #E3F2FD;
            color: #2196F3;
        }
        
        /* Progress Indicators */
        QProgressBar.mobileProgress {
            border: none;
            border-radius: 6px;
            background: #F5F5F5;
            height: 12px;
        }
        QProgressBar.mobileProgress::chunk {
            background: #2196F3;
            border-radius: 6px;
        }
        
        /* Headers and Labels */
        QLabel.mobileHeader {
            font-size: 18px;
            font-weight: bold;
            color: #212121;
            padding: 10px 0;
        }
        QLabel.mobileSubheader {
            font-size: 14px;
            color: #757575;
        }
    """
    
    @staticmethod
    def apply_mobile_theme(widget):
        """Apply mobile theme to widget and all children."""
        widget.setStyleSheet(MobileStyles.COMMON_STYLES)


class MobileGestureHandler:
    """Handles touch gestures for mobile interface."""
    
    def __init__(self, widget):
        self.widget = widget
        self.setup_gestures()
        
    def setup_gestures(self):
        """Setup gesture recognition."""
        self.widget.grabGesture(Qt.SwipeGesture)
        self.widget.grabGesture(Qt.PinchGesture)
        self.widget.grabGesture(Qt.PanGesture)
        
    def handle_gesture_event(self, event: QGestureEvent) -> bool:
        """Handle various gesture events."""
        swipe = event.gesture(Qt.SwipeGesture)
        pinch = event.gesture(Qt.PinchGesture)
        pan = event.gesture(Qt.PanGesture)
        
        if swipe:
            return self._handle_swipe(swipe)
        elif pinch:
            return self._handle_pinch(pinch)
        elif pan:
            return self._handle_pan(pan)
            
        return False
        
    def _handle_swipe(self, gesture):
        """Handle swipe gestures."""
        horizontal = gesture.horizontalDirection()
        vertical = gesture.verticalDirection()
        
        # Implement swipe handling based on direction
        pass
        
    def _handle_pinch(self, gesture):
        """Handle pinch gestures for zoom."""
        scale_factor = gesture.scaleFactor()
        # Implement pinch zoom
        pass
        
    def _handle_pan(self, gesture):
        """Handle pan gestures for scrolling."""
        delta = gesture.delta()
        # Implement smooth scrolling
        pass

class MobileChatCoordinator:
    """Coordinates mobile UI interactions between chat frames."""
    
    def __init__(self):
        self.active_sheet = None
        self.settings_visible = False
        self.analysis_visible = False
        
    def show_settings(self, chat_frame):
        """Show settings and hide other panels."""
        if self.active_sheet:
            self.active_sheet.hide_with_animation()
        self.active_sheet = chat_frame.settings_sheet
        chat_frame.settings_sheet.show_with_animation()
        
    def hide_all_panels(self):
        """Hide all floating panels and sheets."""
        if self.active_sheet:
            self.active_sheet.hide_with_animation()
            self.active_sheet = None
            
    def toggle_chat_list(self, visible: bool):
        """Toggle chat list visibility."""
        pass
        
    def update_layout_for_keyboard(self, keyboard_height: int):
        """Adjust layout when keyboard appears/disappears."""
        pass
        
    def handle_orientation_change(self, orientation: Qt.ScreenOrientation):
        """Handle device orientation changes."""
        pass

class MobileAccessibilityFeatures:
    """Enhanced accessibility and usability features for mobile chat interface."""
    
    # Font size presets
    FONT_SIZES = {
        'small': {
            'body': 12,
            'header': 16,
            'button': 14
        },
        'medium': {
            'body': 14,
            'header': 18,
            'button': 16
        },
        'large': {
            'body': 16,
            'header': 20,
            'button': 18
        }
    }

    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.current_font_size = 'medium'
        self.current_theme = 'light'
        self.setup_features()

    def setup_features(self):
        """Setup additional accessibility features."""
        # Add pull-to-refresh gesture
        self.pull_refresh = QPullToRefreshWidget(self.parent)
        
        # Add floating action button for quick actions
        self.fab = FloatingActionButton(self.parent)
        
        # Add haptic feedback
        self.haptics = HapticFeedback()
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()

class FloatingActionButton(QPushButton):
    """Floating action button for quick access to common actions."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("mobileFAB")
        self.setup_ui()
        self.setup_menu()

    def setup_ui(self):
        self.setFixedSize(56, 56)
        self.setStyleSheet("""
            QPushButton#mobileFAB {
                background-color: #2196F3;
                border-radius: 28px;
                color: white;
                font-size: 24px;
            }
            QPushButton#mobileFAB:pressed {
                background-color: #1976D2;
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

class ChatBubbleDelegate(QStyledItemDelegate):
    """Custom delegate for chat messages to display them as bubbles."""
    
    def paint(self, painter, option, index):
        """Paint chat messages as bubbles with user/AI differentiation."""
        is_user_message = index.data(Qt.UserRole)
        
        # Configure bubble appearance
        if is_user_message:
            bubble_color = QColor("#E3F2FD")
            text_color = QColor("#000000")
            alignment = Qt.AlignRight
        else:
            bubble_color = QColor("#F5F5F5")
            text_color = QColor("#000000")
            alignment = Qt.AlignLeft

        # Draw bubble
        painter.setPen(Qt.NoPen)
        painter.setBrush(bubble_color)
        bubble_rect = option.rect.adjusted(8, 4, -8, -4)
        painter.drawRoundedRect(bubble_rect, 15, 15)

        # Draw text
        painter.setPen(text_color)
        text_rect = bubble_rect.adjusted(12, 8, -12, -8)
        painter.drawText(text_rect, alignment | Qt.AlignVCenter | Qt.TextWordWrap, index.data())

class VoiceInputButton(QPushButton):
    """Button for voice input with visual feedback."""
    
    voiceInput = Signal(str)  # Emits transcribed text
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_recorder()
        
    def setup_ui(self):
        self.setIcon(QIcon(ICONS.get('mic', '')))
        self.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                border-radius: 20px;
                padding: 10px;
            }
            QPushButton:pressed {
                background-color: #F44336;
            }
        """)
        
        # Add recording indicator
        self.indicator = QWidget(self)
        self.indicator.setStyleSheet("background-color: #F44336; border-radius: 5px;")
        self.indicator.hide()

class ChatImageViewer(QWidget):
    """Enhanced image viewer for chat attachments."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.view = QLabel()
        self.view.setScaledContents(True)
        
        # Add zoom controls
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(100, 400)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.handle_zoom)

class NetworkStatusIndicator(QWidget):
    """Network status indicator with automatic retry."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        self.status_icon = QLabel()
        self.status_text = QLabel("Connected")
        self.retry_button = QPushButton("Retry")
        self.retry_button.hide()
        
        layout.addWidget(self.status_icon)
        layout.addWidget(self.status_text)
        layout.addWidget(self.retry_button)

class MobileOptimizations:
    """Mobile-specific optimizations for better performance."""
    
    @staticmethod
    def apply_optimizations(widget):
        # Enable hardware acceleration
        widget.setAttribute(Qt.WA_TranslucentBackground)
        
        # Optimize scrolling
        if isinstance(widget, QAbstractScrollArea):
            widget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
            widget.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
            
        # Enable touch optimization
        widget.setAttribute(Qt.WA_AcceptTouchEvents)

class DarkModeHandler:
    """Handles dark mode transitions and theming."""
    
    DARK_THEME = {
        'background': '#121212',
        'surface': '#1E1E1E',
        'primary': '#BB86FC',
        'text': '#FFFFFF',
        'text_secondary': '#B0B0B0'
    }
    
    LIGHT_THEME = {
        'background': '#FFFFFF',
        'surface': '#F5F5F5',
        'primary': '#2196F3',
        'text': '#000000',
        'text_secondary': '#757575'
    }
    
    @staticmethod
    def apply_theme(widget, is_dark: bool):
        theme = DarkModeHandler.DARK_THEME if is_dark else DarkModeHandler.LIGHT_THEME
        # Apply theme colors recursively
        pass

class ChatFrame(QFrame):
    """Enhanced mobile chat frame with additional features."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_enhanced_features()
        
    def setup_enhanced_features(self):
        # Add floating action button
        self.fab = FloatingActionButton(self)
        self.fab.move(self.width() - 66, self.height() - 66)
        
        # Add voice input
        self.voice_input = VoiceInputButton(self)
        self.voice_input.voiceInput.connect(self.handle_voice_input)
        
        # Add network status
        self.network_status = NetworkStatusIndicator(self)
        
        # Add haptic feedback
        self.haptics = HapticFeedback()
        
        # Setup chat bubbles
        self.chat_list.setItemDelegate(ChatBubbleDelegate())
        
        # Add image viewer
        self.image_viewer = ChatImageViewer(self)
        self.image_viewer.hide()
        
        # Setup dark mode
        self.dark_mode = DarkModeHandler()
        
        # Apply mobile optimizations
        MobileOptimizations.apply_optimizations(self)
        
    def handle_voice_input(self, text: str):
        """Handle voice input transcription."""
        self.haptics.trigger('light')
        self.message_input.setPlainText(text)
        
    def resizeEvent(self, event):
        """Handle resize events for floating elements."""
        super().resizeEvent(event)
        if hasattr(self, 'fab'):
            self.fab.move(self.width() - 66, self.height() - 66)
            
    def show_typing_indicator(self):
        """Show typing indicator with animation."""
        if not hasattr(self, 'typing_indicator'):
            self.typing_indicator = QLabel("AI is typing...", self)
            self.typing_indicator.setStyleSheet("""
                background: rgba(0, 0, 0, 0.1);
                border-radius: 10px;
                padding: 5px 10px;
            """)
        animation = QPropertyAnimation(self.typing_indicator, b"opacity")
        animation.setDuration(500)
        animation.setLoopCount(-1)
        animation.setStartValue(0.4)
        animation.setEndValue(1.0)
        animation.start()
        self.typing_indicator.show()

# Utility Functions
def create_shadow_effect(blur_radius=8, x_offset=0, y_offset=2, color=QColor(0, 0, 0, 80)):
    """Create a consistent shadow effect for mobile elements."""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur_radius)
    shadow.setOffset(x_offset, y_offset)
    shadow.setColor(color)
    return shadow

def apply_mobile_style(widget, style_class):
    """Apply mobile styling to a widget."""
    MobileStyles.apply_mobile_theme(widget)
    widget.setProperty("mobileStyleClass", style_class)


__all__ = [
    'MobileBottomSheet',
    'MobileStyles',
    'MobileGestureHandler',
    'MobileChatCoordinator',
    'MobileAccessibilityFeatures',
    'FloatingActionButton',
    'ChatBubbleDelegate',
    'VoiceInputButton',
    'ChatImageViewer',
    'NetworkStatusIndicator',
    'MobileOptimizations',
    'DarkModeHandler',
    'ChatFrame',
    'apply_mobile_style'
]
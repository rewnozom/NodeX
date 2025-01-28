# ./_markdown_csv_extractor/Phone_Touch_and_Scroll.py

from PySide6.QtWidgets import QScrollArea, QScroller, QScrollerProperties
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from .GUI_Constants_and_Settings import GuiConstants

class TouchScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_touch_scroll()
        
    def setup_touch_scroll(self):
        if GuiConstants.TOUCH_SCROLL:
            # Enable touch scrolling
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setWidgetResizable(True)
            
            # Enable kinetic scrolling
            if GuiConstants.KINETIC_SCROLLING:
                QScroller.grabGesture(
                    self.viewport(),
                    QScroller.LeftMouseButtonGesture
                )
                
                # Configure QScrollerProperties
                scroller = QScroller.scroller(self.viewport())
                properties = QScrollerProperties()
                
                # Set scroller properties
                property_values = {
                    QScrollerProperties.DragStartDistance: 0.002,
                    QScrollerProperties.DragVelocitySmoothingFactor: 0.6,
                    QScrollerProperties.MinimumVelocity: 0.0,
                    QScrollerProperties.MaximumVelocity: 0.6,
                    QScrollerProperties.DecelerationFactor: 0.1,
                }
                
                for key, value in property_values.items():
                    properties.setScrollMetric(key, value)
                
                scroller.setScrollerProperties(properties)
                
                # Style for touch scrolling
                self.setStyleSheet(GuiConstants.get_scroll_stylesheet())
        else:
            # Desktop mode
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setWidgetResizable(True)
            
    def wheelEvent(self, event):
        if GuiConstants.SMOOTH_SCROLL:
            delta = event.angleDelta().y()
            scrollBar = self.verticalScrollBar()
            
            # Calculate new position with smooth scrolling
            value = scrollBar.value()
            newValue = value - (delta / 120.0 * GuiConstants.SCROLL_SPEED)
            
            # Create smooth animation
            self.animation = QPropertyAnimation(scrollBar, b"value")
            self.animation.setDuration(GuiConstants.SCROLL_ANIMATION_DURATION)
            self.animation.setStartValue(value)
            self.animation.setEndValue(newValue)
            self.animation.setEasingCurve(QEasingCurve.OutCubic)
            self.animation.start()
            
            event.accept()
        else:
            super().wheelEvent(event)

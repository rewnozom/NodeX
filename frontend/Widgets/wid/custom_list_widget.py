from PySide6.QtCore import Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QListWidget

class CustomListWidget(QListWidget):
    keyPressed = Signal(QKeyEvent)

    def keyPressEvent(self, event: QKeyEvent):
        self.keyPressed.emit(event)
        super().keyPressEvent(event)

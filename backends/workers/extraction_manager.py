from PySide6.QtCore import QObject, Signal

class ExtractionManager(QObject):
    all_finished = Signal()

    def __init__(self):
        super().__init__()
        self.active_threads = 0

    def thread_finished(self):
        self.active_threads -= 1
        if self.active_threads == 0:
            self.all_finished.emit()

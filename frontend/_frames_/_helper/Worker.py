# pages/qframes/helper/Worker.py

from PySide6.QtCore import QObject, Signal, QThread

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    """
    finished = Signal()
    error = Signal(str)
    result = Signal(object)

class WorkerThread(QThread):
    """
    Worker thread for processing extraction and analysis to keep the GUI responsive.
    """
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = self.function(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()

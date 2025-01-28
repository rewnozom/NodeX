from PySide6.QtCore import QObject, Signal, Slot

class ExtractionWorker(QObject):
    finished = Signal()
    error = Signal(str)
    progress = Signal(int)
    status = Signal(str)

    def __init__(self, extractor_class, input_path, output_path, settings_path):
        super().__init__()
        self.extractor_class = extractor_class
        self.input_path = input_path
        self.output_path = output_path
        self.settings_path = settings_path
        self._is_running = True

    @Slot()
    def run(self):
        try:
            # Create the extractor instance
            extractor = self.extractor_class(
                self.input_path,
                self.output_path,
                self.settings_path
            )
            
            # Connect progress updates if the extractor supports them
            if hasattr(extractor, 'update_progress'):
                extractor.update_progress = self._handle_progress
            if hasattr(extractor, 'update_status'):
                extractor.update_status = self._handle_status

            # Run the extraction
            if self._is_running:
                extractor.run()
                self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def _handle_progress(self, value):
        if self._is_running:
            self.progress.emit(value)

    def _handle_status(self, message):
        if self._is_running:
            self.status.emit(message)

    def stop(self):
        self._is_running = False

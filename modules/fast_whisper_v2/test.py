# test_whisperhub.py

import sys
from PySide6.QtWidgets import QApplication
from modules.fast_whisper_v2.main import WhisperHub

def main():
    app = QApplication(sys.argv)
    whisper_hub = WhisperHub()
    whisper_hub.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

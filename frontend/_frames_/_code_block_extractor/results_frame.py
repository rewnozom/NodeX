from PySide6.QtWidgets import QFrame, QVBoxLayout, QListWidget, QWebEngineView, QSplitter
from PySide6.QtCore import Signal
from pygments.formatters import HtmlFormatter

class ResultsFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.analysis_results = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.results_list = QListWidget()
        self.results_list.currentRowChanged.connect(self.display_result)
        self.result_display = QWebEngineView()
        splitter = QSplitter()
        splitter.addWidget(self.results_list)
        splitter.addWidget(self.result_display)
        layout.addWidget(splitter)

    def update_results(self, results):
        self.analysis_results = results
        self.populate_results_list()

    def populate_results_list(self):
        self.results_list.clear()
        for res in self.analysis_results:
            self.results_list.addItem(f"{res.language} - Complexity: {res.complexity:.2f}")

    def display_result(self, index):
        if 0 <= index < len(self.analysis_results):
            res = self.analysis_results[index]
            html_content = f"""
            <html>
            <head>
                <style>{HtmlFormatter().get_style_defs('.source')}</style>
            </head>
            <body>{res.syntax_highlighted}</body>
            </html>
            """
            self.result_display.setHtml(html_content)
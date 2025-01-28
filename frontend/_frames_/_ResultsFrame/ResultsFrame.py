# pages/qframes/ResultsFrame/ResultsFrame.py

from PySide6.QtWidgets import QFrame, QVBoxLayout, QListWidget, QLineEdit, QLabel, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtWebEngineWidgets import QWebEngineView
from pygments.formatters import HtmlFormatter

from frontend._frames_._helper.CodeAnalysis import CodeAnalysisResult


class ResultsFrame(QFrame):
    """
    Displays the list of code blocks and their details.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.analysis_results = []
        self.initUI()

    def initUI(self):
        try:
            layout = QVBoxLayout()

            # Search Bar
            search_layout = QHBoxLayout()
            self.searchBar = QLineEdit()
            self.searchBar.setPlaceholderText("Search code blocks by language or keyword...")
            self.searchBar.textChanged.connect(self.filterResults)
            search_layout.addWidget(QLabel("Search:"))
            search_layout.addWidget(self.searchBar)
            layout.addLayout(search_layout)

            # Splitter for list and display
            from PySide6.QtWidgets import QSplitter
            splitter = QSplitter(Qt.Horizontal)

            # List of Code Blocks
            self.resultsList = QListWidget()
            self.resultsList.currentRowChanged.connect(self.displayResult)
            splitter.addWidget(self.resultsList)

            # Display Area
            self.resultDisplay = QWebEngineView()
            splitter.addWidget(self.resultDisplay)
            splitter.setSizes([300, 700])

            layout.addWidget(splitter)
            self.setLayout(layout)

            print("ResultsFrame initialized successfully.")
        except Exception as e:
            print(f"Error initializing ResultsFrame: {e}")

    def updateResults(self, results: list):
        try:
            assert all(isinstance(r, CodeAnalysisResult) for r in results), "Invalid results data"
            self.analysis_results.extend(results)
            self.populateResultsList(results)
        except AssertionError as e:
            print(f"Data validation error: {e}")
            raise


    def populateResultsList(self, results: list):
        """
        Populates the results list with new analysis results.
        """
        for res in results:
            item_text = f"{res.language} - Complexity: {res.complexity:.2f}"
            self.resultsList.addItem(item_text)

    def displayResult(self, current_row: int):
        try:
            if current_row < 0 or current_row >= len(self.analysis_results):
                self.resultDisplay.setHtml("")
                return
            res = self.analysis_results[current_row]
            html_content = f"""
            <html>
            <head>
                <style>
                    {HtmlFormatter().get_style_defs('.source')}
                </style>
            </head>
            <body>
                {res.syntax_highlighted}
            </body>
            </html>
            """
            self.resultDisplay.setHtml(html_content)
            print("Result displayed successfully.")
        except Exception as e:
            print(f"Error displaying result: {e}")
            self.resultDisplay.setHtml("<html><body><p>Error loading content.</p></body></html>")

    def filterResults(self, text: str):
        """
        Filters the results list based on the search query.
        """
        for i in range(self.resultsList.count()):
            item = self.resultsList.item(i)
            if text.lower() in item.text().lower():
                self.resultsList.setRowHidden(i, False)
            else:
                self.resultsList.setRowHidden(i, True)

    def clearResults(self):
        """
        Clears all results from the list and display.
        """
        self.resultsList.clear()
        self.resultDisplay.setHtml("")
        self.analysis_results.clear()

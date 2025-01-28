# pages/qframes/helper/CodeAnalysis.py

import re
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter
from radon.complexity import cc_visit

class CodeAnalysisResult:
    """
    Holds the analysis results of a code block.
    """
    def __init__(self, code: str, language: str):
        self.code = code
        self.language = language
        self.syntax_highlighted = ""
        self.complexity = 0
        self.todos = []

    def analyze(self):
        """
        Perform syntax highlighting, complexity analysis, and TODO detection.
        """
        # Syntax Highlighting
        try:
            lexer = get_lexer_by_name(self.language, stripall=True)
        except Exception:
            lexer = TextLexer()
        formatter = HtmlFormatter(full=False, linenos=True, cssclass="source")
        self.syntax_highlighted = highlight(self.code, lexer, formatter)

        # Complexity Analysis
        try:
            blocks = cc_visit(self.code)
            self.complexity = sum(block.complexity for block in blocks) / len(blocks) if blocks else 0
        except Exception:
            self.complexity = 0

        # TODO Detection
        self.todos = re.findall(r'\bTODO\b.*', self.code, re.IGNORECASE)

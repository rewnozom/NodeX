# ./shared/themes/code_block_style.py

from PySide6.QtWidgets import QTextEdit, QTextBrowser
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtCore import QRegularExpression
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
import re
import logging

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)  # Adjust as needed

class CodeBlockHighlighter(QSyntaxHighlighter):
    def __init__(self, document, styles):
        super().__init__(document)
        self.styles = styles
        self.highlightingRules = []
        self.initialize_highlighting_rules()

    def initialize_highlighting_rules(self):
        """
        Initialize syntax highlighting rules based on the provided styles.
        """
        try:
            # Define patterns and corresponding formats
            keywords = [
                "def", "class", "import", "from", "as", "if", "elif", "else",
                "for", "while", "return", "try", "except", "with", "lambda",
                "pass", "break", "continue"
            ]
            keyword_pattern = "\\b(" + "|".join(keywords) + ")\\b"
            self.highlightingRules.append((QRegularExpression(keyword_pattern), self.create_format('keyword_color')))

            # Strings
            string_pattern = "\".*?\"|'.*?'"
            self.highlightingRules.append((QRegularExpression(string_pattern), self.create_format('string_color')))

            # Comments
            comment_pattern = "#[^\n]*"
            self.highlightingRules.append((QRegularExpression(comment_pattern), self.create_format('comment_color')))

            # Functions
            function_pattern = "\\b[A-Za-z0-9_]+(?=\\()"
            self.highlightingRules.append((QRegularExpression(function_pattern), self.create_format('function_color')))

            # Numbers
            number_pattern = "\\b[0-9]+\\b"
            self.highlightingRules.append((QRegularExpression(number_pattern), self.create_format('number_color')))

            # Operators
            operator_pattern = "[+-/*=<>!&|]+"
            self.highlightingRules.append((QRegularExpression(operator_pattern), self.create_format('operator_color')))
        except Exception as e:
            logger.error(f"Error initializing highlighting rules: {e}")

    def create_format(self, style_key):
        """
        Create a QTextCharFormat based on the style key.
        """
        format = QTextCharFormat()
        color = QColor(self.styles.get(style_key, "#FFFFFF"))
        format.setForeground(color)
        if style_key in ['keyword_color', 'string_color', 'comment_color', 'function_color', 'number_color', 'operator_color']:
            format.setFontWeight(QFont.Bold)
        return format

    def highlightBlock(self, text):
        """
        Apply syntax highlighting to the given block of text.
        """
        for pattern, format in self.highlightingRules:
            expression = QRegularExpression(pattern.pattern())
            iterator = expression.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
        self.setCurrentBlockState(0)

class MarkdownRenderer(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.highlighter = None  # To be initialized with styles
        self.initialize_renderer()

    def initialize_renderer(self, styles=None):
        """
        Initialize the renderer with default styles or provided styles.
        """
        if styles:
            self.apply_styles(styles)
        else:
            # Default styles can be set here or via apply_theme
            pass

    def setMarkdown(self, text, language='python'):
        """
        Convert markdown to HTML with syntax-highlighted code blocks.
        """
        html = markdown.markdown(text, extensions=['fenced_code', 'codehilite'])

        # Replace code blocks with syntax-highlighted versions using Pygments
        def replace_code_block(match):
            language = match.group(1) or 'text'
            code = match.group(2)
            try:
                lexer = get_lexer_by_name(language, stripall=True)
            except ValueError:
                lexer = get_lexer_by_name('text', stripall=True)
            formatter = HtmlFormatter(style='default')
            highlighted_code = highlight(code, lexer, formatter)
            return highlighted_code

        html = re.sub(r'<pre><code class="language-(\w+)">(.*?)</code></pre>', replace_code_block, html, flags=re.DOTALL)

        self.setHtml(html)

    def apply_styles(self, styles):
        """
        Apply styles to the MarkdownRenderer.
        """
        try:
            # Initialize the highlighter with styles
            if self.highlighter:
                self.highlighter.setDocument(None)
                del self.highlighter
            self.highlighter = CodeBlockHighlighter(self.document(), styles)

            # Apply additional styles if needed
            self.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {styles.get('background_color', '#1e1e1e')};
                    color: {styles.get('text_color', '#d4d4d4')};
                    font-family: {styles.get('font_family', 'Consolas, Courier New, monospace')};
                    font-size: 12px;  /* Reduced base font size */
                }}
                pre {{
                    background-color: {styles.get('background_color', '#1e1e1e')};
                    color: {styles.get('text_color', '#d4d4d4')};
                    padding: 10px;
                    border-radius: 5px;
                }}
                code {{
                    font-family: {styles.get('font_family', 'Consolas, Courier New, monospace')};
                    font-size: 10px;  /* Further reduced font size for code */
                }}
            """)
            logger.debug("MarkdownRenderer styles applied successfully.")
        except Exception as e:
            logger.error(f"Error applying styles to MarkdownRenderer: {e}")

def apply_code_block_style(widget, styles):
    """
    Apply the code block style to a given text widget.

    Args:
        widget (QTextEdit or QTextBrowser): The text widget to apply the highlighter to.
        styles (dict): The code block style configurations from the theme.
    """
    try:
        if isinstance(widget, (QTextEdit, QTextBrowser)):
            highlighter = CodeBlockHighlighter(widget.document(), styles)
            logger.debug(f"Code block style applied to {widget}.")
        else:
            logger.warning("Widget is not a QTextEdit or QTextBrowser. Cannot apply code block style.")
    except Exception as e:
        logger.error(f"Error applying code block style to widget: {e}")

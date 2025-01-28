# AI_Agent/utils/code_extractor.py

import re
import os
import sys
import requests
import zipfile
from typing import List, Dict, Optional
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter
from radon.complexity import cc_visit
from bs4 import BeautifulSoup

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

class CodeBlockExtractor:
    """
    Extracts and analyzes code blocks from various input sources.
    """
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.ensure_output_dir()

    def ensure_output_dir(self):
        """
        Creates the output directory if it doesn't exist.
        """
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """
        Extracts code blocks demarcated by triple backticks with optional language specifiers.
        Returns a list of dictionaries containing the language and code for each block.
        """
        pattern = r'```(?P<language>\w+)?\n(?P<code>.*?)```'
        matches = re.finditer(pattern, text, re.DOTALL)
        code_blocks = []
        for match in matches:
            language = match.group("language") or "text"
            code = match.group("code").strip()
            code_blocks.append({
                "language": language,
                "code": code
            })
        return code_blocks

    def extract_inline_code(self, text: str) -> List[Dict[str, str]]:
        """
        Extracts inline code snippets enclosed in single backticks.
        """
        pattern = r'`(?P<code>[^`]+)`'
        matches = re.finditer(pattern, text)
        inline_blocks = []
        for match in matches:
            code = match.group("code").strip()
            inline_blocks.append({
                "language": "inline",
                "code": code
            })
        return inline_blocks

    def extract_from_url(self, url: str) -> Optional[str]:
        """
        Fetches and extracts text content from a web page URL.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.get_text()
        except Exception as e:
            print(f"Error fetching URL {url}: {e}")
            return None

    def process_code_block(self, block: Dict[str, str]) -> CodeAnalysisResult:
        """
        Analyzes a single code block.
        """
        analysis = CodeAnalysisResult(code=block["code"], language=block["language"])
        analysis.analyze()
        return analysis

    def process_text(self, text: str) -> List[CodeAnalysisResult]:
        """
        Processes text input to extract and analyze code blocks.
        """
        code_blocks = self.extract_code_blocks(text)
        inline_blocks = self.extract_inline_code(text)
        all_blocks = code_blocks + inline_blocks
        results = []
        for block in all_blocks:
            result = self.process_code_block(block)
            results.append(result)
        return results

    def process_file(self, file_path: str) -> List[CodeAnalysisResult]:
        """
        Processes a single file to extract and analyze code blocks.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.process_text(content)
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            return []

    def process_directory(self, dir_path: str) -> List[CodeAnalysisResult]:
        """
        Recursively processes a directory to extract and analyze code blocks from supported files.
        """
        results = []
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith(('.txt', '.md', '.html')):
                    file_path = os.path.join(root, file)
                    print(f"Processing file: {file_path}")
                    file_results = self.process_file(file_path)
                    results.extend(file_results)
        return results

    def process_url(self, url: str) -> List[CodeAnalysisResult]:
        """
        Processes a web page URL to extract and analyze code blocks.
        """
        text = self.extract_from_url(url)
        if text:
            return self.process_text(text)
        return []

    def save_analysis_results(self, analysis_results: List[CodeAnalysisResult]):
        """
        Saves analyzed code blocks into language-specific directories and generates a summary report.
        """
        summary_path = os.path.join(self.output_dir, "summary.md")
        with open(summary_path, 'w', encoding='utf-8') as summary_file:
            summary_file.write("# Extracted Code Blocks Summary\n\n")
            for idx, result in enumerate(analysis_results, 1):
                language_dir = os.path.join(self.output_dir, result.language)
                os.makedirs(language_dir, exist_ok=True)
                safe_language = re.sub(r'\W+', '', result.language)  # Sanitize language name
                file_name = f"code_block_{idx}.{safe_language if safe_language != 'inline' else 'txt'}"
                file_path = os.path.join(language_dir, file_name)
                try:
                    with open(file_path, 'w', encoding='utf-8') as code_file:
                        code_file.write(result.code)
                    summary_file.write(f"## Code Block {idx} - {result.language}\n")
                    summary_file.write(f"- **File:** `{file_path}`\n")
                    summary_file.write(f"- **Cyclomatic Complexity:** {result.complexity:.2f}\n")
                    if result.todos:
                        summary_file.write(f"- **TODOs:** {', '.join(result.todos)}\n")
                    summary_file.write("\n")
                except Exception as e:
                    print(f"Error saving code block {idx}: {e}")

    def export_as_zip(self, zip_name: str = "extracted_code.zip"):
        """
        Exports the output directory as a ZIP archive.
        """
        zip_path = os.path.join(self.output_dir, zip_name)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(self.output_dir):
                for file in files:
                    if file != zip_name:  # Avoid including the zip file itself
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, self.output_dir)
                        zipf.write(file_path, arcname)
        print(f"Exported all code blocks to {zip_path}")

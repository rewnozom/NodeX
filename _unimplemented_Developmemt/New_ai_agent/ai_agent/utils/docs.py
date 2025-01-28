"""
ai_agent/utils/docs.py - API documentation generator
"""

import inspect
import ast
from pathlib import Path
from typing import Dict, Any, List
import yaml

class APIDocGenerator:
    def __init__(self, source_dir: str, output_dir: str):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.api_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "AI Agent API",
                "version": "1.0.0"
            },
            "paths": {},
            "components": {
                "schemas": {}
            }
        }

    def generate_docs(self):
        """Generate API documentation"""
        # Parse source files
        for py_file in self.source_dir.rglob("*.py"):
            self._process_file(py_file)

        # Generate OpenAPI spec
        spec_file = self.output_dir / "openapi.yaml"
        with open(spec_file, "w") as f:
            yaml.dump(self.api_spec, f)

        # Generate Markdown docs
        self._generate_markdown()

    def _process_file(self, file_path: Path):
        with open(file_path) as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._process_class(node)

    def _process_class(self, node: ast.ClassDef):
        """Extract API info from class"""
        class_info = {
            "description": ast.get_docstring(node),
            "methods": []
        }

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self._process_method(item)
                class_info["methods"].append(method_info)

        # Add to OpenAPI spec
        self._add_to_spec(node.name, class_info)

    def _process_method(self, node: ast.FunctionDef):
        """Extract method info"""
        return {
            "name": node.name,
            "description": ast.get_docstring(node),
            "parameters": self._get_parameters(node),
            "return_type": self._get_return_type(node)
        }

    def _generate_markdown(self):
        """Generate Markdown documentation"""
        docs_dir = self.output_dir / "docs"
        docs_dir.mkdir(exist_ok=True)

        # Generate index
        index = docs_dir / "index.md"
        with open(index, "w") as f:
            f.write("# AI Agent API Documentation\n\n")
            
            for path, ops in self.api_spec["paths"].items():
                f.write(f"## {path}\n\n")
                for method, details in ops.items():
                    f.write(f"### {method.upper()}\n\n")
                    f.write(f"{details['description']}\n\n")

        # Generate component docs
        components = docs_dir / "components.md"
        with open(components, "w") as f:
            f.write("# API Components\n\n")
            
            for name, schema in self.api_spec["components"]["schemas"].items():
                f.write(f"## {name}\n\n")
                f.write(f"{schema['description']}\n\n")
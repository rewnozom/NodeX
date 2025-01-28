"""
ai_agent/utils/reporting.py - Report generation utilities
"""

import json
import markdown
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass
class ReportSection:
    title: str
    content: str
    data: Dict[str, Any]

class ReportGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_workflow_report(
        self,
        workflow_results: Dict[str, Any],
        workflow_status: Dict[str, Any]
    ) -> str:
        """Generate workflow execution report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"workflow_report_{timestamp}.html"

        sections = [
            self._generate_overview_section(workflow_status),
            self._generate_design_section(workflow_results.get("design", {})),
            self._generate_implementation_section(workflow_results.get("implement", {})),
            self._generate_validation_section(workflow_results.get("validate", {}))
        ]

        html = self._render_html_report(sections)
        report_file.write_text(html)
        return str(report_file)

    def _generate_overview_section(self, status: Dict[str, Any]) -> ReportSection:
        """Generate workflow overview section"""
        content = f"""
## Workflow Overview

**Status**: {status['state']}
**Current Step**: {status['current_step']}

### Step Status:
{self._format_step_status(status['steps'])}
"""
        return ReportSection(
            title="Overview",
            content=content,
            data=status
        )

    def _generate_design_section(self, design: Dict[str, Any]) -> ReportSection:
        """Generate design section"""
        if not design:
            return ReportSection(
                title="Design",
                content="No design data available",
                data={}
            )

        content = f"""
## System Design

### Components
{self._format_components(design.get('components', []))}

### Data Flows
{self._format_data_flows(design.get('data_flows', []))}

### API Specifications
```json
{json.dumps(design.get('api_specs', {}), indent=2)}
```
"""
        return ReportSection(
            title="Design",
            content=content,
            data=design
        )

    def _generate_implementation_section(self, implementation: Dict[str, Any]) -> ReportSection:
        """Generate implementation section"""
        if not implementation:
            return ReportSection(
                title="Implementation",
                content="No implementation data available",
                data={}
            )

        content = f"""
## Implementation

### Code
```python
{implementation.get('code', '')}
```

### Tests
```python
{implementation.get('tests', '')}
```
"""
        return ReportSection(
            title="Implementation", 
            content=content,
            data=implementation
        )

    def _generate_validation_section(self, validation: Dict[str, Any]) -> ReportSection:
        """Generate validation section"""
        if not validation:
            return ReportSection(
                title="Validation",
                content="No validation data available",
                data={}
            )

        test_results = validation.get('test_results', {})
        content = f"""
## Validation Results

**Overall Status**: {'Passed' if validation.get('passed', False) else 'Failed'}

### Test Results
- Tests Run: {test_results.get('tests_run', 0)}
- Tests Passed: {test_results.get('tests_passed', 0)}
- Coverage: {test_results.get('test_coverage', 0):.1f}%
- Execution Time: {test_results.get('execution_time', 0):.2f}s

### Issues
{self._format_list(test_results.get('error_messages', []))}

### Coverage Report
{self._format_coverage(test_results.get('coverage_report', {}))}
"""
        return ReportSection(
            title="Validation",
            content=content,
            data=validation
        )

    def _render_html_report(self, sections: List[ReportSection]) -> str:
        """Render report sections as HTML"""
        content = "# Workflow Execution Report\n\n"
        content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for section in sections:
            content += f"{section.content}\n\n"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Workflow Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        pre {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
        code {{ background: #f5f5f5; padding: 2px 5px; border-radius: 3px; }}
        .error {{ color: #bf0000; }}
        .success {{ color: #006400; }}
    </style>
</head>
<body>
    {markdown.markdown(content)}
</body>
</html>
"""
        return html

    def _format_step_status(self, steps: List[Dict[str, Any]]) -> str:
        """Format step status list"""
        result = ""
        for step in steps:
            status = "✓" if step["state"] == "completed" else "✗"
            result += f"- {status} **{step['name']}**: {step['state']}\n"
            if step.get("error"):
                result += f"  - Error: {step['error']}\n"
        return result

    def _format_components(self, components: List[Dict[str, Any]]) -> str:
        """Format component list"""
        result = ""
        for comp in components:
            result += f"### {comp['name']}\n"
            result += f"{comp['description']}\n\n"
            result += "**Interfaces:**\n"
            result += self._format_list(comp['interfaces'])
            result += "\n**Dependencies:**\n"
            result += self._format_list(comp['dependencies'])
            result += "\n"
        return result

    def _format_data_flows(self, flows: List[Dict[str, str]]) -> str:
        """Format data flow list"""
        result = "```mermaid\ngraph LR\n"
        for flow in flows:
            result += f"    {flow['source']} --> {flow['target']}\n"
        result += "```\n"
        return result

    def _format_coverage(self, coverage: Dict[str, Any]) -> str:
        """Format coverage data"""
        result = f"Overall Coverage: {coverage.get('total_coverage', 0):.1f}%\n\n"
        result += "File Coverage:\n"
        for file, data in coverage.get('files', {}).items():
            result += f"- {file}: {data['total_coverage']:.1f}%\n"
            if data['missing_lines']:
                result += f"  - Missing Lines: {data['missing_lines']}\n"
        return result

    def _format_list(self, items: List[str]) -> str:
        """Format simple list"""
        return "".join(f"- {item}\n" for item in items)
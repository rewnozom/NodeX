"""
ai_agent/core/workflow/templates.py - Workflow templates
"""

from typing import Dict, List, Any
from ..agents.base import BaseAgent
from .manager import WorkflowManager

class CodeReviewWorkflow:
    """Code review and improvement workflow"""
    
    def __init__(self,
                judge_agent: BaseAgent,
                reviewer_agent: BaseAgent,
                developer_agent: BaseAgent):
        self.workflow = WorkflowManager()
        self.judge = judge_agent
        self.reviewer = reviewer_agent
        self.developer = developer_agent

    def setup(self, code: str, requirements: List[str]) -> None:
        """Setup review workflow"""
        # Static Analysis 
        self.workflow.add_step(
            name="analyze",
            agent=self.judge,
            inputs={
                "code": code,
                "requirements": requirements,
                "mode": "analysis"
            }
        )

        # Code Review
        self.workflow.add_step(
            name="review",
            agent=self.reviewer,
            inputs={
                "code": code,
                "analysis": "$analyze.results",
                "requirements": requirements
            }
        )

        # Generate Improvements
        self.workflow.add_step(
            name="improve",
            agent=self.developer,
            inputs={
                "code": code,
                "review": "$review.feedback",
                "requirements": requirements
            }
        )

        # Validate Changes
        self.workflow.add_step(
            name="validate",
            agent=self.judge,
            inputs={
                "original_code": code,
                "improved_code": "$improve.code",
                "mode": "comparison"
            }
        )

    async def execute(self) -> Dict[str, Any]:
        """Execute review workflow"""
        return await self.workflow.execute()

    def get_status(self) -> Dict[str, Any]:
        """Get workflow status"""
        return self.workflow.get_status()

class SecurityAuditWorkflow:
    """Security audit workflow"""
    
    def __init__(self,
                judge_agent: BaseAgent,
                security_agent: BaseAgent,
                developer_agent: BaseAgent):
        self.workflow = WorkflowManager()
        self.judge = judge_agent
        self.security = security_agent
        self.developer = developer_agent

    def setup(self, code: str) -> None:
        """Setup security audit workflow"""
        # Vulnerability Scan
        self.workflow.add_step(
            name="scan",
            agent=self.security,
            inputs={
                "code": code,
                "mode": "vulnerability_scan"
            }
        )

        # Dependency Analysis
        self.workflow.add_step(
            name="dependencies",
            agent=self.security,
            inputs={
                "code": code,
                "mode": "dependency_check"
            }
        )

        # Generate Fixes
        self.workflow.add_step(
            name="fix",
            agent=self.developer,
            inputs={
                "code": code,
                "vulnerabilities": "$scan.vulnerabilities",
                "dependencies": "$dependencies.issues"
            }
        )

        # Validate Fixes
        self.workflow.add_step(
            name="validate",
            agent=self.judge,
            inputs={
                "original_code": code,
                "fixed_code": "$fix.code",
                "mode": "security"
            }
        )

    async def execute(self) -> Dict[str, Any]:
        """Execute security audit workflow"""
        return await self.workflow.execute()

    def get_status(self) -> Dict[str, Any]:
        """Get workflow status"""
        return self.workflow.get_status()

class CodeOptimizationWorkflow:
    """Performance optimization workflow"""
    
    def __init__(self,
                judge_agent: BaseAgent,
                developer_agent: BaseAgent,
                architect_agent: BaseAgent):
        self.workflow = WorkflowManager()
        self.judge = judge_agent 
        self.developer = developer_agent
        self.architect = architect_agent

    def setup(self, code: str, performance_targets: Dict[str, Any]) -> None:
        """Setup optimization workflow"""
        # Performance Analysis
        self.workflow.add_step(
            name="analyze",
            agent=self.judge,
            inputs={
                "code": code,
                "mode": "performance",
                "targets": performance_targets
            }
        )

        # Architecture Review
        self.workflow.add_step(
            name="review",
            agent=self.architect,
            inputs={
                "code": code,
                "performance_analysis": "$analyze.results"
            }
        )

        # Implement Optimizations
        self.workflow.add_step(
            name="optimize",
            agent=self.developer,
            inputs={
                "code": code,
                "architecture_feedback": "$review.feedback",
                "performance_targets": performance_targets
            }
        )

        # Benchmark & Validate
        self.workflow.add_step(
            name="benchmark",
            agent=self.judge,
            inputs={
                "original_code": code,
                "optimized_code": "$optimize.code",
                "mode": "benchmark",
                "targets": performance_targets
            }
        )

    async def execute(self) -> Dict[str, Any]:
        """Execute optimization workflow"""
        return await self.workflow.execute()

    def get_status(self) -> Dict[str, Any]:
        """Get workflow status"""
        return self.workflow.get_status()
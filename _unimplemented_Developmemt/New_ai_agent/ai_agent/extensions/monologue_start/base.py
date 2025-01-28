"""
ai_agent/extensions/monologue_start/base.py - Base monologue extensions
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ...core.agents.base import BaseAgent

class MonologueExtension(ABC):
    def __init__(self, agent: BaseAgent):
        self.agent = agent
        
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        pass

    @property
    def priority(self) -> int:
        return 50

class BehaviorAdjustmentExtension(MonologueExtension):
    """Adjusts agent behavior based on conversation"""
    
    @property
    def priority(self) -> int:
        return 10
        
    async def execute(self, messages: List[dict], **kwargs) -> None:
        """Update agent behavior rules"""
        # Analyze recent interactions
        behavior_analysis = await self._analyze_behavior(messages)
        
        # Update behavior rules if needed
        if behavior_analysis["adjustments"]:
            await self._update_behavior(behavior_analysis["adjustments"])

    async def _analyze_behavior(self, messages: List[dict]) -> Dict[str, Any]:
        """Analyze conversation for behavior patterns"""
        system_prompt = "Analyze the conversation and suggest behavior adjustments. Focus on:"
        system_prompt += "\n- Communication style"
        system_prompt += "\n- Task approach"
        system_prompt += "\n- Error handling"
        
        conversation = "\n\n".join(f"{m['role']}: {m['content']}" for m in messages[-5:])
        response = await self.agent.analyze(prompt=system_prompt, content=conversation)
        
        try:
            return {
                "adjustments": response.get("adjustments", []),
                "reasoning": response.get("reasoning", "")
            }
        except:
            return {"adjustments": [], "reasoning": ""}

    async def _update_behavior(self, adjustments: List[str]) -> None:
        """Update agent behavior rules"""
        # Load current rules
        current_rules = await self.agent.get_behavior_rules()
        
        # Apply adjustments
        for adjustment in adjustments:
            if adjustment.startswith("ADD:"):
                current_rules.append(adjustment[4:].strip())
            elif adjustment.startswith("REMOVE:"):
                rule = adjustment[7:].strip()
                if rule in current_rules:
                    current_rules.remove(rule)
            elif adjustment.startswith("MODIFY:"):
                old, new = adjustment[7:].split("->")
                if old.strip() in current_rules:
                    idx = current_rules.index(old.strip())
                    current_rules[idx] = new.strip()
                    
        # Save updated rules
        await self.agent.set_behavior_rules(current_rules)

class MemorizeSolutionsExtension(MonologueExtension):
    """Saves successful solutions to memory"""
    
    @property 
    def priority(self) -> int:
        return 20
        
    async def execute(self, messages: List[dict], **kwargs) -> None:
        """Extract and save solutions from conversation"""
        solutions = await self._extract_solutions(messages)
        
        for solution in solutions:
            await self.agent.save_to_memory(
                content=solution["content"],
                metadata={
                    "type": "solution",
                    "problem": solution["problem"],
                    "success": solution["success"]
                }
            )

    async def _extract_solutions(self, messages: List[dict]) -> List[Dict[str, Any]]:
        """Extract solutions from messages"""
        solutions = []
        current_problem = None
        
        for msg in messages:
            # Detect problem statements
            if self._is_problem_statement(msg["content"]):
                current_problem = msg["content"]
                
            # Detect solutions
            elif current_problem and self._is_solution(msg["content"]):
                solutions.append({
                    "problem": current_problem,
                    "content": msg["content"],
                    "success": self._verify_success(messages, msg)
                })
                current_problem = None
                
        return solutions

    def _is_problem_statement(self, text: str) -> bool:
        """Detect if text describes a problem"""
        keywords = ["how to", "how do i", "help with", "issue:"]
        return any(k in text.lower() for k in keywords)

    def _is_solution(self, text: str) -> bool:
        """Detect if text contains a solution"""
        return len(text) > 50 and ("```" in text or "steps:" in text.lower())

    def _verify_success(self, messages: List[dict], solution_msg: dict) -> bool:
        """Check if solution was successful"""
        start_idx = messages.index(solution_msg)
        follow_up = messages[start_idx+1:start_idx+3]
        
        success_indicators = ["thank", "works", "solved", "fixed"]
        failure_indicators = ["not work", "error", "issue", "problem"]
        
        for msg in follow_up:
            if msg["role"] == "user":
                text = msg["content"].lower()
                if any(i in text for i in success_indicators):
                    return True
                if any(i in text for i in failure_indicators):
                    return False
                    
        return True  # Assume success if no negative feedback
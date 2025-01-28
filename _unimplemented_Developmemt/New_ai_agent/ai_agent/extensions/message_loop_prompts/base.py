"""
ai_agent/extensions/message_loop_prompts/base.py - Base message loop extension
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Any
from ...core.agents.base import BaseAgent

class MessageLoopExtension(ABC):
    """Base class for message loop extensions"""
    
    def __init__(self, agent: BaseAgent):
        self.agent = agent
        
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the extension"""
        pass

    @property
    def priority(self) -> int:
        """Extension priority (lower runs first)"""
        return 50

class RecallMemoriesExtension(MessageLoopExtension):
    """Extension for memory recall"""
    
    @property
    def priority(self) -> int:
        return 10
        
    async def execute(self, messages: List[dict], **kwargs) -> Optional[str]:
        """Recall relevant memories based on context"""
        if not messages:
            return None
            
        # Get last message
        last_message = messages[-1]["content"]
        
        # Search memory
        memories = await self.agent.search_memory(
            query=last_message,
            limit=3,
            threshold=0.7
        )
        
        if not memories:
            return None
            
        # Format memories
        memory_text = "\n\n".join(f"Memory {i+1}:\n{memory.content}" 
            for i, memory in enumerate(memories)
        )
        
        return f"Relevant Context:\n{memory_text}"

class OrganizeHistoryExtension(MessageLoopExtension):
    """Extension for managing conversation history"""
    
    @property
    def priority(self) -> int:
        return 20

    async def execute(self, **kwargs) -> None:
        """Compress and organize conversation history"""
        if len(self.agent.history) > self.agent.config.max_history:
            # Group messages into topics
            topics = await self._group_messages(self.agent.history)
            
            # Summarize old topics
            for topic in topics[:-3]:  # Keep last 3 topics expanded
                summary = await self._summarize_topic(topic)
                topic.messages = [{"role": "system", "content": summary}]
                
            self.agent.history = topics

    async def _group_messages(self, messages: List[dict]) -> List[List[dict]]:
        """Group messages into coherent topics"""
        topics = []
        current_topic = []
        
        for msg in messages:
            # Check if message starts new topic
            if self._is_new_topic(msg, current_topic):
                if current_topic:
                    topics.append(current_topic)
                current_topic = []
            current_topic.append(msg)
            
        if current_topic:
            topics.append(current_topic)
            
        return topics

    async def _summarize_topic(self, messages: List[dict]) -> str:
        """Generate concise summary of topic"""
        content = "\n".join(m["content"] for m in messages)
        summary = await self.agent.summarize(content)
        return summary

    def _is_new_topic(self, message: dict, current_topic: List[dict]) -> bool:
        """Determine if message starts new topic"""
        if not current_topic:
            return True
            
        # Topic breaks on task completion or context switch
        if any(phrase in message["content"].lower() 
              for phrase in ["task complete", "moving on", "next task"]):
            return True
            
        return False

class SaveChatExtension(MessageLoopExtension):
    """Extension for persisting chat history"""
    
    @property
    def priority(self) -> int:
        return 90
        
    async def execute(self, **kwargs) -> None:
        """Save chat history to storage"""
        await self.agent.save_history()
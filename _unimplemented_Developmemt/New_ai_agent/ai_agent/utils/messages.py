"""
ai_agent/utils/messages.py - Message handling utilities
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime = datetime.now()
    metadata: Optional[Dict[str, Any]] = None

class MessageHistory:
    def __init__(self, max_messages: int = 1000):
        self.messages: List[Message] = []
        self.max_messages = max_messages

    def add(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add message to history"""
        if len(self.messages) >= self.max_messages:
            self.messages.pop(0)
        self.messages.append(Message(role=role, content=content, metadata=metadata))

    def get_last_n(self, n: int) -> List[Message]:
        """Get last n messages"""
        return self.messages[-n:]

    def clear(self):
        """Clear message history"""
        self.messages.clear()

    def format_for_model(self, system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        """Format messages for model input"""
        formatted = []
        if system_prompt:
            formatted.append({
                "role": "system",
                "content": system_prompt
            })
        
        for msg in self.messages:
            formatted.append({
                "role": msg.role,
                "content": msg.content
            })
        return formatted

    def export_json(self) -> List[Dict[str, Any]]:
        """Export messages as JSON"""
        return [{
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "metadata": msg.metadata
        } for msg in self.messages]

class MessageProcessor:
    @staticmethod
    def extract_code_blocks(content: str) -> List[str]:
        """Extract code blocks from message"""
        code_blocks = []
        in_block = False
        current_block = []
        
        for line in content.split('\n'):
            if line.startswith('```'):
                if in_block:
                    code_blocks.append('\n'.join(current_block))
                    current_block = []
                in_block = not in_block
            elif in_block:
                current_block.append(line)
                
        return code_blocks

    @staticmethod
    def extract_tasks(content: str) -> List[str]:
        """Extract task items from message"""
        tasks = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith(('- [ ]', '* [ ]', '- []', '* []')):
                task = line[line.find(']')+1:].strip()
                if task:
                    tasks.append(task)
        return tasks

    @staticmethod
    def summarize_messages(messages: List[Message], max_length: int = 500) -> str:
        """Generate summary of message history"""
        total_content = ' '.join(msg.content for msg in messages)
        words = total_content.split()
        
        if len(words) <= max_length:
            return total_content
            
        return ' '.join(words[:max_length]) + '...'
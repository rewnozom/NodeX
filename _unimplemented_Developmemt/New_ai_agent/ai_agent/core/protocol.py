"""
ai_agent/core/protocol.py - Agent communication protocol
"""

import asyncio
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class MessageType(Enum):
    TASK = "task"
    RESULT = "result"
    ERROR = "error"
    STATUS = "status"
    CANCEL = "cancel"

@dataclass
class Message:
    type: MessageType
    sender: str
    receiver: str
    content: Dict[str, Any]
    id: Optional[str] = None
    reply_to: Optional[str] = None

class AgentProtocol:
    def __init__(self):
        self.message_queue = asyncio.Queue()
        self.handlers = {}
        self.running = False

    async def start(self):
        """Start message processing"""
        self.running = True
        asyncio.create_task(self._process_messages())

    async def stop(self):
        """Stop message processing"""
        self.running = False
        while not self.message_queue.empty():
            await self.message_queue.get()

    async def send(self, message: Message):
        """Send message to queue"""
        await self.message_queue.put(message)

    def register_handler(self, message_type: MessageType, handler):
        """Register message handler"""
        self.handlers[message_type] = handler

    async def _process_messages(self):
        """Process messages from queue"""
        while self.running:
            message = await self.message_queue.get()
            
            try:
                handler = self.handlers.get(message.type)
                if handler:
                    response = await handler(message)
                    if response:
                        await self.send(response)
            except Exception as e:
                error_msg = Message(
                    type=MessageType.ERROR,
                    sender="protocol",
                    receiver=message.sender,
                    content={"error": str(e)},
                    reply_to=message.id
                )
                await self.send(error_msg)

            self.message_queue.task_done()
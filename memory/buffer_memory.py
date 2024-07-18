
from typing import List

from memory.memory import Memory
from schema.prompt.openai_chat import Message

class BufferMemory(Memory):
    def __init__(self, memory_key: str) -> None:
        self._message_history: List[Message] = []
        super().__init__(memory_key)

    def add_message(self, message: Message) -> None:
        self._message_history.append(message)

    def get_messages(self, _: List[Message]) -> List[Message]:
        return self._message_history

__all__ = [
    "BufferMemory"
]

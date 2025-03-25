
from typing import TypeVar

from memory.buffer_memory import BufferMemory

T = TypeVar("T")

class WindowBufferMemory(BufferMemory[T]):

    def __init__(self, memory_key: str, window_size: int) -> None:
        super().__init__(memory_key)
        self._window_size: int = window_size

    def save_context(self, context: T) -> None:
        buffer = self.get_contexts(None)
        buffer.append(context)
        self._buffer = buffer[-self._window_size:]

__all__ = [
    "WindowBufferMemory"
]

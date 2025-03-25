
from typing import List
from typing import TypeVar

from memory.memory import Memory

T = TypeVar("T")

class BufferMemory(Memory[T]):

    def __init__(self, memory_key: str) -> None:
        super().__init__(memory_key)
        self._buffer: List[T] = []

    def save_context(self, context: T) -> None:
        self._buffer.append(context)

    def get_contexts(self, _: List[T]) -> List[T]:
        return self._buffer

    def reset_memory(self) -> None:
        self._buffer.clear()

__all__ = [
    "BufferMemory"
]


from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import List
from typing import TypeVar
from typing import Generic

T = TypeVar("T")

class Memory(ABC, Generic[T]):

    def __init__(self, memory_key: str) -> None:
        self.__memory_key: str = memory_key

    @property
    def memory_key(self) -> str:
        return self.__memory_key

    @abstractmethod
    def save_context(self, context: T) -> Any:
        pass

    @abstractmethod
    def get_contexts(self, contexts: List[T]) -> List[T]:
        pass

    @abstractmethod
    def reset_memory(self) -> None:
        pass

__all__ = [
    "Memory"
]

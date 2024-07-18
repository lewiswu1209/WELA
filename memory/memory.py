
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import List

from schema.prompt.openai_chat import Message

class Memory(ABC):
    def __init__(self, memory_key: str) -> None:
        self.__memory_key: str = memory_key

    @property
    def memory_key(self) -> str:
        return self.__memory_key

    @abstractmethod
    def add_message(self, message: Message) -> Any:
        pass

    @abstractmethod
    def get_messages(self, message: List[Message]) -> List[Message]:
        pass

__all__ = [
    "Memory"
]

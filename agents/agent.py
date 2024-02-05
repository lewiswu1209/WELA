
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Generator

from schema.message import AIMessage

class Agent(ABC):

    def __init__(self,
        input_key: str = "input",
        output_key: str = "output"
    ) -> None:
        self.__input_key: str = input_key
        self.__output_key: str = output_key

    @property
    def output_key(self) -> str:
        return self.__output_key

    @property
    def input_key(self) -> str:
        return self.__input_key

    @abstractmethod
    def predict(self, **kwargs: Any) -> AIMessage | Generator:
        pass

    @abstractmethod
    def run(self, **kwargs: Any) -> str | Generator:
        pass

__all__ = [
    "Agent"
]

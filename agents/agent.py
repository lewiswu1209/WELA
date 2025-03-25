
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Union
from typing import Generator

class Agent(ABC):

    def __init__(self,
        *,
        input_key: str,
        output_key: str
    ) -> None:
        self.__input_key: str = input_key
        self.__output_key: str = output_key

    @property
    def input_key(self) -> str:
        return self.__input_key

    @property
    def output_key(self) -> str:
        return self.__output_key

    @abstractmethod
    def predict(self, **kwargs: Any) -> Union[Any, Generator[Any, None, None]]:
        pass

__all__ = [
    "Agent"
]

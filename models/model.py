
from abc import ABC
from abc import abstractmethod
from typing import List
from typing import Union
from typing import TypeVar
from typing import Generic
from typing import Generator

T = TypeVar("T")

class Model(ABC, Generic[T]):

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @property
    @abstractmethod
    def streaming(self) -> bool:
        pass

    @abstractmethod
    def predict(self, **kargs) -> Union[List[T], Generator[List[T], None, None]]:
        pass

__all__ = [
    "Model"
]


from abc import ABC
from abc import abstractmethod

class Model(ABC):

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @property
    @abstractmethod
    def streaming(self) -> bool:
        pass

__all__ = [
    "Model"
]


from abc import ABC
from abc import abstractmethod
from typing import List

class Embedding(ABC):

    @abstractmethod
    def embed(self, sentence_list: List[str]) -> List[List[float]]:
        pass

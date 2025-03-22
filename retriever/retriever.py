
from abc import ABC
from abc import abstractmethod
from typing import List

from schema.document.document import Document

class Retriever(ABC):

    def __init__(self, retriever_key: str) -> None:
        super().__init__()
        self.__retriever_key: str = retriever_key

    @property
    def retriever_key(self) -> str:
        return self.__retriever_key

    @abstractmethod
    def add_documents(self, documents: List[Document]) -> None:
        pass

    @abstractmethod
    def retrieve(self, query: str) -> List[Document]:
        pass


from torch import Tensor
from numpy import ndarray
from sentence_transformers import SentenceTransformer

from typing import List
from typing import Union
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance
from qdrant_client.models import PointStruct
from qdrant_client.models import VectorParams
from qdrant_client.models import ExtendedPointId
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.conversions.common_types import ScoredPoint

from memory import Memory
from schema.message import Message

def compare_scored_points_id(scored_point: ScoredPoint) -> ExtendedPointId:
    return scored_point.id

class QdrantMemory(Memory):
    def __init__(self, memory_key: str, qdrant_client: QdrantClient, limit: int=10, score_threshold: Optional[float] = None) -> None:
        super().__init__(memory_key)
        self.__sentence_transformer: SentenceTransformer = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.__score_threshold: Optional[float] = score_threshold
        self.__limit: int = limit
        self.__client: QdrantClient = qdrant_client
        try:
            self.__client.create_collection(
                collection_name=self.memory_key,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
        except UnexpectedResponse as e:
            pass
        except ValueError:
            pass

    def __text2embedding(self, text: Union[str, List[str]]) -> Union[List[Tensor], ndarray, Tensor]:
        return self.__sentence_transformer.encode(text).tolist()

    def add_message(self, message: Message) -> None:
        vector = [float(x) for x in self.__text2embedding(message["content"])]
        id = self.__client.count(collection_name=self.memory_key).count + 1
        self.__client.upsert(
            collection_name=self.memory_key,
            points=[
                PointStruct(
                    id=id,
                    vector=vector,
                    payload=message
                )
            ]
        )

    def get_messages(self, sentences: str) -> List[Message]:
        sentences_vector = [float(x) for x in self.__text2embedding(sentences)]
        hits = self.__client.search(
            collection_name=self.memory_key,
            query_vector=sentences_vector,
            limit=self.__limit,
            score_threshold = self.__score_threshold,
        )
        hits = sorted(hits, key=compare_scored_points_id)
        return [Message.from_dict(hit.payload) for hit in hits]

__all__ = [
    "QdrantMemory"
]

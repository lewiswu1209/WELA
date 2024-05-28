
from torch import Tensor
from numpy import ndarray
from typing import List
from typing import Union
from typing import Optional
from sentence_transformers import SentenceTransformer

from qdrant_client import QdrantClient
from qdrant_client.models import Distance
from qdrant_client.models import PointStruct
from qdrant_client.models import VectorParams
from qdrant_client.models import ExtendedPointId
from qdrant_client.http.exceptions import UnexpectedResponse

from memory.memory import Memory
from schema.message import Message

def compare_point_id(point: PointStruct) -> ExtendedPointId:
    return point.id

class WindowQdrantMemory(Memory):
    def __init__(self, memory_key: str, qdrant_client: QdrantClient, limit: int=15, window_size: int = 5, score_threshold: Optional[float] = None) -> None:
        super().__init__(memory_key)
        self.__sentence_transformer: SentenceTransformer = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.__score_threshold: Optional[float] = score_threshold
        self.__limit: int = limit - window_size
        self.__client: QdrantClient = qdrant_client
        self.__window_size: int = window_size
        self._message_history: List[PointStruct] = []
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
        point = PointStruct(
            id=id,
            vector=vector,
            payload=message
        )
        messages = self._message_history
        messages.append(point)
        self._message_history = messages[-self.__window_size:]
        self.__client.upsert(
            collection_name=self.memory_key,
            points=[point]
        )

    def get_messages(self, sentences: str) -> List[Message]:
        sentences_vector = [float(x) for x in self.__text2embedding(sentences)]
        scored_points = self.__client.search(
            collection_name=self.memory_key,
            query_vector=sentences_vector,
            limit=self.__limit,
            score_threshold = self.__score_threshold,
        )
        searched_points = [PointStruct(id=scored_point.id, vector = [float(x) for x in self.__text2embedding(scored_point.payload["content"])], payload=scored_point.payload) for scored_point in scored_points]
        all_points = searched_points + self._message_history
        all_points = sorted(all_points, key=compare_point_id)
        uniq_points= []
        for point in all_points:
            if point.id not in [uniq_point.id for uniq_point in uniq_points]:
                uniq_points.append(point)
        return [Message.from_dict(uniq_point.payload) for uniq_point in uniq_points]

__all__ = [
    "QdrantMemory"
]

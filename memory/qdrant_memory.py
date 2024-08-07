
from uuid import uuid4
from torch import Tensor
from numpy import ndarray
from typing import Any
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
from qdrant_client.conversions.common_types import ScoredPoint

from memory.memory import Memory
from schema.prompt.openai_chat import Message

def unique(scored_points: List[ScoredPoint]):
    seen_uuids = set()
    unique_scored_points: List[ScoredPoint] = []
    for scored_point in scored_points:
        if scored_point.payload["uuid"] not in seen_uuids:
            seen_uuids.add(scored_point.payload["uuid"])
            unique_scored_points.append(scored_point)
    return unique_scored_points

def sort_key_id(scored_point: ScoredPoint) -> ExtendedPointId:
    return scored_point.id

def sort_key_score(scored_point: ScoredPoint) -> float:
    return scored_point.score

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
        except UnexpectedResponse as _:
            pass
        except ValueError:
            pass

    def __text2embedding(self, text: Union[str, List[str]]) -> Union[List[Tensor], ndarray, Tensor]:
        return self.__sentence_transformer.encode(text).tolist()

    def add_message(self, message: Message) -> Any:
        payload={
            "uuid": str(uuid4()),
            "message": message
        }
        if isinstance(message["content"], str):
            sentences = [message["content"]]
        else:
            sentences = []
            for content in message["content"]:
                if content["type"] == "text":
                    sentences.append(content["text"])
        sentences_embedding = self.__text2embedding(sentences)
        point = None
        for sentence_embedding in sentences_embedding:
            vector = [float(x) for x in sentence_embedding]
            id = self.__client.count(collection_name=self.memory_key).count + 1
            point = PointStruct(
                id=id,
                vector=vector,
                payload=payload
            )
            self.__client.upsert(
                collection_name=self.memory_key,
                points=[point]
            )
        return point

    def _get_points_by_sentence(self, sentence: str) -> List[ScoredPoint]:
        sentence_embedding = self.__text2embedding(sentence)
        vector = [float(x) for x in sentence_embedding]
        return self.__client.search(
            collection_name=self.memory_key,
            query_vector=vector,
            limit=self.__limit,
            score_threshold = self.__score_threshold,
        )

    def _get_points_by_sentence_list(self, sentence_list: List[str]) -> List[ScoredPoint]:
        scored_points: List[ScoredPoint] = []
        for sentence in sentence_list:
            scored_points.extend( self._get_points_by_sentence(sentence) )
        return scored_points

    def _get_points_by_message(self, message: Message) -> List[ScoredPoint]:
        if isinstance(message["content"], str):
            sentence_list = [message["content"]]
        else:
            sentence_list = []
            for content in message["content"]:
                if content["type"] == "text":
                    sentence_list.append(content["text"])
        return self._get_points_by_sentence_list(sentence_list)

    def _get_points_by_message_list(self, message_list: List[Message]) -> List[ScoredPoint]:
        scored_points: List[ScoredPoint] = []
        for message in message_list:
            scored_points.extend(self._get_points_by_message(message))
        return scored_points

    def get_messages(self, message_list: List[Message]) -> List[Message]:
        scored_points = self._get_points_by_message_list(message_list)
        scored_points = unique(scored_points)
        scored_points = sorted(scored_points, key=sort_key_score)
        scored_points = scored_points[-self.__limit:]
        scored_points = sorted(scored_points, key=sort_key_id)

        return [scored_point.payload["message"] for scored_point in scored_points]

__all__ = [
    "QdrantMemory",
    "unique",
    "sort_key_id",
    "sort_key_score"
]

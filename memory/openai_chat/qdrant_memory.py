
from uuid import uuid4
from typing import Any
from typing import List
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Record
from qdrant_client.models import Distance
from qdrant_client.models import PointStruct
from qdrant_client.models import VectorParams
from qdrant_client.models import ExtendedPointId
from qdrant_client.conversions.common_types import ScoredPoint

from memory.memory import Memory
from embedding.text_embedding import text_embedding
from schema.prompt.openai_chat import Message

def unique(scored_points: List[ScoredPoint]) -> List[ScoredPoint]:
    seen_uuids = set()
    unique_scored_points: List[ScoredPoint] = []
    scored_points = sorted(scored_points, key=sort_key_id, reverse=True)
    for scored_point in scored_points:
        if scored_point.payload["uuid"] not in seen_uuids:
            seen_uuids.add(scored_point.payload["uuid"])
            unique_scored_points.append(scored_point)
    return unique_scored_points

def sort_key_id(scored_point: ScoredPoint) -> ExtendedPointId:
    return scored_point.id

def sort_key_score(scored_point: ScoredPoint) -> float:
    return scored_point.score

class QdrantMemory(Memory[Message]):
    def __init__(self, memory_key: str, qdrant_client: QdrantClient, limit: int=10, score_threshold: Optional[float] = None) -> None:
        super().__init__(memory_key)

        self.__score_threshold: Optional[float] = score_threshold
        self.__limit: int = limit
        self.__client: QdrantClient = qdrant_client

        if not self.__client.collection_exists(collection_name=self.memory_key):
            self.__client.create_collection(
                collection_name=self.memory_key,
                vectors_config=VectorParams(size=512, distance=Distance.COSINE)
            )

    def save_context(self, context: Message) -> Any:
        payload={
            "uuid": str(uuid4()),
            "message": context
        }
        if isinstance(context["content"], str):
            sentences = [context["content"]]
        else:
            sentences = []
            for content in context["content"]:
                if content["type"] == "text":
                    sentences.append(content["text"])
        sentences_embedding = text_embedding.embed(sentences)

        count = self.__client.count(collection_name=self.memory_key).count
        points = [
            PointStruct(
                id = count + idx,
                vector = [float(x) for x in sentence_embedding],
                payload = payload
            )
            for idx, sentence_embedding in enumerate(sentences_embedding)
        ]

        self.__client.upsert(
            collection_name=self.memory_key,
            points=points
        )

    def _get_points_by_sentence(self, sentence: str) -> List[ScoredPoint]:
        sentence_embedding = text_embedding.embed([sentence])[0]
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

    def _get_last_n_points(self, n: int) -> List[ScoredPoint]:
        ids: List[int] = [id + 1 for id in range(0, self.__client.count(collection_name=self.memory_key).count)][-n:]
        records: List[Record] = self.__client.retrieve(
            collection_name=self.memory_key,
            ids=ids
        )
        return [ScoredPoint(id=record.id, version=record.id-1, score=1.0, payload=record.payload, vector=record.vector) for record in records]

    def get_contexts(self, contexts: List[Message]) -> List[Message]:
        scored_points = self._get_points_by_message_list(contexts)
        scored_points = unique(scored_points)
        scored_points = sorted(scored_points, key=sort_key_score)
        scored_points = scored_points[-self.__limit:]
        scored_points = sorted(scored_points, key=sort_key_id)

        return [scored_point.payload["message"] for scored_point in scored_points]

    def reset_memory(self) -> None:
        self.__client.delete_collection(self.memory_key)

        self.__client.create_collection(
            collection_name=self.memory_key,
            vectors_config=VectorParams(size=512, distance=Distance.COSINE),
        )

__all__ = [
    "QdrantMemory",
    "unique",
    "sort_key_id",
    "sort_key_score"
]

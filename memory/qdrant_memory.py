
from uuid import uuid4
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
from qdrant_client.conversions.common_types import ScoredPoint

from memory.memory import Memory
from schema.prompt.openai_chat import Message

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
        except UnexpectedResponse as _:
            pass
        except ValueError:
            pass

    def __text2embedding(self, text: Union[str, List[str]]) -> Union[List[Tensor], ndarray, Tensor]:
        return self.__sentence_transformer.encode(text).tolist()

    def add_message(self, message: Message) -> None:
        if isinstance(message["content"], str):
            sentences = [message["content"]]
        else:
            sentences = []
            for content in message["content"]:
                if content["type"] == "text":
                    sentences.append(content["text"])
        payload={
            "uuid": str(uuid4()),
            "message": message
        }
        sentences_embedding = self.__text2embedding(sentences)
        for sentence_embedding in sentences_embedding:
            vector = [float(x) for x in sentence_embedding]
            id = self.__client.count(collection_name=self.memory_key).count + 1
            self.__client.upsert(
                collection_name=self.memory_key,
                points=[
                    PointStruct(
                        id=id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )

    def get_messages(self, message: Message) -> List[Message]:
        if isinstance(message["content"], str):
            sentences = [message["content"]]
        else:
            sentences = []
            for content in message["content"]:
                if content["type"] == "text":
                    sentences.append(content["text"])

        sentences_embedding = self.__text2embedding(sentences)
        searched_scored_points: List[ScoredPoint] = []
        for sentence_embedding in sentences_embedding:
            vector = [float(x) for x in sentence_embedding]
            scored_points = self.__client.search(
                collection_name=self.memory_key,
                query_vector=vector,
                limit=self.__limit,
                score_threshold = self.__score_threshold,
            )
            searched_scored_points.extend(scored_points)

        seen_uuids = set()
        unique_scored_points: List[ScoredPoint] = []
        for searched_scored_point in searched_scored_points:
            if searched_scored_point.payload["uuid"] not in seen_uuids:
                seen_uuids.add(searched_scored_point.payload["uuid"])
                unique_scored_points.append(searched_scored_point)
        sorted_unique_scored_points = sorted(unique_scored_points, key=compare_scored_points_id)
        return [scored_point.payload["message"] for scored_point in sorted_unique_scored_points]

__all__ = [
    "QdrantMemory"
]

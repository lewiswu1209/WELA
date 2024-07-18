
from typing import List
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from qdrant_client.conversions.common_types import ScoredPoint

from memory.qdrant_memory import QdrantMemory
from memory.qdrant_memory import unique
from memory.qdrant_memory import sort_key_id
from memory.qdrant_memory import sort_key_score
from schema.prompt.openai_chat import Message

class WindowQdrantMemory(QdrantMemory):
    def __init__(self, memory_key: str, qdrant_client: QdrantClient, limit: int=15, window_size: int = 5, score_threshold: Optional[float] = None) -> None:
        super().__init__(memory_key, qdrant_client, limit, score_threshold)
        self.__limit: int = limit
        self.__window_size: int = window_size
        self.__message_history: List[PointStruct] = []

    def add_message(self, message: Message) -> None:
        point = super().add_message(message)
        messages = self.__message_history
        messages.append(point)
        self.__message_history = messages[-self.__window_size:]

    def get_messages(self, message_list: List[Message]) -> List[Message]:
        scored_points = self._get_points_by_message_list(message_list)
        scored_points = scored_points + [ScoredPoint(id=point.id, version=point.id-1, score=1.0, payload=point.payload, vector=point.vector) for point in self.__message_history]
        scored_points = unique(scored_points)
        scored_points = sorted(scored_points, key=sort_key_score)
        scored_points = scored_points[-self.__limit:]
        scored_points = sorted(scored_points, key=sort_key_id)

        return [scored_point.payload["message"] for scored_point in scored_points]

__all__ = [
    "WindowQdrantMemory"
]

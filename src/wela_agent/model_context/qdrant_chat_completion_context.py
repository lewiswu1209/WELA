
from typing import Dict
from typing import List
from typing import Callable
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from collections import deque
from autogen_core import Image
from autogen_core.models import LLMMessage
from autogen_core.model_context import ChatCompletionContext
from qdrant_client import QdrantClient
from qdrant_client.models import Distance
from qdrant_client.models import ScoredPoint
from qdrant_client.models import PointStruct
from qdrant_client.models import VectorParams

class QdrantChatCompletionContext(ChatCompletionContext):

    class StoredMessage(BaseModel):
        message: LLMMessage
        timestamp: float

    def __init__(
            self,
            qdrant_client: QdrantClient,
            collection_name: str,
            embed_func: Callable[[List[str]], List[List[float]]],
            vector_size: int = 768,
            score_threshold: Optional[float] = None
        ) -> None:
        self.__client = qdrant_client
        self.__collection_name = collection_name
        self.__embed = embed_func
        self.__vector_size = vector_size
        self.__score_threshold = score_threshold

        self.__message_buffer: deque[QdrantChatCompletionContext.StoredMessage] = deque(maxlen=5)
        self.__memory_context: List[QdrantChatCompletionContext.StoredMessage] = []

        self.__is_collection_created = False

        self.__last_query_timestamp: float | None = None
        self.__last_result: List[LLMMessage] | None = None

    def __ensure_collection(self) -> bool:
        try:
            if not self.__is_collection_created and not self.__client.collection_exists(collection_name=self.__collection_name):
                self.__client.create_collection(
                    collection_name=self.__collection_name,
                    vectors_config=VectorParams(size=self.__vector_size, distance=Distance.COSINE)
                )
            self.__is_collection_created = True
        except Exception:
            pass
        return self.__is_collection_created

    async def add_message(self, message: LLMMessage) -> None:
        if self.__ensure_collection():
            try:
                timestamp = datetime.now().timestamp()

                stored = QdrantChatCompletionContext.StoredMessage(
                    message=message,
                    timestamp=timestamp
                )

                if stored.message.type == "SystemMessage":
                    self.__memory_context.append(stored)
                else:
                    self.__memory_context.clear()
                    self.__message_buffer.append(stored)

                    text_list: List[str] = []
                    if isinstance(message.content, str):
                        text_list.append(message.content)
                    elif isinstance(message.content, list) and all(isinstance(i, (str, Image)) for i in message.content):
                        for i in message.content:
                            if isinstance(i, str):
                                text_list.append(i)

                    vectors = self.__embed(text_list)
                    for vector in vectors:
                        self.__client.upsert(
                            collection_name=self.__collection_name,
                            points=[
                                PointStruct(
                                    id=int(timestamp * 1000000),
                                    vector=vector,
                                    payload=stored.model_dump()
                                )
                            ]
                        )
            except Exception:
                pass

    async def get_messages(self) -> List[LLMMessage]:
        if not self.__message_buffer:
            return []

        last_stored = self.__message_buffer[-1]

        if self.__last_query_timestamp and last_stored.timestamp == self.__last_query_timestamp:
            if self.__last_result:
                return [stored.message for stored in self.__memory_context] + self.__last_result

        if self.__ensure_collection():
            try:
                text_list: List[str] = []
                if isinstance(last_stored.message.content, str):
                    text_list.append(last_stored.message.content)
                elif isinstance(last_stored.message.content, List[str | Image]):
                    for content_item in last_stored.message.content:
                        if isinstance(content_item, str):
                            text_list.append(content_item)

                query_vectors = self.__embed(text_list)
                query_response_points: List[ScoredPoint] = []
                for query_vector in query_vectors:
                    query_response_points.extend(
                        self.__client.query_points(
                            collection_name=self.__collection_name,
                            query=query_vector,
                            limit=20,
                            score_threshold=self.__score_threshold
                        ).points
                    )
            except Exception:
                query_response_points = []
        else:
            query_response_points = []

        history: List[QdrantChatCompletionContext.StoredMessage] = [
            QdrantChatCompletionContext.StoredMessage.model_validate(hit.payload)
            for hit in query_response_points
        ]
        for message in self.__message_buffer:
            history.append(message)

        unique_map: Dict[float, QdrantChatCompletionContext.StoredMessage] = {}
        for message in history:
            unique_map[message.timestamp] = message

        sorted_history = sorted(unique_map.values(), key=lambda x: x.timestamp)

        result = [item.message for item in sorted_history]

        self.__last_query_timestamp = last_stored.timestamp
        self.__last_result = result

        return [i.message for i in self.__memory_context] + result

    def clear(self):
        try:
            self.__client.delete_collection(self.__collection_name)
            self.__is_collection_created = False
            self.__client.create_collection(
                collection_name=self.__collection_name,
                vectors_config=VectorParams(size=self.__vector_size, distance=Distance.COSINE),
            )
            self.__is_collection_created = True
        except Exception:
            pass

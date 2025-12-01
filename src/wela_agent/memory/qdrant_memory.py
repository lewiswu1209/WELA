
import uuid

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from autogen_core import Image
from autogen_core import CancellationToken
from autogen_core.models import SystemMessage
from autogen_core.memory import Memory
from autogen_core.memory import MemoryContent
from autogen_core.memory import MemoryMimeType
from autogen_core.memory import MemoryQueryResult
from autogen_core.memory import UpdateContextResult
from autogen_core.model_context import ChatCompletionContext
from qdrant_client import QdrantClient
from qdrant_client.models import Distance
from qdrant_client.models import PointStruct
from qdrant_client.models import ScoredPoint
from qdrant_client.models import VectorParams
from qdrant_client.models import ExtendedPointId

class QdrantMemory(Memory):

    def __init__(
        self,
        qdrant_client: QdrantClient,
        collection_name: str,
        vector_size: int = 768,
        embed_func=None,
        score_threshold: Optional[float] = None
    ):
        self.__collection_name = collection_name
        self.__vector_size = vector_size
        self.__embed = embed_func
        self.__score_threshold = score_threshold

        self.__client: QdrantClient = qdrant_client
        self.__collection_was_created = False

    def __ensure_collection(self) -> bool:
        try:
            if not self.__collection_was_created and not self.__client.collection_exists(collection_name=self.__collection_name):
                self.__client.create_collection(
                    collection_name=self.__collection_name,
                    vectors_config=VectorParams(size=self.__vector_size, distance=Distance.COSINE)
                )
            self.__collection_was_created = True
        except Exception:
            pass
        return self.__collection_was_created

    async def add(self, content: MemoryContent, cancellation_token: CancellationToken | None = None) -> None:
        if self.__ensure_collection():
            try:
                if content.mime_type == MemoryMimeType.TEXT:
                    text = content.content
                    vector = self.__embed([text])[0]
                    point = PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        payload=content.model_dump(),
                    )
                    self.__client.upsert(collection_name=self.__collection_name, points=[point])
            except Exception:
                pass

    async def query(
        self,
        query: str | MemoryContent,
        cancellation_token: CancellationToken | None = None,
        **kwargs: Any,
    ) -> MemoryQueryResult:
        merged_points: Dict[ExtendedPointId, ScoredPoint] = {}
        if self.__ensure_collection():
            query_list: List[str] = []
            if isinstance(query, str):
                query_list.append(query)
            else:
                if query.mime_type == MemoryMimeType.TEXT:
                    query_list.append(query.content)
            try:
                query_vectors = self.__embed(query_list)
            except Exception:
                query_vectors = []
            for query_vector in query_vectors:
                try:
                    result = self.__client.query_points(
                        collection_name=self.__collection_name,
                        query=query_vector,
                        score_threshold = self.__score_threshold
                    )
                    for point in result.points:
                        if point.id not in merged_points:
                            merged_points[point.id] = point
                        else:
                            if point.score > merged_points[point.id].score:
                                merged_points[point.id] = point
                except Exception:
                    continue
        matches = [
            MemoryContent.model_validate(point.payload)
            for point in list(merged_points.values())
        ]
        return MemoryQueryResult(results=matches)

    async def clear(self) -> None:
        try:
            self.__client.delete_collection(self.__collection_name)
            self.__collection_was_created = False
            self.__client.create_collection(
                collection_name=self.__collection_name,
                vectors_config=VectorParams(size=self.__vector_size, distance=Distance.COSINE),
            )
            self.__collection_was_created = True
        except Exception:
            pass

    async def close(self) -> None:
        self.__client.close()

    async def update_context(
        self,
        model_context: ChatCompletionContext,
    ) -> UpdateContextResult:
        messages = await model_context.get_messages()
        if not messages:
            return UpdateContextResult(memories=MemoryQueryResult(results=[]))

        last_message = messages[-1]

        query_text_list: List[str] = []
        if isinstance(last_message.content, str):
            query_text_list.append(last_message.content)
        elif isinstance(last_message.content, list) and all(isinstance(i, (str, Image)) for i in last_message.content):
            for i in last_message.content:
                if isinstance(i, str):
                    query_text_list.append(i)

        query_results: List[MemoryContent] = []
        for query_text in query_text_list:
            results = await self.query(query_text)
            query_results.extend( results.results )

        if query_results:
            memory_strings = [f"{i}. {str(memory.content)}" for i, memory in enumerate(query_results, 1)]
            memory_context = "\nRelevant memory content:\n" + "\n".join(memory_strings)

            await model_context.add_message(SystemMessage(content=memory_context))

        return UpdateContextResult(memories=MemoryQueryResult(results=query_results))

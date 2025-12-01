
from typing import Any
from typing import List
from autogen_core import Image
from autogen_core import CancellationToken
from autogen_core.models import SystemMessage
from autogen_core.memory import Memory
from autogen_core.memory import MemoryContent
from autogen_core.memory import MemoryMimeType
from autogen_core.memory import MemoryQueryResult
from autogen_core.memory import UpdateContextResult
from autogen_core.model_context import ChatCompletionContext

from ..reranker.reranker import Reranker

class ProfilesMemory(Memory):

    def __init__(
        self,
        reranker: Reranker,
        profiles: List[str] = []
    ):
        self.__reranker = reranker
        self.__profiles: List[str] = profiles

    async def add(self, content: MemoryContent, cancellation_token: CancellationToken | None = None) -> None:
        if content.mime_type == MemoryMimeType.TEXT:
            self.__profiles.append(content.content)

    async def query(
        self,
        query: str | MemoryContent,
        cancellation_token: CancellationToken | None = None,
        **kwargs: Any,
    ) -> MemoryQueryResult:
        query_text = None
        if isinstance(query, str):
            query_text = query
        else:
            if query.mime_type == MemoryMimeType.TEXT:
                query_text = query.content
        matches = []
        if query_text:
            matches = [
                MemoryContent(content=i["document"], mime_type=MemoryMimeType.TEXT)
                for i in self.__reranker.rerank(
                    query_text,
                    self.__profiles
                )
            ]
        return MemoryQueryResult(results=matches)

    async def clear(self) -> None:
        self.__profiles.clear()

    async def close(self) -> None:
        pass

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

        query_results_list: List[MemoryContent] = []
        for query_text in query_text_list:
            query_results = await self.query(query_text)
            query_results_list.extend( query_results.results )

        if query_results_list:
            memory_strings = [f"{i}. {str(memory.content)}" for i, memory in enumerate(query_results_list, 1)]
            memory_context = "\nMore profiles about you:\n" + "\n".join(memory_strings)

            await model_context.add_message(SystemMessage(content=memory_context.strip()))

        return UpdateContextResult(memories=query_results)

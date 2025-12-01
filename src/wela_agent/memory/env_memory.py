
import time

from typing import Any
from autogen_core import CancellationToken
from autogen_core.models import SystemMessage
from autogen_core.memory import Memory
from autogen_core.memory import MemoryContent
from autogen_core.memory import MemoryMimeType
from autogen_core.memory import MemoryQueryResult
from autogen_core.memory import UpdateContextResult
from autogen_core.model_context import ChatCompletionContext

class EnvMemory(Memory):
    def __init__(self):
        super().__init__()

    async def add(self, content: MemoryContent, cancellation_token: CancellationToken | None = None) -> None:
        pass

    async def query(
        self,
        query: str | MemoryContent,
        cancellation_token: CancellationToken | None = None,
        **kwargs: Any,
    ) -> MemoryQueryResult:
        matches = [
            MemoryContent(
                content="Current time is: {}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())),
                mime_type=MemoryMimeType.TEXT
            )
        ]
        return MemoryQueryResult(results=matches)

    async def clear(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def update_context(
        self,
        model_context: ChatCompletionContext,
    ) -> UpdateContextResult:
        query_results = await self.query("")
        if query_results.results:
            memory_strings = [f"{i}. {str(memory.content)}" for i, memory in enumerate(query_results.results, 1)]
            memory_context = "\nEnvironment:\n" + "\n".join(memory_strings)
            await model_context.add_message(SystemMessage(content=memory_context.strip()))
        return UpdateContextResult(memories=query_results)

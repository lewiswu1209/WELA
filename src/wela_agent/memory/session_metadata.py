
import time
import httpx

from typing import Any
from typing import List
from autogen_core import CancellationToken
from autogen_core.models import UserMessage
from autogen_core.memory import Memory
from autogen_core.memory import MemoryContent
from autogen_core.memory import MemoryMimeType
from autogen_core.memory import MemoryQueryResult
from autogen_core.memory import UpdateContextResult
from autogen_core.model_context import ChatCompletionContext

CACHE_DURATION = 3600

class SessionMeta(Memory):

    def __init__(self):
        super().__init__()
        self.__location_cache: List[MemoryContent] | None = None
        self.__cache_time: float | None = None

    async def update_context(
        self,
        model_context: ChatCompletionContext,
    ) -> UpdateContextResult:
        """
        Update the provided model context using relevant memory content.

        Args:
            model_context: The context to update.

        Returns:
            UpdateContextResult containing relevant memories
        """
        memories = await self.query()

        memory_results = memories.results

        memory_string = "\n\n".join(memory_result.content for memory_result in memory_results)

        await model_context.add_message(
            UserMessage(
                content=memory_string,
                source=self.__class__.__name__,
            )
        )

        return UpdateContextResult(memories=memories)

    async def query(
        self,
        query: str | MemoryContent = "",
        cancellation_token: CancellationToken | None = None,
        **kwargs: Any,
    ) -> MemoryQueryResult:
        """
        Query the memory store and return relevant entries.

        Args:
            query: Query content item
            cancellation_token: Optional token to cancel operation
            **kwargs: Additional implementation-specific parameters

        Returns:
            MemoryQueryResult containing memory entries with relevance scores
        """
        _ = query, cancellation_token, kwargs
        current_time = time.time()
        results = [
            MemoryContent(
                content=f"Current time: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(current_time))}",
                mime_type=MemoryMimeType.TEXT
            )
        ]

        if (
            self.__location_cache is not None
            and self.__cache_time is not None
            and current_time - self.__cache_time < CACHE_DURATION
        ):
            results.extend(self.__location_cache)
            return MemoryQueryResult(results=results)

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                ip_resp = await client.get("https://ifconfig.me/ip")
                ip = ip_resp.text.strip()
                resp = await client.get(f"https://api.iping.cc/v1/query?ip={ip}")
                data = resp.json()
                if data.get("code") == 200:
                    loc = data["data"]
                    location_contents = [
                        MemoryContent(
                            content=f"Location：{loc.get('country', 'Unknown')}-{loc.get('region', 'Unknown')}-{loc.get('city', 'Unknown')}",
                            mime_type=MemoryMimeType.TEXT
                        ),
                        MemoryContent(
                            content=f"ISP：{loc.get('isp', 'Unknown')}",
                            mime_type=MemoryMimeType.TEXT
                        )
                    ]
                    results.extend(location_contents)
                    self.__location_cache = location_contents
                    self.__cache_time = current_time
                    return MemoryQueryResult(results=results)
                else:
                    return MemoryQueryResult(results=results)
        except httpx.HTTPError:
            return MemoryQueryResult(results=results)
        except ValueError:
            return MemoryQueryResult(results=results)
        except KeyError:
            return MemoryQueryResult(results=results)

    async def add(self, content: MemoryContent, cancellation_token: CancellationToken | None = None) -> None:
        """
        Add a new content to memory.

        Args:
            content: The memory content to add
            cancellation_token: Optional token to cancel operation
        """
        _ = content, cancellation_token
        ...

    async def clear(self) -> None:
        """Clear all entries from memory."""
        ...

    async def close(self) -> None:
        """Clean up any resources used by the memory implementation."""
        ...

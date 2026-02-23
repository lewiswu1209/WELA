
import time
import requests

from typing import Any
from autogen_core import CancellationToken
from autogen_core.models import SystemMessage
from autogen_core.memory import Memory
from autogen_core.memory import MemoryContent
from autogen_core.memory import MemoryMimeType
from autogen_core.memory import MemoryQueryResult
from autogen_core.memory import UpdateContextResult
from autogen_core.model_context import ChatCompletionContext

class SessionMeta(Memory):

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

        memory_strings = [memory_result.content for memory_result in memory_results]

        for memory_string in memory_strings:
            await model_context.add_message(SystemMessage(content=memory_string))

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
        results = [
            MemoryContent(
                content=f"Current time: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}",
                mime_type=MemoryMimeType.TEXT
            )
        ]
        try:
            ip = requests.get("https://ifconfig.me/ip").text.strip()
            resp = requests.get(f"https://api.iping.cc/v1/query?ip={ip}")
            data = resp.json()
            if data.get("code") == 200:
                loc = data["data"]
                results.extend(
                    [
                        MemoryContent(
                            content=f"Location：{loc.get('country', 'Unknown')}-{loc.get('region', 'Unknown')}-{loc.get('city', 'Unknown')}",
                            mime_type=MemoryMimeType.TEXT
                        ),
                        MemoryContent(
                            content=f"ISP：{loc.get('isp', 'Unknown')}",
                            mime_type=MemoryMimeType.TEXT
                        )
                    ]
                )
                return MemoryQueryResult(results=results)
            else:
                return MemoryQueryResult(results=results)
        except requests.exceptions.RequestException:
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

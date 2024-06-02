
from typing import Any
from typing import Dict
from duckduckgo_search import DDGS

from toolkit.toolkit import Tool

class DuckDuckGo(Tool):

    def __init__(self, proxies: Dict[str, Any] = None) -> None:
        super().__init__(
            name="duckduckgo",
            description="Use DuckDuckGo to search information on the Internet.",
            required=["query"],
            query={
                "type": "string",
                "description": "search query",
            }
        )
        self.__proxies = proxies

    def _invoke(self, **kwargs: Any) -> str:
        query = kwargs["query"]
        result = f"Here are the search results for '{query}'. If you need, you can click on the URL to explore further:\n\n"
        try:
            with DDGS(proxies=self.__proxies) as ddgs:
                for r in ddgs.text(query, max_results=5):
                    title = r["title"]
                    href = r["href"]
                    body = r["body"]
                    result += f"title: {title}\n"
                    result += f"url: {href}\n"
                    result += f"body: {body}\n"
                    result += "\n"
            return result
        except Exception as e:
            return f"{e}"

__all__ = [
    "DuckDuckGo"
]

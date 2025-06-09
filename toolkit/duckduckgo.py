
from typing import Any
from typing import Dict
from duckduckgo_search import DDGS

from wela_agents.toolkit.toolkit import Tool

class DuckDuckGo(Tool):

    def __init__(self, proxies: Dict[str, Any] = None) -> None:
        super().__init__(
            name="duckduckgo_search",
            description="Use DuckDuckGo to search for information on the Internet.",
            required=["keywords"],
            keywords={
                "type": "string",
                "description": "keywords for query, you can use advanced syntax on DuckDuckGo Search.",
            }
        )
        self.__proxies = proxies

    def _invoke(self, **kwargs: Any) -> str:
        keywords = kwargs["keywords"]
        result = f"Here are the search results for '{keywords}':\n\n"
        proxy = self.__proxies["http"] if self.__proxies else None
        try:
            with DDGS(proxy=proxy) as ddgs:
                for r in ddgs.text(keywords, safesearch="off", max_results=10):
                    title = r["title"]
                    href = r["href"]
                    body = r["body"]
                    result += f"title: {title}\n"
                    result += f"url: {href}\n"
                    result += f"body: {body}\n"
                    result += "\n"
            return result.strip()
        except Exception as e:
            return f"{e}"

__all__ = [
    "DuckDuckGo"
]

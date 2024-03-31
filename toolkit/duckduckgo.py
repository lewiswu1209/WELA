
import json

from typing import Any
from typing import Dict
from itertools import islice
from duckduckgo_search import DDGS

from toolkit import Tool

class DuckDuckGo(Tool):

    def __init__(self, proxies: Dict[str, Any] = None) -> None:
        super().__init__(
            name="duckduckgo_search",
            description="DuckDuckGo Search. Useful for when you need to answer questions about current events. Input should be a search query.",
            required=["query"],
            query={
                "type": "string",
                "description": "search query",
            }
        )
        self.__proxies = proxies

    def _invoke(self, **kwargs: Any) -> str:
        query = kwargs["query"]
        result = []
        try:
            with DDGS(proxies=self.__proxies) as ddgs:
                for r in islice(ddgs.text(query), 5):
                    r["snippet"] = r["body"]
                    r["title"] = r["title"]
                    del r["body"]
                    result.append(r)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return f"{e}"

__all__ = [
    "DuckDuckGo"
]

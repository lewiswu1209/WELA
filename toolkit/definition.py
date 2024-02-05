
from typing import Any
from typing import Dict
from itertools import islice
from duckduckgo_search import DDGS

from toolkit import Tool

class Definition(Tool):
    def __init__(self, proxies: Dict[str, Any] = None) -> None:
        super().__init__(
            name="get_definition",
            description="Get the definition of a specified keyword",
            required=["keyword"],
            keyword={
                "type": "string",
                "description": "The keyword to get the definition. It MUST be in English."
            }
        )
        self.__proxies = proxies

    def _invoke(self, **kwargs: Any) -> str:
        keyword = kwargs["keyword"]
        try:
            with DDGS(proxies=self.__proxies) as ddgs:
                for r in islice(ddgs.answers(keyword), 1):
                    return r.get("text")
        except Exception as e:
            return f"{e}"

__all__ = [
    "Definition"
]

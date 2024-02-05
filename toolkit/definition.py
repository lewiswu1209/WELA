
from typing import Any
from typing import List
from typing import Dict
from itertools import islice
from duckduckgo_search import DDGS

from toolkit import Tool

class Definition(Tool):
    def __init__(self, proxies: Dict[str, Any] = None) -> None:
        super().__init__(
            name="get_definition",
            description="Get the definition of a specified English keywords",
            required=["english_keywords"],
            english_keywords={
                "type": "string",
                "description": "The specified keywords to get the definition. The language of the keywords MUST be English."
            }
        )
        self.__proxies = proxies

    def _invoke(self, **kwargs: Any) -> str:
        keywords = kwargs["english_keywords"]
        try:
            with DDGS(proxies=self.__proxies) as ddgs:
                for r in islice(ddgs.answers(keywords), 1):
                    return r.get("text")
        except Exception as e:
            return f"{e}"

__all__ = [
    "Definition"
]

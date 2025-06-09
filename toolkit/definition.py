
from typing import Any
from typing import Dict
from itertools import islice
from duckduckgo_search import DDGS

from wela_agents.toolkit.toolkit import Tool

class Definition(Tool):
    def __init__(self, proxies: Dict[str, Any] = None) -> None:
        super().__init__(
            name="get_definition",
            description="Get the definition of a given noun",
            required=["given_noun"],
            given_noun={
                "type": "string",
                "description": "Given noun to be defined. It MUST be in English."
            }
        )
        self.__proxies = proxies

    def _invoke(self, **kwargs: Any) -> str:
        given_noun = kwargs["given_noun"]
        proxy = self.__proxies["http"] if self.__proxies else None
        try:
            with DDGS(proxy=proxy) as ddgs:
                for r in islice(ddgs.answers(given_noun), 1):
                    return r.get("text")
        except Exception as e:
            return f"{e}"

__all__ = [
    "Definition"
]

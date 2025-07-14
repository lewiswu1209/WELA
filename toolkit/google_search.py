
import requests

from typing import Any
from typing import Dict
from typing import Callable

from wela_agents.toolkit.toolkit import Tool

class GoogleSearch(Tool):

    def __init__(self, api_key: str, search_engine_id=str, proxies: Dict[str, Any] = None) -> None:
        super().__init__(
            name="google_search",
            description="Use Google to search information on the Internet.",
            required=["query"],
            query={
                "type": "string",
                "description": "Search query that will help gather comprehensive information. You can use google advanced search here.",
            }
        )
        self.__proxies = proxies
        self.__api_key = api_key
        self.__search_engine_id = search_engine_id
        self.__num_of_result = 5

    def _invoke(self, callback: Callable = None, **kwargs: Any) -> str:
        query = kwargs["query"]
        try:
            search_results = f"Here are the search results for '{query}':\n\n"

            response = requests.get(
                f"https://www.googleapis.com/customsearch/v1?q={query}&key={self.__api_key}&cx={self.__search_engine_id}&num={self.__num_of_result}",
                proxies=self.__proxies
            )
            for result in response.json().get("items", []):
                search_results += f"""=========================================
Title: {result["title"]}
-----------------------------------------
Link: {result["link"]}
-----------------------------------------
Snippet: {result["snippet"]}
=========================================
"""
            return search_results.strip()
        except Exception as e:
            return f"{e}"

__all__ = [
    "GoogleSearch"
]

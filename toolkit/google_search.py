
import time
import requests

from typing import Any
from typing import Dict
from typing import List
from typing import Callable
from urllib.parse import quote_plus

from wela_agents.toolkit.toolkit import Tool
from wela_agents.toolkit.tool_result import ToolResult
from wela_agents.reranker.reranker import Reranker

def sort_key_snippet_score(item: Dict[str, str]) -> float:
    return item["snippet_score"]

def clean_up_snippets(items: List[dict]) -> None:
    """
    Remove non-breaking space and trailing whitespace from snippets.
    :param items: The search results that contain snippets that have to be cleaned up.
    :return: Nothing, the dict is mutable and updated directly.
    """
    for item in items:
        item.update({k: v.replace('\xa0', ' ').strip() if k == 'snippet' else v for k, v in item.items()})

class GoogleSearch(Tool):

    def __init__(self, reranker: Reranker, api_key: str, search_engine_id=str, proxies: Dict[str, Any] = None) -> None:
        super().__init__(
            name="google_search",
            description="Search the custom search engine using the search term.",
            required=["topic_description", "search_term"],
            topic_description={
                "type": "string",
                "description": "detailed, descriptive text that defines the specific target, subject, or thematic focus of a planned search. Unlike short search keywords, its content provides comprehensive context about what kind of information needs to be retrieved—including relevant scopes, requirements, or contextual details—to clarify the exact objective of the search."
            },
            search_term={
                "type": "string",
                "description": "Regular query arguments can also be used, like appending site:reddit.com or after:2024-04-30. If available and/or requested, the links of the search results should be used in a follow-up request using a different tool to get the full content. Example: \"claude.ai features site:reddit.com after:2024-04-30\""
            }
        )
        self.__proxies = proxies
        self.__api_key = api_key
        self.__search_engine_id = search_engine_id
        self.__reranker = reranker

    def _invoke(self, callback: Callable = None, **kwargs: Any) -> str:
        search_term = quote_plus(kwargs["search_term"])
        topic_description = kwargs["topic_description"]
        try:
            hits = []
            startIndex = 1
            while startIndex > 0:
                time.sleep(0.2)
                response = requests.get(
                    f"https://www.googleapis.com/customsearch/v1?q={search_term}&key={self.__api_key}&cx={self.__search_engine_id}&num=10&start={startIndex}",
                    proxies=self.__proxies
                )
                if "error" in response.json():
                    startIndex = 0
                else:
                    queries = response.json()["queries"]
                    if "nextPage" in queries:
                        startIndex = queries["nextPage"][0]["startIndex"]
                    else:
                        startIndex = 0
                    hits.extend( response.json().get("items", []) )
            clean_up_snippets(hits)

            scored_snippet_hits = self.__reranker.rerank(
                query=topic_description,
                documents=[hit.get("snippet", "none") for hit in hits]
            )
            scored_snippet_hits = sorted(scored_snippet_hits, key=lambda x: x["index"])
            scored_title_hits = self.__reranker.rerank(
                query=topic_description,
                documents=[hit.get("title", "none") for hit in hits]
            )
            scored_title_hits = sorted(scored_title_hits, key=lambda x: x["index"])
            results = []
            for idx, hit in enumerate(hits):
                if scored_snippet_hits[idx]["score"] > 0.60 and scored_title_hits[idx]["score"] > 0.60:
                    results.append(
                        {
                            "title": hit["title"],
                            "link": hit["link"],
                            "snippet": hit["snippet"],
                            "title_score": scored_title_hits[idx]["score"],
                            "snippet_score": scored_snippet_hits[idx]["score"]
                        }
                    )
            sorted_results = sorted(results, key=sort_key_snippet_score, reverse=True)

            search_results = f"Here are the search results for '{search_term}':\n\n"

            for result in sorted_results:
                search_results += f"""=========================================
Title: {result["title"]}
-----------------------------------------
Link: {result["link"]}
-----------------------------------------
Snippet: {result["snippet"]}
=========================================
"""
            return ToolResult(
                result=search_results.strip()
            )
        except Exception as e:
            return ToolResult(
                result=f"{e}"
            )

__all__ = [
    "GoogleSearch"
]

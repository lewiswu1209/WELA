
import httpx

from typing import Dict
from typing import List
from typing import Union

from .reranker import Reranker

class SiliconflowReRanker(Reranker):

    def __init__(
        self,
        *,
        model_name: str,
        api_key: Union[str, None] = None,
        score_threshold: float = 0.0
    ) -> None:
        self.__model_name: str = model_name
        self.__api_key: str = api_key
        self.__score_threshold: float = score_threshold

    def rerank(self, query: str, documents: List) -> List[Dict[str, Union[int, float, str]]]:
        url = "https://api.siliconflow.cn/v1/rerank"
        payload = {
            "model": self.__model_name,
            "query": query,
            "documents": documents,
            "return_documents": True
        }
        headers = {
            "Authorization": f"Bearer {self.__api_key}",
            "Content-Type": "application/json"
        }
        response = httpx.post(url, json=payload, headers=headers)
        filtered_results = [
            {
                "index": result["index"],
                "score": result["relevance_score"],
                "document": result["document"]["text"]
            }
            for result in response.json().get("results", [])
            if result["relevance_score"] > self.__score_threshold
        ]
        sorted_results = sorted(
            filtered_results,
            key=lambda x: x["score"],
            reverse=True
        )
        return sorted_results

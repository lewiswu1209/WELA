
import httpx

from typing import List
from openai import OpenAI

from .embedding import Embedding

class OpenAIEmbedding(Embedding):
    def __init__(self,
        *,
        model_name: str,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
    ) -> None:
        self.__model_name: str = model_name
        self.__client: OpenAI = OpenAI(api_key=api_key, base_url=base_url)

    def embed(self, sentence_list: List[str]) -> List[List[float]]:
        response = self.__client.embeddings.create(model=self.__model_name, input=sentence_list)

        return [data_i.embedding for data_i in response.data]

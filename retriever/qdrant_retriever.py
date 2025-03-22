
from typing import List
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance
from qdrant_client.models import PointStruct
from qdrant_client.models import VectorParams

from retriever.retriever import Retriever
from schema.document.document import Document
from embedding.text_embedding import text_embedding

class QdrantRetriever(Retriever):

    def __init__(self, retriever_key: str, qdrant_client: QdrantClient, limit: int=10, score_threshold: Optional[float] = None) -> None:
        Retriever.__init__(self, retriever_key)
        self.__client: QdrantClient = qdrant_client
        self.__score_threshold: Optional[float] = score_threshold
        self.__limit: int = limit

        if not self.__client.collection_exists(collection_name=self.retriever_key):
            self.__client.create_collection(
                collection_name = self.retriever_key,
                vectors_config = VectorParams(size=512, distance = Distance.COSINE)
            )

    def add_documents(self, documents: List[Document]) -> None:
        count = self.__client.count(collection_name = self.retriever_key).count
        points = [
            PointStruct(
                id = count + idx,
                vector = text_embedding.embed([ str({**document["metadata"], "page_content": document["page_content"]}) ])[0],
                payload = {**document["metadata"], "page_content": document["page_content"]}
            )
            for idx, document in enumerate(documents)
        ]
        self.__client.upsert(
            collection_name = self.retriever_key,
            points = points
        )

    def retrieve(self, retrieve: str) -> List[Document]:
        vector = [float(x) for x in text_embedding.embed([retrieve])[0]]
        return [
            Document(
                page_content=point.payload["page_content"],
                payload={k: v for k, v in point.payload.items() if k != "page_content"}
            )
            for point in self.__client.query_points(
                collection_name = self.retriever_key,
                query = vector,
                with_payload = True,
                score_threshold = self.__score_threshold,
                limit = self.__limit
            ).points
        ]

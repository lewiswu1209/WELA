
from typing import Any
from typing import List

from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

class TextEmbedding:
    def __init__(self) -> None:
        self.__pipeline = pipeline(
            Tasks.sentence_embedding,
            model="iic/nlp_gte_sentence-embedding_chinese-small",
            sequence_length=512
        )

    def embed(self, text_list: List[str]) -> Any:
        return self.__pipeline(
            input={
                "source_sentence": text_list
            }
        )["text_embedding"]

text_embedding: TextEmbedding = TextEmbedding()

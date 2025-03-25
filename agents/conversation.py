
from typing import Any
from typing import Union
from typing import Optional
from typing import Generator

from agents.llm import LLMAgent
from models.model import Model
from models.openai_chat import OpenAIChat
from memory.memory import Memory
from toolkit.toolkit import Toolkit
from retriever.retriever import Retriever
from schema.prompt.openai_chat import SystemMessage
from schema.template.prompt_template import PromptTemplate

class ConversationAgent(LLMAgent):
    def __init__(self,
        *,
        model: Model,
        prompt_template: PromptTemplate,
        toolkit: Toolkit = None,
        memory: Memory = None,
        retriever: Retriever = None,
        input_key: str = "__input__",
        output_key: str = "__output__",
        max_loop: int = 5,
        max_tokens: Optional[int] = None
    ) -> None:
        assert isinstance(model, OpenAIChat), "Unsupported model type"

        super().__init__(
            model = model,
            prompt_template = prompt_template,
            toolkit = toolkit,
            input_key = input_key,
            output_key = output_key,
            max_loop = max_loop,
            max_tokens = max_tokens
        )
        self.__memory: Memory = memory
        self.__retriever: Retriever = retriever

    def predict(self, **kwargs: Any) -> Union[Any, Generator[Any, None, None]]:
        if self.__memory:
            kwargs[self.__memory.memory_key] = self.__memory.get_messages(kwargs[self.input_key])

        if self.__retriever:
            knowladge = []
            for message in kwargs[self.input_key]:
                if isinstance(message["content"], str):
                    knowladge.extend(
                        [
                            SystemMessage(
                                role = "system",
                                content = document["page_content"]
                            )
                            for document in self.__retriever.retrieve(message["content"])
                        ]
                    )
                else:
                    for content in message["content"]:
                        if content["type"] == "text":
                            knowladge.extend(
                                [
                                    SystemMessage(
                                        role = "system",
                                        content = document["page_content"]
                                    )
                                    for document in self.__retriever.retrieve(content["text"])
                                ]
                            )
            kwargs[self.__retriever.retriever_key] = knowladge

        output_message = super().predict(**kwargs)

        if isinstance(self.model, OpenAIChat):
            if not self.model.streaming:
                if self.__memory:
                    for message in kwargs[self.input_key]:
                        self.__memory.add_message(message)
                    self.__memory.add_message(output_message)
                return output_message
            def stream() -> Generator[Any, None, None]:
                final_output_messsage = None
                for message in output_message:
                    final_output_messsage = message
                    yield message
                if self.__memory:
                    for message in kwargs[self.input_key]:
                        self.__memory.add_message(message)
                    self.__memory.add_message(final_output_messsage)
            return stream()

    def reset_memory(self) -> None:
        if self.__memory:
            self.__memory.reset_memory()

__all__ = [
    "ConversationAgent"
]


from typing import Any
from typing import Union
from typing import Generator
from openai._types import NOT_GIVEN

from agents.llm import LLMAgent
from memory.memory import Memory
from toolkit.toolkit import Toolkit
from models.openai_chat import OpenAIChat
from schema.prompt.openai_chat import Message
from schema.template.prompt_template import PromptTemplate

class ConversationAgent(LLMAgent):
    def __init__(self,
        model: OpenAIChat,
        prompt_template: PromptTemplate,
        toolkit: Toolkit = None,
        memory: Memory = None,
        input_key: str = "__input__",
        output_key: str = "__output__",
        max_loop: int = 5,
    ) -> None:
        super().__init__(model, prompt_template, NOT_GIVEN, toolkit, input_key, output_key, max_loop)
        self.__memory: Memory = memory

    def predict(self, **kwargs: Any) -> Union[Message, Generator[Message, None, None], str, Generator[str, None, None]]:
        if self.__memory:
            kwargs[self.__memory.memory_key] = self.__memory.get_messages(kwargs[self.input_key])

        output_message = super().predict(**kwargs)

        if not self.model.streaming:
            if self.__memory:
                for message in kwargs[self.input_key]:
                    self.__memory.add_message(message)
                self.__memory.add_message(output_message)
            return output_message
        def stream() -> Generator[Message, None, None]:
            final_output_messsage = None
            for message in output_message:
                final_output_messsage = message
                yield message
            if self.__memory:
                for message in kwargs[self.input_key]:
                    self.__memory.add_message(message)
                self.__memory.add_message(final_output_messsage)

        return stream()

__all__ = [
    "ConversationAgent"
]

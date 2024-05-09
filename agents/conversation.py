
from typing import Any
from typing import Generator
from openai._types import NOT_GIVEN

from memory import Memory
from models import OpenAIChat
from toolkit import Toolkit
from agents.llm import LLMAgent
from schema.message import AIMessage
from schema.message import UserMessage
from prompts.messages_template import ChatTemplate

class ConversationAgent(LLMAgent):
    def __init__(self,
        model: OpenAIChat,
        chat_template: ChatTemplate,
        toolkit: Toolkit = None,
        input_key: str = "input",
        output_key: str = "output",
        max_loop: int = 5,
        memory: Memory = None
    ) -> None:
        self.__model = model
        super().__init__(self.__model, chat_template, NOT_GIVEN, toolkit, input_key, output_key, max_loop)
        self.__memory = memory

    def predict(self, **kwargs: Any) -> AIMessage | Generator:
        if self.__memory:
            kwargs[self.__memory.memory_key] = self.__memory.get_messages(kwargs[self.input_key])

        output_message = super().predict(**kwargs)

        if not self.__model.streaming:
            if self.__memory:
                self.__memory.add_message(
                    UserMessage(content=kwargs[self.input_key])
                )
                self.__memory.add_message(output_message)
            return output_message
        def stream():
            final_output_messsage = None
            for message in output_message:
                final_output_messsage = message
                yield message
            if self.__memory:
                self.__memory.add_message(
                    UserMessage(content=kwargs[self.input_key])
                )
                self.__memory.add_message(final_output_messsage)

        return stream()

__all__ = [
    "ConversationAgent"
]

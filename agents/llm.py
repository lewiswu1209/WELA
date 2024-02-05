
from typing import Any
from typing import List
from typing import Union
from typing import Optional
from typing import Generator
from openai._types import NotGiven
from openai._types import NOT_GIVEN
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall

from agents import Agent
from models import OpenAIChat
from toolkit import Toolkit
from schema.message import AIMessage
from schema.message import ToolMessage
from prompts.messages_template import ChatTemplate

class LLMAgent(Agent):

    def __init__(self,
        model: OpenAIChat,
        chat_template: ChatTemplate,
        stop: Union[Optional[str], List[str], None] | NotGiven = NOT_GIVEN,
        toolkit: Toolkit = None,
        input_key: str = "input",
        output_key: str = "output",
        max_loop: int = 5
    ) -> None:
        self.__model: OpenAIChat = model
        self.__chat_template: ChatTemplate = chat_template
        self.__stop: Union[Optional[str], List[str], None] | NotGiven = stop
        self.__toolkit: Toolkit = toolkit
        super().__init__(input_key, output_key)
        self.__max_loop: int = max_loop

    def predict(self, **kwargs: Any) -> AIMessage | Generator:
        messages = self.__chat_template.to_messages(**kwargs)
        if not self.__model.streaming:
            for i in range(self.__max_loop):
                if i == self.__max_loop - 1 or not self.__toolkit:
                    response_message = self.__model.run(messages, stop=self.__stop)
                else:
                    response_message = self.__model.run(messages, stop=self.__stop, tools=self.__toolkit.to_tools_param())
                if "tool_calls" in response_message:
                    tool_calls: List[ChatCompletionMessageToolCall] = response_message["tool_calls"]
                    for tool_call in tool_calls:
                        tool_result = self.__toolkit.run(tool_call.function)
                        messages.append(response_message)
                        messages.append(
                            ToolMessage(
                                tool_call_id=tool_call.id,
                                tool_name=tool_call.function.name,
                                tool_content=tool_result
                            )
                        )
                else:
                    break
            return response_message
        else:
            def stream():
                for i in range(self.__max_loop):
                    if i == self.__max_loop - 1 or not self.__toolkit:
                        response_message = self.__model.run(messages, stop=self.__stop)
                    else:
                        response_message = self.__model.run(messages, stop=self.__stop, tools=self.__toolkit.to_tools_param())
                    tool_calls: List[ChatCompletionMessageToolCall] = None
                    final_response_message = None
                    for chunk_message in response_message:
                        if "tool_calls" in chunk_message:
                            tool_calls = chunk_message["tool_calls"]
                            final_response_message = chunk_message
                        else:
                            yield chunk_message
                    if not tool_calls:
                        break
                    else:
                        for tool_call in tool_calls:
                            tool_result = self.__toolkit.run(tool_call.function)
                            messages.append(final_response_message)
                            messages.append(
                                ToolMessage(
                                    tool_call_id=tool_call.id,
                                    tool_name=tool_call.function.name,
                                    tool_content=tool_result
                                )
                            )
            return stream()

    def run(self, **kwargs: Any) -> str | Generator:
        prediction = self.predict(**kwargs)
        if not self.__model.streaming:
            return prediction["content"]
        def stream():
            for message in prediction:
                yield message["content"]
        return stream()

__all__ = [
    "LLMAgent"
]

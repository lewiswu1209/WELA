
from typing import Any
from typing import List
from typing import Union
from typing import Optional
from typing import Generator
from openai._types import NotGiven
from openai._types import NOT_GIVEN

from agents.agent import Agent
from toolkit.toolkit import Toolkit
from models.model import Model
from models.openai_chat import OpenAIChat
from schema.prompt.openai_chat import Message
from schema.prompt.openai_chat import ToolCall
from schema.prompt.openai_chat import Function
from schema.prompt.openai_chat import ToolMessage
from schema.template.prompt_template import PromptTemplate

class LLMAgent(Agent):

    def __init__(self,
        model: Model,
        prompt_template: PromptTemplate,
        stop: Union[Optional[str], List[str], None] = None,
        toolkit: Toolkit = None,
        input_key: str = "__input__",
        output_key: str = "__output__",
        max_loop: int = 5,
        max_tokens: Optional[int] | NotGiven = NOT_GIVEN
    ) -> None:
        self.__model: Model = model
        self.__prompt_template: PromptTemplate = prompt_template
        self.__stop: Union[Optional[str], List[str], None] = stop
        self.__toolkit: Toolkit = toolkit
        super().__init__(input_key, output_key)
        self.__max_loop: int = max_loop
        self.__max_tokens: int = max_tokens

        if self.__stop is None:
            if isinstance(self.__model, OpenAIChat):
                self.__stop = NOT_GIVEN

    @property
    def model(self) -> Model:
        return self.__model

    @property
    def toolkit(self) -> Toolkit:
        return self.__toolkit

    def predict(self, **kwargs: Any) -> Union[Any, Generator[Any, None, None]]:
        if isinstance(self.__model, OpenAIChat):
            messages: List[Message] = self.__prompt_template.format(**kwargs)
            if not self.__model.streaming:
                for i in range(self.__max_loop):
                    if i == self.__max_loop - 1 or not self.__toolkit:
                        response_message = self.__model.predict(messages, stop=self.__stop, max_tokens=self.__max_tokens)[0]
                    else:
                        response_message = self.__model.predict(messages, stop=self.__stop, max_tokens=self.__max_tokens, tools=self.__toolkit.to_tools_param())[0]
                    if "tool_calls" in response_message:
                        tool_calls: List[ToolCall] = response_message["tool_calls"]
                        messages.append(response_message)
                        for tool_call in tool_calls:
                            tool_result = self.__toolkit.run(tool_call["function"])
                            messages.append(
                                ToolMessage(
                                    content=tool_result,
                                    role="tool",
                                    tool_call_id=tool_call["id"]
                                )
                            )
                    else:
                        break
                return response_message
            else:
                def stream() -> Generator[Any, None, None]:
                    for i in range(self.__max_loop):
                        if i == self.__max_loop - 1 or not self.__toolkit:
                            response_message = self.__model.predict(messages, stop=self.__stop, max_tokens=self.__max_tokens)
                        else:
                            response_message = self.__model.predict(messages, stop=self.__stop, max_tokens=self.__max_tokens, tools=self.__toolkit.to_tools_param())
                        final_response_message = {"role": "assistant"}
                        for delta_message_list in response_message:
                            delta_message = delta_message_list[0]
                            final_response_message["role"] = delta_message["role"] if "role" in delta_message else final_response_message["role"]
                            if "content" not in final_response_message:
                                final_response_message["content"] = ""
                            if "content" in final_response_message and "content" in delta_message and delta_message["content"]:
                                final_response_message["content"] += delta_message["content"]
                            if "tool_calls" in delta_message:
                                if "tool_calls" not in final_response_message:
                                    final_response_message["tool_calls"] = [ToolCall() for _ in range(len(delta_message["tool_calls"]))]
                                for index in range(len(delta_message["tool_calls"])):
                                    final_response_message["tool_calls"][index]["id"] = delta_message["tool_calls"][index]["id"] if "id" in delta_message["tool_calls"][index] else final_response_message["tool_calls"][index]["id"]
                                    final_response_message["tool_calls"][index]["type"] = delta_message["tool_calls"][index]["type"] if "type" in delta_message["tool_calls"][index] else final_response_message["tool_calls"][index]["type"]
                                    if "function" not in final_response_message["tool_calls"][index]:
                                        final_response_message["tool_calls"][index]["function"] = Function(arguments="")
                                    final_response_message["tool_calls"][index]["function"]["name"] = delta_message["tool_calls"][index]["function"]["name"] if "name" in delta_message["tool_calls"][index]["function"] else final_response_message["tool_calls"][index]["function"]["name"]
                                    if "arguments" in delta_message["tool_calls"][index]["function"]:
                                        final_response_message["tool_calls"][index]["function"]["arguments"] += delta_message["tool_calls"][index]["function"]["arguments"]
                            else:
                                yield final_response_message
                        if "tool_calls" not in final_response_message:
                            break
                        else:
                            messages.append(final_response_message)
                            for tool_call in final_response_message["tool_calls"]:
                                tool_result = self.__toolkit.run(tool_call["function"])
                                messages.append(
                                    ToolMessage(
                                        content=tool_result,
                                        role="tool",
                                        tool_call_id=tool_call["id"]
                                    )
                                )
                return stream()
        else:
            if not self.__model.streaming:
                return "This is a test for other model"
            else:
                def stream() -> Generator[Any, None, None]:
                    for i in "This is a test for other model":
                        yield i
                return stream()

__all__ = [
    "LLMAgent"
]

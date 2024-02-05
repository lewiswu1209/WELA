
import httpx
import random

from openai import OpenAI
from openai import Stream
from openai._types import NotGiven
from openai._types import NOT_GIVEN
from openai.types.chat import ChatCompletion
from openai.types.chat import ChatCompletionChunk
from openai.types.chat import ChatCompletionToolParam

from typing import List
from typing import Union
from typing import Optional
from typing import Generator
from typing_extensions import Literal

from schema.role import Role
from schema.message import Message
from schema.message import AIMessage

class OpenAIChat:
    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        temperature: Optional[float] | NotGiven = NOT_GIVEN,
        top_p: Optional[float] | NotGiven = NOT_GIVEN,
        frequency_penalty: Optional[float] | NotGiven = NOT_GIVEN,
        presence_penalty: Optional[float] | NotGiven = NOT_GIVEN,
        stream: Optional[Literal[False]] | Literal[True] | NotGiven = NOT_GIVEN,
    ) -> None:
        self.__model: str = model
        self.__client: OpenAI = OpenAI(api_key=api_key, base_url=base_url)
        self.__temperature: Optional[float] | NotGiven = temperature
        self.__top_p: Optional[float] | NotGiven = top_p
        self.__frequency_penalty: Optional[float] | NotGiven = frequency_penalty
        self.__presence_penalty: Optional[float] | NotGiven = presence_penalty
        self.__stream: Optional[Literal[False]] | Literal[True] | NotGiven = stream

    @property
    def streaming(self) -> NotGiven | bool:
        return self.__stream

    def generate(
        self,
        messages: List[Message],
        max_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        n: Optional[int] | NotGiven = NOT_GIVEN,
        stop: Union[Optional[str], List[str], None] | NotGiven = NOT_GIVEN,
        tools: List[ChatCompletionToolParam] | NotGiven = NOT_GIVEN
    ) -> ChatCompletion | Stream[ChatCompletionChunk]:
        return self.__client.chat.completions.create(
            messages=messages,
            model=self.__model,
            stream=self.__stream,
            frequency_penalty=self.__frequency_penalty,
            max_tokens=max_tokens,
            n=n,
            presence_penalty=self.__presence_penalty,
            stop=stop,
            temperature=self.__temperature,
            top_p=self.__top_p,
            tools=tools
        )

    def predict(
        self,
        messages: List[Message],
        max_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        n: Optional[int] | NotGiven = NOT_GIVEN,
        stop: Union[Optional[str], List[str], None] | NotGiven = NOT_GIVEN,
        tools: List[ChatCompletionToolParam] | NotGiven = NOT_GIVEN
    ) -> List[Message] | Generator:
        try:
            generation = self.generate(
                messages=messages,
                max_tokens=max_tokens,
                n=n,
                stop=stop,
                tools=tools
            )
            if not self.__stream:
                return [Message.from_chat_completion_message(choice.message) for choice in generation.choices]
            def stream():
                messages = [Message(role=None, content=None) for _ in range(1 if n == NOT_GIVEN else n)]
                for chunk in generation:
                    for choice in chunk.choices:
                        index = choice.index
                        message = messages[index]
                        message.merge_chunk(choice)
                        if not choice.finish_reason:
                            yield messages
            return stream()
        except Exception as e:
            if not self.__stream:
                return [Message(role=Role.ASSISTANT, content=f"{e}")]
            else:
                def stream(e: Exception):
                    yield [Message(role=Role.ASSISTANT, content=f"{e}") for _ in range(1 if n == NOT_GIVEN else n)]
            return stream(e)

    def run(
        self,
        messages: List[Message],
        max_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        n: Optional[int] | NotGiven = NOT_GIVEN,
        stop: Union[Optional[str], List[str], None] | NotGiven = NOT_GIVEN,
        tools: List[ChatCompletionToolParam] | NotGiven = NOT_GIVEN
    ) -> AIMessage | Generator:
        if self.__stream:
            n = NOT_GIVEN
        prediction = self.predict(
            messages=messages,
            max_tokens=max_tokens,
            n=n,
            stop=stop,
            tools=tools
        )
        if not self.__stream:
            return random.choice(prediction)

        def stream():
            for messages in prediction:
                for message in messages:
                    yield message
        return stream()

__all__ = [
    "OpenAIChat"
]

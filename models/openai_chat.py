
import httpx

from typing import List
from typing import Union
from typing import Optional
from typing import Generator
from typing_extensions import Literal
from openai import OpenAI
from openai import Stream
from openai._types import NotGiven
from openai._types import NOT_GIVEN
from openai.types.chat import ChatCompletion
from openai.types.chat import ChatCompletionChunk
from openai.types.chat import ChatCompletionToolParam

from schema.prompt.openai_chat import Message
from schema.prompt.openai_chat import AIMessage

class OpenAIChat:
    def __init__(
        self,
        model_name: str = "gpt-3.5-turbo",
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        temperature: Optional[float] | NotGiven = NOT_GIVEN,
        top_p: Optional[float] | NotGiven = NOT_GIVEN,
        frequency_penalty: Optional[float] | NotGiven = NOT_GIVEN,
        presence_penalty: Optional[float] | NotGiven = NOT_GIVEN,
        stream: Optional[Literal[False]] | Literal[True] | NotGiven = NOT_GIVEN,
    ) -> None:
        self.__model_name: str = model_name
        self.__client: OpenAI = OpenAI(api_key=api_key, base_url=base_url)
        self.__temperature: Optional[float] | NotGiven = temperature
        self.__top_p: Optional[float] | NotGiven = top_p
        self.__frequency_penalty: Optional[float] | NotGiven = frequency_penalty
        self.__presence_penalty: Optional[float] | NotGiven = presence_penalty
        self.__stream: Optional[Literal[False]] | Literal[True] | NotGiven = stream

    @property
    def model_name(self) -> str:
        return self.__model_name

    @property
    def streaming(self) -> NotGiven | bool:
        return self.__stream

    def __create(
        self,
        messages: List[Message],
        max_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        n: Optional[int] | NotGiven = NOT_GIVEN,
        stop: Union[Optional[str], List[str], None] | NotGiven = NOT_GIVEN,
        tools: List[ChatCompletionToolParam] | NotGiven = NOT_GIVEN
    ) -> Union[ChatCompletion, Stream[ChatCompletionChunk]]:
        return self.__client.chat.completions.create(
            messages=messages,
            model=self.__model_name,
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
    ) -> Union[List[Message], Generator[List[Message], None, None]]:
        try:
            completions = self.__create(
                messages=messages,
                max_tokens=max_tokens,
                n=n,
                stop=stop,
                tools=tools
            )
            if not self.__stream:
                return [choice.message.to_dict() for choice in completions.choices]
            def stream():
                for chunk in completions:
                    messages = [None for _ in range(1 if n == NOT_GIVEN else n)]
                    for choice in chunk.choices:
                        index = choice.index
                        messages[index] = choice.delta.to_dict()
                        if not choice.finish_reason:
                            yield messages
            return stream()
        except Exception as e:
            if not self.__stream:
                return [AIMessage(role="assistant", content=f"{e}")]
            else:
                def stream(e: Exception):
                    yield [AIMessage(role="assistant", content=f"{e}") for _ in range(1 if n == NOT_GIVEN else n)]
            return stream(e)

__all__ = [
    "OpenAIChat"
]

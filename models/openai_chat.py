
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

from models.model import Model
from schema.prompt.openai_chat import Message
from schema.prompt.openai_chat import AIMessage

class OpenAIChat(Model[Message]):
    def __init__(
        self,
        *,
        model_name: str = "gpt-3.5-turbo",
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        temperature: Optional[float] | NotGiven = NOT_GIVEN,
        top_p: Optional[float] | NotGiven = NOT_GIVEN,
        frequency_penalty: Optional[float] | NotGiven = NOT_GIVEN,
        presence_penalty: Optional[float] | NotGiven = NOT_GIVEN,
        stream: Optional[Literal[False]] | Literal[True] | NotGiven = NOT_GIVEN
    ) -> None:
        super().__init__()
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
    def streaming(self) -> bool:
        return self.__stream if not self.__stream == NOT_GIVEN else False

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

    def predict(self, **kwargs) -> Union[List[Message], Generator[List[Message], None, None]]:
        """
        Generates predictions based on the provided messages and optional parameters.
        Args:
            **kwargs: Arbitrary keyword arguments.
                - messages (List[Message]): Required. The list of messages to generate predictions for.
                - max_tokens (Optional[int] | NotGiven): Optional. The maximum number of tokens to generate.
                - n (Optional[int] | NotGiven): Optional. The number of completions to generate.
                - stop (Union[Optional[str], List[str], None] | NotGiven): Optional. The stop sequence(s) to end the generation.
                - tools (List[ChatCompletionToolParam] | NotGiven): Optional. The tools to use for chat completion.
        Returns:
            Union[List[Message], Generator[List[Message], None, None]]:
                - If streaming is disabled, returns a list of message dictionaries.
                - If streaming is enabled, returns a generator that yields lists of delta dictionaries.
        Raises:
            AssertionError: If the "messages" key is not present in kwargs.
        """
        assert "messages" in kwargs, "messages is required"

        messages: List[Message] = kwargs["messages"]
        max_tokens: Optional[int] | NotGiven = kwargs.get("max_tokens", NOT_GIVEN)
        n: Optional[int] | NotGiven = kwargs.get("n", NOT_GIVEN)
        stop: Union[Optional[str], List[str], None] | NotGiven = kwargs.get("stop", NOT_GIVEN)
        tools: List[ChatCompletionToolParam] | NotGiven = kwargs.get("tools", NOT_GIVEN)

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

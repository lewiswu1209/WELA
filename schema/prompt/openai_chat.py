
from typing import Union
from typing import Iterable
from typing import Optional
from typing_extensions import Literal
from typing_extensions import Required
from typing_extensions import TypedDict
from openai.types.chat.chat_completion_message_tool_call_param import Function

class ImageURL(TypedDict, total=False):
    url: Required[str]
    """Either a URL of the image or the base64 encoded image data."""

    detail: Literal["auto", "low", "high"]
    """Specifies the detail level of the image.

    Learn more in the
    [Vision guide](https://platform.openai.com/docs/guides/vision/low-or-high-fidelity-image-understanding).
    """

class ImageContent(TypedDict, total=False):
    image_url: Required[ImageURL]

    type: Required[Literal["image_url"]]
    """The type of the content part."""

class TextContent(TypedDict, total=False):
    text: Required[str]
    """The text content."""

    type: Required[Literal["text"]]
    """The type of the content part."""

Content = Union[ImageContent, TextContent]

class ToolCall(TypedDict, total=False):
    id: Required[str]
    """The ID of the tool call."""

    function: Required[Function]
    """The function that the model called."""

    type: Required[Literal["function"]]
    """The type of the tool. Currently, only `function` is supported."""

class SystemMessage(TypedDict, total=False):
    content: Required[str]
    """The contents of the system message."""

    role: Required[Literal["system"]]
    """The role of the messages author, in this case `system`."""

    name: str
    """An optional name for the participant.

    Provides the model information to differentiate between participants of the same role.
    """

class UserMessage(TypedDict, total=False):
    content: Required[Union[str, Iterable[Content]]]
    """The contents of the user message."""

    role: Required[Literal["user"]]
    """The role of the messages author, in this case `user`."""

    name: str
    """An optional name for the participant.

    Provides the model information to differentiate between participants of the same role.
    """

class ToolMessage(TypedDict, total=False):
    content: Required[str]
    """The contents of the tool message."""

    role: Required[Literal["tool"]]
    """The role of the messages author, in this case `tool`."""

    tool_call_id: Required[str]
    """Tool call that this message is responding to."""

class AIMessage(TypedDict, total=False):
    role: Required[Literal["assistant"]]
    """The role of the messages author, in this case `assistant`."""

    content: Optional[str]
    """The contents of the assistant message.

    Required unless `tool_calls` or `function_call` is specified.
    """

    name: str
    """An optional name for the participant.

    Provides the model information to differentiate between participants of the same role.
    """

    tool_calls: Iterable[ToolCall]
    """The tool calls generated by the model, such as function calls."""

Message = Union[SystemMessage, UserMessage, ToolMessage, AIMessage]

__all__ = [
    "ImageURL",
    "ImageContent",
    "TextContent",
    "Content",
    "ToolCall",
    "SystemMessage",
    "UserMessage",
    "ToolMessage",
    "AIMessage",
    "Message"
]

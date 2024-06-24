
from abc import ABC
from abc import abstractmethod

from typing import Any
from typing import List
from typing import Union
from typing import Optional

from schema.prompt.openai_chat import ToolCall
from schema.prompt.openai_chat import ImageURL
from schema.prompt.openai_chat import TextContent
from schema.prompt.openai_chat import ImageContent
from schema.prompt.openai_chat import Message
from schema.prompt.openai_chat import AIMessage
from schema.prompt.openai_chat import UserMessage
from schema.prompt.openai_chat import ToolMessage
from schema.prompt.openai_chat import SystemMessage
from schema.template.prompt_template import PromptTemplate
from schema.template.prompt_template import StringPromptTemplate

class TextContentTemplate(PromptTemplate):

    def __init__(self, template: StringPromptTemplate) -> None:
        self.__template: StringPromptTemplate = template

    def format(self, **kwargs: Any) -> Any:
        if self.__template is None:
            return None
        text_content = TextContent(text=self.__template.format(**kwargs), type="text")
        return text_content

class ImageContentTemplate(PromptTemplate):

    def __init__(self, image_url: str = None, key: str = None) -> None:
        self.__key: str = key
        self.__image_url: str = image_url

    def format(self, **kwargs: Any) -> Any:
        image_content = None
        if self.__image_url:
            image_url = ImageURL(url=self.__image_url, detail="low")
            image_content = ImageContent(image_url=image_url, type="image_url")
        elif self.__key and kwargs.get(self.__key, None):
            image_url = ImageURL(url=kwargs.get(self.__key, None), detail="low")
            image_content = ImageContent(image_url=image_url, type="im/age_url")

        return image_content

class ContentTemplate(PromptTemplate):
    def __init__(self, templates: List[PromptTemplate]) -> None:
        self.__templates: List[PromptTemplate] = templates

    def format(self, **kwargs: Any) -> Any:
        content_list = []
        for template in self.__templates:
            content = template.format(**kwargs)
            if content:
                content_list.append(content)
        return content_list

class MessageTemplate(ABC):
    @abstractmethod
    def to_message(self, **kwargs: Any) -> Message:
        pass

class MessagePlaceholder:
    def __init__(self, placeholder_key: str) -> None:
        self.__placeholder_key = placeholder_key

    @property
    def placeholder_key(self) -> str:
        return self.__placeholder_key

class ToolMessageTemplate(MessageTemplate):
    def __init__(self, template: PromptTemplate, tool_call_id: str) -> None:
        self.__template = template
        self.__tool_call_id = tool_call_id

    def to_message(self, **kwargs: Any) -> AIMessage:
        if self.__tool_call_id:
            return ToolMessage(role="tool", content=self.__template.format(**kwargs), tool_call_id=self.__tool_call_id)
        else:
            return ToolMessage(role="tool", content=self.__template.format(**kwargs))

class AIMessageTemplate(MessageTemplate):

    def __init__(
        self,
        template: StringPromptTemplate = None,
        name: str = None,
        tool_calls: Optional[List[ToolCall]] = None
    ) -> None:
        self.__template = template
        self.__name = name
        self.__tool_calls = tool_calls

    def to_message(self, **kwargs: Any) -> AIMessage:
        message = AIMessage(role="assistant")
        if self.__template:
            message["content"] = self.__template.format(**kwargs)
        if self.__name:
            message["name"] = self.__name
        if self.__tool_calls:
            message["tool_calls"] = self.__tool_calls
        return message

class SystemMessageTemplate(MessageTemplate):

    def __init__(
        self,
        template: StringPromptTemplate,
        name: str = None
    ) -> None:
        self.__template = template
        self.__name = name

    def to_message(self, **kwargs: Any) -> Message:
        if self.__name:
            return SystemMessage(
                content=self.__template.format(**kwargs),
                role="system",
                name=self.__name
            )
        else:
            return SystemMessage(
                content=self.__template.format(**kwargs),
                role="system"
            )

class UserMessageTemplate(MessageTemplate):

    def __init__(
        self,
        template: Union[PromptTemplate, ContentTemplate],
        name: str = None
    ) -> None:
        self.__template = template
        self.__name = name

    def to_message(self, **kwargs: Any) -> Message:
        if self.__name:
            return UserMessage(
                content=self.__template.format(**kwargs),
                role="user",
                name=self.__name
            )
        else:
            return UserMessage(
                content=self.__template.format(**kwargs),
                role="user"
            )

class ChatTemplate(PromptTemplate):

    def __init__(self, message_template_list: List[MessageTemplate]) -> None:
        self.__message_template_list: List[MessageTemplate] = []
        for message_template in message_template_list:
            self.__message_template_list.append(message_template)

    def format(self, **kwargs: Any) -> Any:
        messages = []
        for message_template in self.__message_template_list:
            if isinstance(message_template, MessagePlaceholder):
                messages.extend(kwargs.get(message_template.placeholder_key))
            elif isinstance(message_template, MessageTemplate):
                message = message_template.to_message(**kwargs)
                messages.append(message)
        return messages

__all__ = [
    "TextContentTemplate",
    "ImageContentTemplate",
    "ContentTemplate",
    "MessageTemplate",
    "MessagePlaceholder",
    "ToolMessageTemplate",
    "AIMessageTemplate",
    "SystemMessageTemplate",
    "UserMessageTemplate",
    "ChatTemplate"
]


from abc import ABC
from abc import abstractmethod

from typing import Any
from typing import List
from typing import Optional
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall

from schema.message import Message
from schema.message import AIMessage
from schema.message import UserMessage
from schema.message import ToolMessage
from schema.message import SystemMessage
from prompts.prompt_template import PromptTemplate
from schema.message_placeholder import MessagePlaceholder

class MessageTemplate(ABC):

    def __init__(
            self,
            template: PromptTemplate,
            name: Optional[str] = None,
            tool_calls: Optional[List[ChatCompletionMessageToolCall]] = None
        ) -> None:
        self._prompt_template: PromptTemplate = template
        self._name: Optional[str] = name
        self._tool_calls: Optional[List[ChatCompletionMessageToolCall]] = tool_calls

    @abstractmethod
    def to_message(self, **kwargs: Any) -> Message:
        pass

class ToolMessageTemplate(MessageTemplate):

    def __init__(self, name: str, template: PromptTemplate) -> None:
        super().__init__(template, name, None)

    def to_message(self, **kwargs: Any) -> AIMessage:
        return ToolMessage(content=self._prompt_template.format(**kwargs), name=self._name)

class AIMessageTemplate(MessageTemplate):

    def __init__(self, template: PromptTemplate = None, tool_calls: Optional[List[ChatCompletionMessageToolCall]] = None) -> None:
        super().__init__(template, None, tool_calls)

    def to_message(self, **kwargs: Any) -> AIMessage:
        return AIMessage(content=self._prompt_template.format(**kwargs), tool_calls=self._tool_calls)

class SystemMessageTemplate(MessageTemplate):

    def __init__(self, template: PromptTemplate) -> None:
        super().__init__(template, None, None)

    def to_message(self, **kwargs: Any) -> Message:
        return SystemMessage(content=self._prompt_template.format(**kwargs))

class UserMessageTemplate(MessageTemplate):

    def __init__(self, template: PromptTemplate) -> None:
        super().__init__(template, None, None)

    def to_message(self, **kwargs: Any) -> Message:
        return UserMessage(content=self._prompt_template.format(**kwargs))

class ChatTemplate():

    def __init__(self, message_template_list: List[MessageTemplate]) -> None:
        self.__message_template_list: List[MessageTemplate] = []
        for message_template in message_template_list:
            self.__message_template_list.append(message_template)

    def to_messages(self, **kwargs: Any) -> List[Message]:
        messages = []
        for message_template in self.__message_template_list:
            if isinstance(message_template, MessagePlaceholder):
                messages.extend(kwargs.get(message_template.placeholder_key))
            elif isinstance(message_template, MessageTemplate):
                message = message_template.to_message(**kwargs)
                messages.append(message)
        return messages

__all__ = [
    "ChatTemplate",
    "MessageTemplate",
    "AIMessageTemplate",
    "UserMessageTemplate",
    "ToolMessageTemplate",
    "SystemMessageTemplate",
]

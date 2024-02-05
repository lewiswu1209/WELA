
from typing import Dict
from typing import List
from typing import Optional

from openai.types.chat.chat_completion_chunk import Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import Function
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall

from schema.role import Role

class Message(Dict):

    def __init__(
        self,
        role: Role,
        content: str,
        tool_call_id = None,
        name: Optional[str] = None,
        tool_calls: Optional[List[ChatCompletionMessageToolCall]] = None
    ) -> None:
        self["role"] = role
        self["content"] = content
        if tool_call_id:
            self["tool_call_id"] = tool_call_id
        if name:
            self["name"] = name
        if tool_calls:
            self["tool_calls"] = tool_calls

    def merge_chunk(self, choice: Choice) -> None:
        if choice.delta.role:
            self["role"] = choice.delta.role
        if not choice.finish_reason and choice.delta.content is not None:
            if self["content"] is None:
                self["content"] = choice.delta.content
            else:
                self["content"] += choice.delta.content
        if choice.delta.tool_calls:
            if "tool_calls" not in self:
                self["tool_calls"] = [ChatCompletionMessageToolCall(id="", type="function", function=Function(name="", arguments="")) for _ in range(len(choice.delta.tool_calls))]
            for index in range(len(choice.delta.tool_calls)):
                if choice.delta.tool_calls[index].id:
                    self["tool_calls"][index].id = choice.delta.tool_calls[index].id
                if choice.delta.tool_calls[index].type:
                    self["tool_calls"][index].type = choice.delta.tool_calls[index].type
                if choice.delta.tool_calls[index].function.name:
                    self["tool_calls"][index].function.name = choice.delta.tool_calls[index].function.name
                self["tool_calls"][index].function.arguments += choice.delta.tool_calls[index].function.arguments

    @classmethod
    def from_dict(cls, message_dict: Dict) -> "Message":
        return cls(**message_dict)

    @classmethod
    def from_chat_completion_message(cls, chat_completion_message: ChatCompletionMessage) -> "Message":
        return cls(
            role = chat_completion_message.role,
            content = chat_completion_message.content,
            tool_calls = chat_completion_message.tool_calls
        )

class AIMessage(Message):
    def __init__(self, content: str, tool_calls: Optional[List[ChatCompletionMessageToolCall]] = None) -> None:
        super().__init__(role=Role.ASSISTANT, content=content, tool_calls=tool_calls)

class UserMessage(Message):
    def __init__(self, content: str) -> None:
        super().__init__(role=Role.USER, content=content)

class SystemMessage(Message):
    def __init__(self, content: str) -> None:
        super().__init__(role=Role.SYSTEM, content=content)

class ToolMessage(Message):
    def __init__(self, tool_call_id: str, tool_name: str, tool_content: str) -> None:
        super().__init__(role=Role.TOOL, tool_call_id=tool_call_id, name=tool_name, content=tool_content)

__all__ = [
    "Message",
    "AIMessage",
    "UserMessage",
    "ToolMessage",
    "SystemMessage"
]


import json

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import List
from typing import Dict
from openai.types.chat.chat_completion_message_tool_call import Function

from callback import ToolEvent
from callback import ToolCallback

class Tool(ABC):
    def __init__(self, name: str, description: str, required: List[str], **properties: Any) -> None:
        self.name: str = name
        self.description: str = description
        self.param_description: Dict = properties
        self.required: List[str] = required

    @abstractmethod
    def _invoke(self, **kwargs: Any) -> str:
        pass

    def run(self, **kwargs: Any) -> str:
        result = self._invoke(**kwargs)
        return result if result else ""

    def to_tool_param(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.param_description,
                    "required": self.required,
                },
            }
        }

class Toolkit(Dict[str, Tool]):

    def __init__(self, tools: List[Tool], callback: ToolCallback = None) -> None:
        for i in tools:
            self[i.name] = i
        self.__callback = callback

    def run(self, function: Function) -> str:
        tool = self[function.name]
        arguments = json.loads(function.arguments)
        if self.__callback:
            event = ToolEvent(function.name, arguments)
            self.__callback.before_tool_call(event)
        result = tool.run(**arguments)
        if self.__callback:
            event = ToolEvent(function.name, arguments, result)
            self.__callback.after_tool_call(event)
        return result

    def to_tools_param(self) -> List[Dict[str, Any]]:
        return [tool.to_tool_param() for tool in self.values()]

__all__ = [
    "Tool",
    "Toolkit"
]

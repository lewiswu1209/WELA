
import json

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List

from callback.event import ToolEvent
from callback.callback import ToolCallback
from schema.prompt.openai_chat import Function

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
        for tool in tools:
            self[tool.name] = tool
        self.__callback = callback

    def add_tool(self, tool: Tool) -> None:
        self[tool.name] = tool

    def set_callback(self, callback: ToolCallback) -> None:
        self.__callback = callback

    def run(self, function: Function) -> str:
        tool_name = function.get("name")
        arguments_str = function.get("arguments")

        try:
            arguments = json.loads(arguments_str)
        except json.JSONDecodeError:
            return "Error: Invalid JSON format for arguments."

        if tool_name not in self:
            return f"Error: Tool '{tool_name}' not found."

        tool = self[tool_name]

        if self.__callback:
            event = ToolEvent(tool_name, arguments)
            self.__callback.before_tool_call(event)

        try:
            result = tool.run(**arguments)
        except Exception as e:
            return f"Error: An error occurred while running the tool - {str(e)}"

        if self.__callback:
            event = ToolEvent(tool_name, arguments, result)
            self.__callback.after_tool_call(event)

        return result

    def to_tools_param(self) -> List[Dict[str, Any]]:
        return [tool.to_tool_param() for tool in self.values()]

__all__ = [
    "Tool",
    "Toolkit"
]

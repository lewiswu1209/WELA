
from callback import ToolEvent

class Callback:
    pass

class ToolCallback(Callback):

    def before_tool_call(self, event: ToolEvent) -> None:
        pass

    def after_tool_call(self, event: ToolEvent) -> None:
        pass

__all__ = [
    "ToolCallback"
]


import sys
import time

from typing import List
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal

from wela_agents.agents.meta import Meta
from wela_agents.callback.event import ToolEvent
from wela_agents.callback.callback import ToolCallback
from wela_agents.schema.prompt.openai_chat import Message

class ConversationThread(QThread, ToolCallback):

    conversation_started = pyqtSignal()
    conversation_changed = pyqtSignal(str)
    conversation_finished= pyqtSignal()
    agent_require_quit = pyqtSignal()
    set_alarm_clock = pyqtSignal(str, str)

    def __init__(self, parent: QObject = None) -> None:
        super().__init__(parent)
        self.__need_quit = False

    def set_messages(self, messages: List[Message]) -> None:
        self.__messages = messages

    def set_meta(self, meta: Meta) -> None:
        self.__meta = meta

    def reset_memory(self) -> None:
        self.__meta.reset_memory()
        self.conversation_started.emit()
        self.conversation_changed.emit("记忆已重置")
        self.conversation_finished.emit()

    def run(self) -> None:
        self.conversation_started.emit()
        response = self.__meta.predict(__input__=self.__messages)
        for token in response:
            self.conversation_changed.emit(token["content"])
        self.conversation_finished.emit()
        if self.__need_quit:
            time.sleep(2)
            self.agent_require_quit.emit()

    def before_tool_call(self, event: ToolEvent) -> None:
        if event.tool_name == "quit":
            pass
        elif event.tool_name == "set_alarm_clock":
            self.set_alarm_clock.emit(event.arguments["date_time"], event.arguments["reason"])
        else:
            self.conversation_changed.emit("我将要使用工具:`{}`".format(event.tool_name))
            for param, value in event.arguments.items():
                self.conversation_changed.emit(" - 参数`{}`的值为: `{}`".format(param, value))

    def after_tool_call(self, event: ToolEvent) -> None:
        if event.tool_name == "quit":
            self.__need_quit = True
        else:
            self.conversation_changed.emit("工具`{}`的结果:".format(event.tool_name))
            for line in event.result.get("result", "").split("\n"):
                self.conversation_changed.emit(line)

__all__ = [
    "ConversationThread"
]

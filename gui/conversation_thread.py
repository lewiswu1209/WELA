
import time

from typing import List
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal

from agents.meta import Meta
from callback.event import ToolEvent
from callback.callback import ToolCallback
from schema.prompt.openai_chat import Message

class ConversationThread(QThread, ToolCallback):

    conversation_started = pyqtSignal()
    conversation_changed = pyqtSignal(str)
    conversation_finished= pyqtSignal()
    agent_require_quit = pyqtSignal()

    def __init__(self, parent: QObject = None) -> None:
        super().__init__(parent)
        self.__need_quit = False

    def set_messages(self, messages: List[Message]) -> None:
        self.__messages = messages

    def set_meta(self, meta: Meta) -> None:
        self.meta = meta

    def run(self) -> None:
        self.conversation_started.emit()
        response = self.meta.predict(__input__=self.__messages)
        for token in response:
            self.conversation_changed.emit(token["content"])
        self.conversation_finished.emit()
        if self.__need_quit:
            time.sleep(2)
            self.agent_require_quit.emit()

    def before_tool_call(self, event: ToolEvent) -> None:
        if event.tool_name == "quit":
            pass
        else:
            self.conversation_changed.emit("准备使用工具:{}\n参数:\n{}".format(event.tool_name, event.arguments))

    def after_tool_call(self, event: ToolEvent) -> None:
        if event.tool_name == "quit":
            self.__need_quit = True
        else:
            self.conversation_changed.emit("工具'{}'的结果:\n{}".format(event.tool_name, event.result))

__all__ = [
    "ConversationThread"
]


import time

from PyQt5.QtCore import QObject
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal

from meta import Meta
from callback import ToolEvent
from callback import ToolCallback

class ConversationThread(QThread, ToolCallback):

    conversation_started = pyqtSignal()
    conversation_changed = pyqtSignal(str)
    agent_require_quit = pyqtSignal()

    def __init__(self, parent: QObject = None) -> None:
        super().__init__(parent)
        self.__need_quit = False

    def set_text(self, text: str) -> None:
        self.text = text

    def set_meta(self, meta: Meta) -> None:
        self.meta = meta

    def run(self) -> None:
        self.conversation_started.emit()
        response = self.meta.run(self.text)
        for token in response:
            self.conversation_changed.emit(token)
        if self.__need_quit:
            time.sleep(2)
            self.agent_require_quit.emit()

    def before_tool_call(self, event: ToolEvent) -> None:
        if event.tool_name == "duckduckgo_search":
            self.conversation_changed.emit("正在搜索\"{}\"".format(event.arguments.get("query")))
        elif event.tool_name == "get_definition":
            self.conversation_changed.emit("正在查找\"{}\"的定义".format(event.arguments.get("english_keywords")))
        elif event.tool_name == "browser":
            self.conversation_changed.emit("正在浏览网页:{}".format(event.arguments.get("url")))
        elif event.tool_name =="quit":
            pass
        else:
            self.conversation_changed.emit("准备使用工具:{}\n参数:{}\n".format(event.tool_name, event.arguments))

    def after_tool_call(self, event: ToolEvent) -> None:
        if event.tool_name == "quit":
            self.__need_quit = True
        else:
            self.conversation_changed.emit("结果:{}".format(event.result))


import os
import sys
import random
import asyncio

from PIL import ImageGrab
from typing import List
from typing import Union
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QMovie
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QShowEvent
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QSystemTrayIcon
from autogen_core import Image as AGImage
from autogen_core import CancellationToken
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import BaseAgentEvent
from autogen_agentchat.messages import BaseChatMessage
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.messages import ThoughtEvent
from autogen_agentchat.messages import BaseAgentEvent
from autogen_agentchat.messages import BaseChatMessage
from autogen_agentchat.messages import ToolCallRequestEvent
from autogen_agentchat.messages import ToolCallExecutionEvent
from autogen_agentchat.messages import ToolCallSummaryMessage
from autogen_agentchat.messages import ModelClientStreamingChunkEvent
from autogen_agentchat.conditions import TextMentionTermination

from wela_agent import Wela
from wela_agent.tools import McpWorkbench
from wela_agent.config_loader import get_app_config
from wela_gui.gui.whiteboard import Whiteboard
from wela_gui.gui.reply_window import ReplyWindow
from wela_gui.gui.user_input_dialog import UserInputDialog

class AssistantAvatar(QWidget):

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("AssistantAvatarWindow")
        self.setLayout(QVBoxLayout(self))
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

        self.__label: QLabel = None
        self.__movie: QMovie = None
        self.__update_animation("normal")

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.__quit)
        paste_to_whiteboard_action = QAction("粘贴到白板", self)
        paste_to_whiteboard_action.triggered.connect(self.__paste_to_whiteboard)
        clear_whiteboard_action = QAction("清空白板", self)
        clear_whiteboard_action.triggered.connect(self.__clear_whiteboard)
        # reset_memory_action = QAction("重置记忆", self)
        # reset_memory_action.triggered.connect(self.__reset_memory)

        self.__context_menu = QMenu(self)
        self.__context_menu.addAction(paste_to_whiteboard_action)
        self.__context_menu.addAction(clear_whiteboard_action)
        # self.__context_menu.addAction(reset_memory_action)
        self.__context_menu.addAction(exit_action)

        self.__tray_icon = QSystemTrayIcon(self)
        self.__tray_icon.setIcon(QIcon(os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), "res/icon.ico")))
        self.__tray_icon.setToolTip("Wela")
        self.__tray_icon.setContextMenu(self.__context_menu)
        self.__tray_icon.show()

        self.__input_completed = asyncio.Event()

        self.__input_text = None
        self.__output_text = ""

        self.__reply_window = ReplyWindow()
        self.__whiteboard = Whiteboard()

        self.__is_dragging = False

    def __update_animation(self, status: str) -> None:
        folder_path = os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), f"res/{status}")
        files = os.listdir(folder_path)
        file = os.path.join(folder_path, random.choice(files))
        pixmap = QPixmap(file)
        height = QApplication.desktop().availableGeometry().height() // 4
        width = int(height * pixmap.width() / pixmap.height())
        self.__movie = QMovie(file)
        self.__movie.setScaledSize(QSize(width, height))
        self.__movie.frameChanged.connect(self.__check_last_frame)
        self.__movie.start()

        if self.__label:
            self.layout().removeWidget(self.__label)
        self.__label: QLabel = QLabel(self)
        self.__label.setMovie(self.__movie)
        self.layout().addWidget(self.__label)
        self.resize(self.__label.size())

    def __check_last_frame(self, frame_number: int) -> None:
        if self.__movie.frameCount() > 0 and frame_number == self.__movie.frameCount() - 1:
            self.__movie.stop()
            self.__movie.frameChanged.disconnect(self.__check_last_frame)

    def __paste_to_whiteboard(self) -> None:
        image = AGImage(ImageGrab.grabclipboard())
        self.__whiteboard.append(image)

    def __clear_whiteboard(self) -> None:
        self.__whiteboard.clear()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        desktop_geometry = QApplication.desktop().availableGeometry()
        initial_position = QPoint()
        initial_position.setX(desktop_geometry.right() - self.width())
        initial_position.setY(desktop_geometry.bottom() - self.height())
        self.move(initial_position)

    def __quit(self) -> None:
        self.__reply_window.close()
        self.__input_text = "exit"
        self.__input_completed.set()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.__is_dragging = True
            self.__reply_window.hide()
            self.__drag_offset: QPoint = event.globalPos() - self.pos()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.__is_dragging:
            desktop_geometry = QApplication.desktop().availableGeometry()
            new_pos: QPoint = event.globalPos() - self.__drag_offset
            new_pos.setX(max(desktop_geometry.x(), min(new_pos.x(), desktop_geometry.right() - self.width())))
            new_pos.setY(max(desktop_geometry.y(), min(new_pos.y(), desktop_geometry.bottom() - self.height())))
            self.move(new_pos)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.__is_dragging = False
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            text, ok = UserInputDialog(self).getText()
            if ok:
                self.__input_text = text
                self.__input_completed.set()
        event.accept()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        self.__context_menu.exec(self.mapToGlobal(event.pos()))
        event.accept()

    async def user_input(self, prompt: str, cancellation_token: CancellationToken | None = None) -> str:
        input_text = None
        await self.__input_completed.wait()
        input_text = self.__input_text
        self.__input_text = None
        self.__input_completed.clear()
        if len(self.__whiteboard) == 0:
            input_content = input_text
        else:
            input_content = self.__whiteboard + [input_text]
        return input_content

    def assistant_output(self, message: Union[BaseAgentEvent,BaseChatMessage,TaskResult]):
        if isinstance(message, ModelClientStreamingChunkEvent):
            self.__reply_window.stop_hide_timer()
            self.__reply_window.show()
            self.__reply_window.set_border_color("LightSalmon")
            self.__output_text += message.content
            self.__reply_window.set_contents(self.__output_text)

            desktop_center = QApplication.desktop().availableGeometry().center()
            self_center = self.geometry().center()
            if self_center.x() > desktop_center.x():
                x = self.x() - self.__reply_window.width() + self.width()
            else:
                x = self.x()
            if self_center.y() > desktop_center.y():
                y = self.y() - self.__reply_window.height()
            else:
                y = self.y() + self.height()
            self.__reply_window.move(QPoint(x, y))
        elif isinstance(message, TextMessage):
            self.__output_text = ""
            self.__reply_window.set_border_color("LightSkyBlue")
            self.__reply_window.start_hide_timer()
        elif isinstance(message, ToolCallRequestEvent):
            pass
        elif isinstance(message, ToolCallExecutionEvent):
            pass
        elif isinstance(message, ToolCallSummaryMessage):
            pass
        elif isinstance(message, ThoughtEvent):
            pass

    async def async_task(self):
        config = get_app_config("config.yaml")
        memory = config.runtime["memory"]
        context = config.runtime["context"]
        model_client = config.runtime["model_client"]
        mcps: List[McpWorkbench] = config.runtime["mcp"]

        await asyncio.gather(*[mcp.start() for mcp in mcps])
        wela = Wela(
            model_client=model_client,
            workbench=mcps,
            model_context=context,
            system_prompt=config.system_prompt,
            max_tool_iterations=5,
            memory=memory,
            termination=TextMentionTermination("exit")
        )
        await wela.chat(input_func=self.user_input, output_func=self.assistant_output)
        await asyncio.gather(*[mcp.stop() for mcp in mcps])
        self.__tray_icon.hide()
        self.__tray_icon.deleteLater()
        self.close()
        QApplication.quit()

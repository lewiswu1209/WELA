
import sys
import random
import asyncio

from PIL import Image
from PIL import ImageGrab
from typing import List
from typing import Union
from pathlib import Path
from datetime import datetime
from functools import partial
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QMovie
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QShowEvent
from PyQt5.QtGui import QDropEvent
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtGui import QDragEnterEvent
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QFileInfo
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QSystemTrayIcon
from autogen_core import Image as AGImage
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.messages import ThoughtEvent
from autogen_agentchat.messages import BaseAgentEvent
from autogen_agentchat.messages import BaseChatMessage
from autogen_agentchat.messages import ToolCallRequestEvent
from autogen_agentchat.messages import ToolCallExecutionEvent
from autogen_agentchat.messages import ToolCallSummaryMessage
from autogen_agentchat.messages import ModelClientStreamingChunkEvent

from ..gui.whiteboard import Whiteboard
from ..gui.reply_window import ReplyWindow
from ..gui.user_input_dialog import UserInputDialog

emotion_map = {
    '✿': 'happiness',
    '⍣': 'sadness',
    'ꙮ': 'anger',
    '⸎': 'fear',
    '꠸': 'disgust',
    '۞': 'surprise',
    '꙾': 'sleeping'
}

class AssistantAvatar(QWidget):

    def __init__(
            self,
            user_input_message_queue: asyncio.Queue[Union[str, List[Union[str, AGImage]]]],
            parent: QWidget = None
        ) -> None:
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
        reset_memory_action = QAction("重置记忆", self)
        # reset_memory_action.triggered.connect(self.__reset_memory)

        self.__context_menu = QMenu(self)
        self.__context_menu.addAction(paste_to_whiteboard_action)
        self.__context_menu.addAction(clear_whiteboard_action)
        self.__context_menu.addAction(reset_memory_action)
        self.__context_menu.addAction(exit_action)

        self.__tray_icon = QSystemTrayIcon(self)
        icon_path = str(Path(sys.argv[0]).resolve().parent / "res/icon.ico")
        self.__tray_icon.setIcon(QIcon(icon_path))
        self.__tray_icon.setToolTip("Wela")
        self.__tray_icon.setContextMenu(self.__context_menu)
        self.__tray_icon.show()

        self.__reply_window = ReplyWindow()
        self.__whiteboard = Whiteboard()

        self.__is_dragging = False

        self.__user_input_message_queue = user_input_message_queue
        self.__output_text = ""

    def __update_animation(self, status: str) -> None:
        script_path = Path(sys.argv[0])
        script_dir = script_path.resolve().parent

        folder_path = script_dir / f"res/{status}"

        files = [file.name for file in folder_path.iterdir()]

        random_file_name = random.choice(files)
        file_path = folder_path / random_file_name

        pixmap = QPixmap(str(file_path))
        height = QApplication.desktop().availableGeometry().height() // 4
        width = int(height * pixmap.width() / pixmap.height())
        
        self.__movie = QMovie(str(file_path))
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

    def __quit(self) -> None:
        self.__reply_window.close()
        self.__user_input_message_queue.put_nowait("EXIT")

    def on_quit(self) -> None:
        self.__tray_icon.hide()
        self.__tray_icon.deleteLater()
        self.close()
        QApplication.quit()

    # def __reset_memory(self) -> None:
    #     self.__reply_window.stop_hide_timer()
    #     self.__reply_window.hide()
    #     # self.__model_context.clear()
    #     self.__reply_window.show()
    #     self.__reply_window.set_contents("记忆已清除")
    #     desktop_center = QApplication.desktop().availableGeometry().center()
    #     self_center = self.geometry().center()
    #     if self_center.x() > desktop_center.x():
    #         x = self.x() - self.__reply_window.width() + self.width()
    #     else:
    #         x = self.x()
    #     if self_center.y() > desktop_center.y():
    #         y = self.y() - self.__reply_window.height()
    #     else:
    #         y = self.y() + self.height()
    #     self.__reply_window.move(QPoint(x, y))
    #     self.__reply_window.set_border_color("LightSkyBlue")
    #     self.__reply_window.start_hide_timer()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        desktop_geometry = QApplication.desktop().availableGeometry()
        initial_position = QPoint()
        initial_position.setX(desktop_geometry.right() - self.width())
        initial_position.setY(desktop_geometry.bottom() - self.height())
        self.move(initial_position)

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
            if ok and text.strip():
                if len(self.__whiteboard) > 0:
                    whiteboard = [item for item in self.__whiteboard]
                    self.__user_input_message_queue.put_nowait(whiteboard + [text.strip()])
                    self.__whiteboard.clear()
                else:
                    self.__user_input_message_queue.put_nowait(text.strip())
        event.accept()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        self.__context_menu.exec(self.mapToGlobal(event.pos()))
        event.accept()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            files_info = [QFileInfo(url.toLocalFile()) for url in event.mimeData().urls()]
            for file_info in files_info:
                if file_info.isFile():
                    if file_info.suffix().lower() in ['png', 'jpg', 'jpeg', 'gif']:
                        event.accept()
        elif event.mimeData().hasText():
            event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            files_info = [QFileInfo(url.toLocalFile()) for url in event.mimeData().urls()]
            for file_info in files_info:
                if file_info.isFile():
                    if file_info.suffix().lower() in ['png', 'jpg', 'jpeg', 'gif']:
                        pil_image = Image.open(file_info.filePath())
                        image = AGImage(pil_image)
                        pil_image.close()
                        self.__whiteboard.append(image)
        elif event.mimeData().hasText():
            text = event.mimeData().text()
            if text:
                translate_action = QAction("翻译", self)
                translate_action.triggered.connect(partial(self.__translate, text))

                function_menu = QMenu(self)
                function_menu.addAction(translate_action)

                function_menu.exec(self.mapToGlobal(event.pos()))

    def output_fun(self, event: Union[BaseAgentEvent, BaseChatMessage, TaskResult]) -> None:
        if isinstance(event, ModelClientStreamingChunkEvent):
            self.__reply_window.stop_hide_timer()
            self.__reply_window.show()
            self.__reply_window.set_border_color("LightSalmon")

            self.__output_text += event.content
            first_char = self.__output_text[0]
            if 0 <= datetime.now().hour <= 5:
                default_status="sleeping"
            else:
                default_status="normal"
            if first_char in emotion_map:
                emotion = emotion_map.get(first_char, default_status)
            else:
                emotion = default_status
            self.__update_animation(emotion)
            self.__reply_window.set_markdown(self.__output_text[1:].lstrip())

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
        elif isinstance(event, TextMessage):
            self.__output_text = ""
            self.__reply_window.set_border_color("LightSkyBlue")
            self.__reply_window.start_hide_timer()
        elif isinstance(event, ToolCallRequestEvent):
            print(event)
        elif isinstance(event, ToolCallExecutionEvent):
            print(event)
        elif isinstance(event, ToolCallSummaryMessage):
            print(event)
        elif isinstance(event, ThoughtEvent):
            print(event)
        else:
            print(event)


import os
import random

import common

from datetime import datetime
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QMovie
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QDropEvent
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtGui import QDragEnterEvent
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QSystemTrayIcon

from gui.whiteboard import Whiteboard
from gui.widget.output_box import TextWidget
from gui.conversation_thread import ConversationThread
from gui.speech_recognition_thread import SpeechRecognitionThread
from schema.template.openai_chat import ContentTemplate
from schema.template.openai_chat import UserMessageTemplate
from schema.template.openai_chat import TextContentTemplate
from schema.template.openai_chat import ImageContentTemplate
from schema.template.prompt_template import StringPromptTemplate

class Widget(QWidget):

    def __init__(self, parent: QWidget = None) -> None:
        super(Widget, self).__init__(parent)

        self.__conversation_thread = ConversationThread()
        meta_gpt_3_5, meta_gpt_4o = common.build_meta(callback=self.__conversation_thread)
        self.__conversation_thread.set_meta_gpt_3_5(meta_gpt_3_5)
        self.__conversation_thread.set_meta_gpt_4o(meta_gpt_4o)

        self.__speech_recognition_thread = SpeechRecognitionThread()
        self.__speech_recognition_thread.record_completed.connect(self.__start_conversation)
        self.__speech_recognition_thread.start()

        self.__is_mouse_dragging = False
        self.__whiteboard = Whiteboard()

        self.setAcceptDrops(True)
        self.setLayout(QVBoxLayout(self))
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

        self.__label: QLabel = None

        if 0 <= datetime.now().hour <= 5:
            self.__change_status(status="sleeping")
        else:
            self.__change_status(status="normal")

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        board_add_clipboard_action = QAction("粘贴图像到白板", self)
        board_add_clipboard_action.triggered.connect(self.__paste_image_to_whiteboard)
        board_clear_action = QAction("清空白板", self)
        board_clear_action.triggered.connect(self.__clear_whiteboard)

        self.__context_menu = QMenu(self)
        self.__context_menu.addAction(board_clear_action)
        self.__context_menu.addAction(board_add_clipboard_action)
        self.__context_menu.addAction(exit_action)

        tray_icon = QSystemTrayIcon(self)
        tray_icon.setIcon(QIcon("res/icon.png"))
        tray_icon.setContextMenu(self.__context_menu)
        tray_icon.show()

        self.__text_widget = TextWidget()

        self.show()
        desktop_geometry = QApplication.desktop().availableGeometry()
        initial_position = QPoint()
        initial_position.setX(desktop_geometry.right() - self.width())
        initial_position.setY(desktop_geometry.bottom() - self.height())
        self.move(initial_position)

    def __change_status(self, status = "normal"):
        folder_path = f"res/{status}"
        files = os.listdir(folder_path)
        file = os.path.join(folder_path, random.choice(files))
        pixmap = QPixmap(file)
        width = 200
        height = int(width * pixmap.height() / pixmap.width())
        movie = QMovie(file)
        movie.setScaledSize(QSize(width, height))
        movie.start()

        if self.__label:
            self.layout().removeWidget(self.__label)
        self.__label: QLabel = QLabel(self)
        self.__label.setMovie(movie)
        self.layout().addWidget(self.__label)
        self.resize(self.__label.size())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.__is_mouse_dragging = True
            self.__text_widget.hide()
            self.__drag_offset: QPoint = event.globalPos() - self.pos()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.__is_mouse_dragging:
            desktop_geometry = QApplication.desktop().availableGeometry()
            new_pos: QPoint = event.globalPos() - self.__drag_offset
            new_pos.setX(max(desktop_geometry.x(), min(new_pos.x(), desktop_geometry.right() - self.width())))
            new_pos.setY(max(desktop_geometry.y(), min(new_pos.y(), desktop_geometry.bottom() - self.height())))
            self.move(new_pos)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.__is_mouse_dragging = False
        event.accept()

    def contextMenuEvent(self, event: QMouseEvent) -> None:
        self.__context_menu.exec(self.mapToGlobal(event.pos()))
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            text, ok = QInputDialog.getText(self, "输入框", "请输入一些文本:")
            if ok:
                self.__start_conversation(text)
        event.accept()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            files = [u.toLocalFile() for u in event.mimeData().urls()]
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file = url.toLocalFile()
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                encode_image = common.encode_image(file)
                self.__whiteboard.append(encode_image)

    def closeEvent(self, _) -> None:
        self.__text_widget.hide()
        self.hide()
        QApplication.quit()

    def __start_conversation(self, text: str) -> None:
        content_list = [ImageContentTemplate(image_url=encoded_image) for encoded_image in self.__whiteboard]
        content_list.append(TextContentTemplate(StringPromptTemplate(text)))
        self.__whiteboard.clear()
        input_message = UserMessageTemplate(ContentTemplate(content_list)).to_message()

        self.__conversation_thread.set_messages([input_message])
        self.__conversation_thread.agent_require_quit.connect(self.close)
        self.__conversation_thread.conversation_started.connect(self.__on_conversation_started)
        self.__conversation_thread.conversation_changed.connect(self.__on_conversation_changed)
        self.__conversation_thread.conversation_finished.connect(self.__on_conversation_finished)
        self.__conversation_thread.start()

    def __on_conversation_started(self) -> None:
        self.__text_widget.reset()
        self.__change_status(status="working")
        self.__on_conversation_changed("对方正在输入……")

    def __on_conversation_changed(self, text: str) -> None:
        self.__text_widget.set_content(text)
        self.__text_widget.show()
        desktop_center = QApplication.desktop().availableGeometry().center()
        self_center = self.geometry().center()
        if self_center.x() > desktop_center.x():
            x = self.x() - self.__text_widget.width() + self.width()
        else:
            x = self.x()
        if self_center.y() > desktop_center.y():
            y = self.y() - self.__text_widget.height()
        else:
            y = self.y() + self.height()
        self.__text_widget.move(QPoint(x, y))

    def __on_conversation_finished(self) -> None:
        if 0 <= datetime.now().hour <= 5:
            self.__change_status(status="sleeping")
        else:
            self.__change_status(status="normal")

    def __paste_image_to_whiteboard(self):
        encode_image = common.encode_clipboard_image()
        self.__whiteboard.append(encode_image)

    def __clear_whiteboard(self):
        self.__whiteboard.clear()

__all__ = [
    "Widget"
]

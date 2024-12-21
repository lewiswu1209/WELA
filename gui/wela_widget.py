
import os
import sys
import time
import random

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
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QSystemTrayIcon
from modelscope.pipelines import Pipeline

from gui.alarm import Alarm
from agents.meta import Meta
from gui.chat_box import ChatBox
from gui.whiteboard import Whiteboard
from gui.initializer import Initializer
from gui.conversation_thread import ConversationThread
from gui.speech_recognition_thread import SpeechRecognitionThread
from schema.template.openai_chat import encode_image
from schema.template.openai_chat import encode_clipboard_image
from schema.template.openai_chat import ContentTemplate
from schema.template.openai_chat import UserMessageTemplate
from schema.template.openai_chat import TextContentTemplate
from schema.template.openai_chat import ImageContentTemplate
from schema.template.openai_chat import SystemMessageTemplate
from schema.template.prompt_template import StringPromptTemplate

class WelaWidget(QWidget):

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.__is_mouse_dragging = False
        self.__is_initialize_completed = False

        self.setLayout(QVBoxLayout(self))
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

        self.__label: QLabel = None

        if 0 <= datetime.now().hour <= 5:
            self.__change_status(status="sleeping")
        else:
            self.__change_status(status="normal")

        self.__chat_box = ChatBox()

        self.show()
        desktop_geometry = QApplication.desktop().availableGeometry()
        initial_position = QPoint()
        initial_position.setX(desktop_geometry.right() - self.width())
        initial_position.setY(desktop_geometry.bottom() - self.height())
        self.move(initial_position)

        self.__initialize()

    def __initialize(self) -> None:
        self.__initialize_thread = QThread()
        self.__initializer = Initializer()
        self.__initializer.signal.meta_created.connect(self.__on_meta_created)
        self.__initializer.signal.speech_recognition_created.connect(self.__on_speech_recognition_created)
        self.__initializer.signal.whiteboard_created.connect(self.__on_whiteboard_created)
        self.__initializer.signal.chat_updated.connect(self.__on_chat_updated)
        self.__initializer.signal.initialize_completed.connect(self.__on_initialize_completed)
        self.__initializer.moveToThread(self.__initialize_thread)
        self.__initialize_thread.started.connect(self.__initializer.initialize)
        self.__chat_box.set_border_color("LightSalmon")
        self.__initialize_thread.start()

    def __change_status(self, status = "normal"):
        folder_path = os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), f"res/{status}")
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

    def __start_conversation(self, text: str) -> None:
        content_list = [ImageContentTemplate(image_url=encoded_image) for encoded_image in self.__whiteboard]
        content_list.append(TextContentTemplate(StringPromptTemplate(text)))
        self.__whiteboard.clear()
        input_message = UserMessageTemplate(ContentTemplate(content_list)).to_message()

        self.__conversation_thread.set_messages([input_message])
        self.__conversation_thread.start()

    def __paste_to_whiteboard(self):
        encoded_image = encode_clipboard_image()
        self.__whiteboard.append(encoded_image)

    def __clear_whiteboard(self):
        self.__whiteboard.clear()

    def __reset_memory(self):
        self.__conversation_thread.reset_memory()

    def __schedule(self, time_str, reason):
        self.__alarm.schedule(time_str, reason)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.__is_mouse_dragging = True
            self.__chat_box.hide()
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
        if self.__is_initialize_completed:
            self.__context_menu.exec(self.mapToGlobal(event.pos()))
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if self.__is_initialize_completed and event.button() == Qt.LeftButton:
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
                encoded_image = encode_image(file)
                self.__whiteboard.append(encoded_image)

    def closeEvent(self, _) -> None:
        self.__alarm.stop()
        self.__alarm.dump()
        self.__chat_box.hide()
        self.hide()
        QApplication.quit()

    def __on_chat_started(self) -> None:
        self.__chat_box.reset()
        self.__change_status(status="working")
        self.__on_chat_updated("对方正在输入……")
        self.__chat_box.set_border_color("LightSalmon")

    def __on_chat_updated(self, text: str) -> None:
        self.__chat_box.set_contents(text)
        self.__chat_box.show()
        desktop_center = QApplication.desktop().availableGeometry().center()
        self_center = self.geometry().center()
        if self_center.x() > desktop_center.x():
            x = self.x() - self.__chat_box.width() + self.width()
        else:
            x = self.x()
        if self_center.y() > desktop_center.y():
            y = self.y() - self.__chat_box.height()
        else:
            y = self.y() + self.height()
        self.__chat_box.move(QPoint(x, y))

    def __on_chat_finished(self) -> None:
        self.__chat_box.set_border_color("LightSkyBlue")
        if 0 <= datetime.now().hour <= 5:
            self.__change_status(status="sleeping")
        else:
            self.__change_status(status="normal")
        self.__chat_box.start_hide_timer(9000)

    def __on_alarm(self, timestamp, reason):
        date_time = time.strftime("%Y-%m-%d %H:%M", time.gmtime(timestamp))
        input_message = SystemMessageTemplate(
            StringPromptTemplate(
                "The alarm is going off. It's time to remind user to do '{reason}'."
            )
        ).to_message(date_time=date_time, reason=reason)

        self.__conversation_thread.set_messages([input_message])
        self.__conversation_thread.start()

    def __on_meta_created(self, meta: Meta) -> None:
        self.__conversation_thread = ConversationThread()
        meta.toolkit.set_callback(self.__conversation_thread)
        self.__conversation_thread.set_meta(meta)
        self.__conversation_thread.agent_require_quit.connect(self.close)
        self.__conversation_thread.conversation_started.connect(self.__on_chat_started)
        self.__conversation_thread.conversation_changed.connect(self.__on_chat_updated)
        self.__conversation_thread.conversation_finished.connect(self.__on_chat_finished)
        self.__conversation_thread.set_alarm_clock.connect(self.__schedule)

    def __on_speech_recognition_created(self, speech_recognition_pipeline: Pipeline) -> None:
        self.__speech_recognition_thread = SpeechRecognitionThread(speech_recognition_pipeline = speech_recognition_pipeline)
        self.__speech_recognition_thread.record_completed.connect(self.__start_conversation)

    def __on_whiteboard_created(self, whiteboard: Whiteboard) -> None:
        self.__whiteboard = whiteboard

    def __on_initialize_completed(self) -> None:
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        paste_to_whiteboard_action = QAction("粘贴到白板", self)
        paste_to_whiteboard_action.triggered.connect(self.__paste_to_whiteboard)
        clear_whiteboard_action = QAction("清空白板", self)
        clear_whiteboard_action.triggered.connect(self.__clear_whiteboard)
        reset_memory_action = QAction("重置记忆", self)
        reset_memory_action.triggered.connect(self.__reset_memory)

        self.__context_menu = QMenu(self)
        self.__context_menu.addAction(paste_to_whiteboard_action)
        self.__context_menu.addAction(clear_whiteboard_action)
        self.__context_menu.addAction(reset_memory_action)
        self.__context_menu.addAction(exit_action)

        tray_icon = QSystemTrayIcon(self)
        tray_icon.setIcon(QIcon(os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), "res/icon.png")))
        tray_icon.setContextMenu(self.__context_menu)
        tray_icon.show()

        self.__speech_recognition_thread.start()
        self.setAcceptDrops(True)
        self.__is_initialize_completed = True
        self.__chat_box.set_border_color("LightSkyBlue")
        self.__chat_box.start_hide_timer(3000)

        self.__alarm = Alarm(self)
        self.__alarm.alarm.connect(self.__on_alarm)
        self.__alarm.load()
        self.__alarm.start(1000)

__all__ = [
    "WelaWidget"
]

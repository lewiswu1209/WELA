
import os
import sys
import time
import random

from funasr import AutoModel
from datetime import datetime
from functools import partial
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QMovie
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QDropEvent
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtGui import QDragEnterEvent
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QLocale
from PyQt5.QtCore import QThread
from PyQt5.QtCore import QFileInfo
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QSystemTrayIcon

from gui.alarm import Alarm
from gui.chat_box import ChatBox
from gui.whiteboard import Whiteboard
from gui.initializer import Initializer
from gui.input_dialog import InputDialog
from gui.conversation_thread import ConversationThread
from gui.speech_recognition_thread import SpeechRecognitionThread
from wela_agents.agents.meta import Meta
from wela_agents.schema.template.openai_chat import encode_image
from wela_agents.schema.template.openai_chat import encode_clipboard_image
from wela_agents.schema.template.openai_chat import ContentTemplate
from wela_agents.schema.template.openai_chat import UserMessageTemplate
from wela_agents.schema.template.openai_chat import TextContentTemplate
from wela_agents.schema.template.openai_chat import ImageContentTemplate
from wela_agents.schema.template.openai_chat import SystemMessageTemplate
from wela_agents.schema.template.prompt_template import StringPromptTemplate

class WelaWidget(QWidget):

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.__is_mouse_dragging = False
        self.__is_initialize_completed = False
        self.__speech_recognition_thread = None
        self.__status = "working"
        self.__old_status = ""
        self.__timer = QTimer()

        self.setLayout(QVBoxLayout(self))
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

        self.__label: QLabel = None
        self.__movie: QMovie = None

        self.__change_status(status=self.__status)

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
        self.__initializer.signal.conversation_started.connect(self.__on_chat_started)
        self.__initializer.signal.conversation_changed.connect(self.__on_chat_updated)
        self.__initializer.signal.conversation_finished.connect(self.__on_chat_finished)
        self.__initializer.signal.initialize_completed.connect(self.__on_initialize_completed)
        self.__initializer.moveToThread(self.__initialize_thread)
        self.__initialize_thread.started.connect(self.__initializer.initialize)
        self.__initialize_thread.start()

    def __change_status(self, status = "normal") -> None:
        if status not in ["normal", "working", "sleeping", "anger", "disgust", "fear", "happiness", "sadness", "surprise"]:
            status = "normal"
        folder_path = os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), f"res/{status}")
        files = os.listdir(folder_path)
        file = os.path.join(folder_path, random.choice(files))
        pixmap = QPixmap(file)
        width = 200
        height = int(width * pixmap.height() / pixmap.width())
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

    def __check_last_frame(self, frame_number):
        if self.__movie.frameCount() > 0 and frame_number == self.__movie.frameCount() - 1:
            self.__movie.stop()
            self.__movie.frameChanged.disconnect(self.__check_last_frame)

    def __start_conversation(self, text: str) -> None:
        content_list = [ImageContentTemplate(image_url=encoded_image) for encoded_image in self.__whiteboard]
        content_list.append(TextContentTemplate(StringPromptTemplate(text)))
        self.__whiteboard.clear()
        input_message = UserMessageTemplate(ContentTemplate(content_list)).to_message()

        self.__conversation_thread.set_messages([input_message])
        self.__conversation_thread.start()

    def __paste_to_whiteboard(self) -> None:
        encoded_image = encode_clipboard_image()
        self.__whiteboard.append(encoded_image)

    def __clear_whiteboard(self) -> None:
        self.__whiteboard.clear()

    def __reset_memory(self) -> None:
        self.__conversation_thread.reset_memory()

    def __schedule(self, time_str, reason) -> None:
        self.__alarm.schedule(time_str, reason)

    def __translate(self, text: str) -> None:
        system_locale = QLocale.system()
        language = system_locale.languageToString(system_locale.language())
        if text:
            text = f'''Translate the following text to {language}:
```
{text}
```'''
            self.__start_conversation(text)

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
            text, ok = InputDialog(self).getText()
            if ok:
                self.__start_conversation(text)
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
                        encoded_image = encode_image(file_info.filePath())
                        self.__whiteboard.append(encoded_image)
        elif event.mimeData().hasText():
            text = event.mimeData().text()
            if text:
                translate_action = QAction("翻译", self)
                translate_action.triggered.connect(partial(self.__translate, text))

                function_menu = QMenu(self)
                function_menu.addAction(translate_action)

                function_menu.exec(self.mapToGlobal(event.pos()))

    def closeEvent(self, _) -> None:
        self.__alarm.stop()
        self.__alarm.dump()
        self.__chat_box.hide()
        self.hide()
        QApplication.quit()

    def __on_chat_started(self) -> None:
        self.__chat_box.reset()
        self.__status = "working"
        self.__on_chat_updated("对方正在输入……")
        self.__chat_box.set_border_color("LightSalmon")

    def __on_chat_updated(self, text: str) -> None:
        emotion_map = {
            '✿': 'happiness',
            '⍣': 'sadness',
            'ꙮ': 'anger',
            '⸎': 'fear',
            '꠸': 'disgust',
            '۞': 'surprise',
            '꙾': 'sleeping'
        }
        if text:
            first_char = text[0]
            if 0 <= datetime.now().hour <= 5:
                default_status="sleeping"
            else:
                default_status="normal"
            emotion = default_status
            if first_char in emotion_map:
                emotion = emotion_map.get(first_char, default_status)
                text = text[1:].lstrip()
            self.__status = emotion
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
        self.__chat_box.start_hide_timer(9000)
        self.__timer.stop()
        self.__timer.singleShot(10000, self.__on_status_timeout)

    def __on_alarm(self, timestamp, reason) -> None:
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

    def __on_speech_recognition_created(self, model: AutoModel) -> None:
        self.__speech_recognition_thread = SpeechRecognitionThread(model = model)
        self.__speech_recognition_thread.record_completed.connect(self.__start_conversation)

    def __on_whiteboard_created(self, whiteboard: Whiteboard) -> None:
        self.__whiteboard = whiteboard

    def __on_refresh(self) -> None:
        if self.__movie.state() == QMovie.MovieState.NotRunning:
            if self.__old_status != self.__status or random.random() < 0.1:
                self.__old_status = self.__status
                self.__change_status(status=self.__status)

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
        tray_icon.setIcon(QIcon(os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), "res/icon.ico")))
        tray_icon.setToolTip("Wela")
        tray_icon.setContextMenu(self.__context_menu)
        tray_icon.show()

        if self.__speech_recognition_thread:
            self.__speech_recognition_thread.start()
        self.setAcceptDrops(True)
        self.__is_initialize_completed = True

        self.__alarm = Alarm(self)
        self.__alarm.alarm.connect(self.__on_alarm)
        self.__alarm.refresh.connect(self.__on_refresh)
        self.__alarm.load()
        self.__alarm.start(1000)

    def __on_status_timeout(self) -> None:
        if 0 <= datetime.now().hour <= 5:
            self.__status="sleeping"
        else:
            self.__status="normal"

__all__ = [
    "WelaWidget"
]

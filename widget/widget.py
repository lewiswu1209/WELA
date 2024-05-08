
import os
import yaml
import random
import markdown
import webbrowser

from datetime import datetime
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QMovie
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QUrl
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QTextBrowser
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QSystemTrayIcon

from meta import Meta
from models import OpenAIChat
from toolkit import Quit
from toolkit import Toolkit
from toolkit import Browser
from toolkit import Definition
from toolkit import DuckDuckGo
from memory import QdrantMemory
from qdrant_client import QdrantClient
from widget.conversation_thread import ConversationThread
from widget.speech_recognition_thread import SpeechRecognitionThread

class TextWidget(QWidget):

    def __init__(self, parent=None) -> None:
        super(TextWidget, self).__init__(parent)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

        self.setLayout(QVBoxLayout())

        self.__text_edit = QTextBrowser(self)
        self.__text_edit.setReadOnly(True)
        self.__text_edit.setOpenLinks(False)
        self.__text_edit.setFont(QFont("微软雅黑", 12))
        self.__text_edit.setLineWrapMode(QTextBrowser.NoWrap)
        self.__text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.__text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.__text_edit.document().contentsChanged.connect(self.__on_contents_changed)
        self.__text_edit.anchorClicked.connect(self.__on_link_clicked)

        self.layout().addWidget(self.__text_edit)

        self.__is_max_width = False

    def __on_link_clicked(self, url: QUrl) -> None:
        webbrowser.open(url.toString())

    def __on_contents_changed(self) -> None:
        desktop_height = QApplication.desktop().availableGeometry().height()
        desktop_width = QApplication.desktop().availableGeometry().width()

        document_height = self.__text_edit.document().size().height()
        document_width = self.__text_edit.document().size().width()

        fixed_height = document_height
        fixed_width = document_width
        if document_height > desktop_height / 5:
            self.__text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            fixed_height = desktop_height / 5
            fixed_width += 15
        else:
            self.__text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        if document_width > desktop_width / 3 or self.__is_max_width:
            self.__text_edit.setLineWrapMode(QTextBrowser.WidgetWidth)
            fixed_width = desktop_width /3
            fixed_height += 15
            self.__is_max_width = True
        else:
            self.__text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.__text_edit.setFixedHeight(int(fixed_height))
        self.__text_edit.setFixedWidth(int(fixed_width))
        self.setFixedHeight(int(fixed_height) + self.layout().spacing() * 4)
        self.setFixedWidth(int(fixed_width) + self.layout().spacing() * 4)

    def set_text(self, text: str) -> None:
        html = markdown.markdown(text)
        self.__text_edit.setHtml(html)

    def reset(self) -> None:
        self.__is_max_width = False
        self.__text_edit.setLineWrapMode(QTextBrowser.NoWrap)

class Widget(QWidget):

    def __init__(self, parent: QWidget = None) -> None:
        super(Widget, self).__init__(parent)
        with open("config.yaml") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        self.__conversation_thread = ConversationThread()
        if config.get("proxy", None):
            proxies = {
                "http": config.get("proxy"),
                "https": config.get("proxy")
            }
        else:
            proxies = None
        if config.get("qdrant", None):
            if config.get("qdrant").get("type") == "cloud":
                qdrant_client = QdrantClient(
                    url=config.get("qdrant", None).get("url"),
                    api_key=config.get("qdrant", None).get("api_key")
                )
            elif config.get("qdrant").get("type") == "local":
                qdrant_client = QdrantClient(
                    path=config.get("qdrant", None).get("path")
                )
            else:
                qdrant_client = QdrantClient(":memory:")
            memory = QdrantMemory(memory_key="memory", qdrant_client=qdrant_client)
        else:
            memory = None
        toolkit = Toolkit([Quit(), Definition(proxies), DuckDuckGo(proxies), Browser()], self.__conversation_thread)
        model = OpenAIChat(stream=True, api_key=config.get("openai").get("api_key"), base_url=config.get("openai").get("base_url"))
        meta = Meta(model=model, prompt=config.get("prompt"),memory=memory, toolkit=toolkit)
        self.__conversation_thread.set_meta(meta)

        self.__speech_recognition = SpeechRecognitionThread()
        self.__speech_recognition.record_completed.connect(self.__conversation)
        self.__speech_recognition.start()

        self.__is_mouse_dragging = False

        self.setLayout(QVBoxLayout(self))
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

        self.__label: QLabel = QLabel(self)
        self.layout().addWidget(self.__label)

        if 0 <= datetime.now().hour <= 5:
            self.__change_status(status="sleeping")
        else:
            self.__change_status(status="normal")

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)

        self.__context_menu = QMenu(self)
        self.__context_menu.addAction(exit_action)

        tray_icon = QSystemTrayIcon(self)
        tray_icon.setIcon(QIcon("res/icon.png"))
        tray_icon.setContextMenu(self.__context_menu)
        tray_icon.show()

        self.__text_widget = TextWidget()

        self.show()
        desktop_geometry = QApplication.desktop().availableGeometry()
        new_pos = QPoint()
        new_pos.setX(desktop_geometry.right() - self.width())
        new_pos.setY(desktop_geometry.bottom() - self.height())
        self.move(new_pos)

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
        self.__label.setMovie(movie)
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
                self.__conversation(text)
        event.accept()

    def __conversation(self, text: str) -> None:
        self.__conversation_thread.set_text(text)
        self.__conversation_thread.agent_require_quit.connect(self.close)
        self.__conversation_thread.conversation_started.connect(self.__on_conversation_started)
        self.__conversation_thread.conversation_changed.connect(self.__on_conversation_changed)
        self.__conversation_thread.conversation_finished.connect(self.__on_conversation_finished)
        self.__conversation_thread.start()

    def closeEvent(self, _) -> None:
        self.__text_widget.hide()
        self.hide()
        QApplication.quit()

    def __on_conversation_started(self) -> None:
        self.__text_widget.reset()
        self.__change_status(status="working")
        self.__on_conversation_changed("对方正在输入……")

    def __on_conversation_changed(self, text: str) -> None:
        self.__text_widget.set_text(text)
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

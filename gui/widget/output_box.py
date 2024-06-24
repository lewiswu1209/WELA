
import markdown
import webbrowser

from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QTextBrowser
from PyQt5.QtWidgets import QApplication

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
        self.__text_edit.document().contentsChanged.connect(self.__on_content_changed)
        self.__text_edit.anchorClicked.connect(self.__on_link_clicked)

        self.layout().addWidget(self.__text_edit)

        self.__is_max_width = False

    def __on_link_clicked(self, url: QUrl) -> None:
        webbrowser.open(url.toString())

    def __on_content_changed(self) -> None:
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

    def set_content(self, text: str) -> None:
        html = markdown.markdown(text)
        self.__text_edit.setHtml(html)

    def reset(self) -> None:
        self.__is_max_width = False
        self.__text_edit.setLineWrapMode(QTextBrowser.NoWrap)

__all__ = [
    "TextWidget"
]

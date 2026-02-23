
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton

class UserInputDialog(QDialog):

    def __init__(self, parent=None) -> None:
        super(UserInputDialog, self).__init__(parent)

        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        self.setFixedSize(800, 70)
        self.setStyleSheet("background-color: #f2f2f2;")

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.__line_edit = QLineEdit()
        self.__line_edit.setPlaceholderText("输入聊天内容……")
        self.__line_edit.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #dcdcdc;
                border-radius: 5px 0 0 5px;
                padding: 5px;
                font-size: 26px;
            }
            QLineEdit:focus {
                border: 1px solid #0078d7;
            }
        """)
        self.__line_edit.setFixedHeight(60)
        self.__line_edit.setFont(QFont("Arial"))
        layout.addWidget(self.__line_edit)

        self.__ok_button = QPushButton("确定")
        self.__ok_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: #ffffff;
                border: none;
                border-radius: 0;
                padding: 5px 10px;
                font-size: 26px;
            }
            QPushButton:hover {
                background-color: #005ea6;
            }
        """)
        self.__ok_button.clicked.connect(self.accept)
        self.__ok_button.setFixedHeight(60)
        layout.addWidget(self.__ok_button)

        self.__cancel_button = QPushButton("取消")
        self.__cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: #ffffff;
                border: none;
                border-radius: 0 5px 5px 0;
                padding: 5px 10px;
                font-size: 26px;
            }
            QPushButton:hover {
                background-color: #005ea6;
            }
        """)
        self.__cancel_button.clicked.connect(self.reject)
        self.__cancel_button.setFixedHeight(60)
        layout.addWidget(self.__cancel_button)

        self.setLayout(layout)

    def getText(self):
        if self.exec_() == QDialog.Accepted:
            return self.__line_edit.text().strip(), True
        else:
            return None, False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super(UserInputDialog, self).keyPressEvent(event)

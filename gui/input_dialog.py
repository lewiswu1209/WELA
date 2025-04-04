
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton

class InputDialog(QDialog):

    def __init__(self, parent=None):
        super(InputDialog, self).__init__(parent)

        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        self.setFixedSize(400, 50)
        self.setStyleSheet("background-color: #f2f2f2;")

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.lineEdit = QLineEdit()
        # self.lineEdit.setPlaceholderText("请输入搜索内容")
        self.lineEdit.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #dcdcdc;
                border-radius: 5px 0 0 5px;
                padding: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #0078d7;
            }
        """)
        self.lineEdit.setFixedHeight(30)
        self.lineEdit.setFont(QFont("Arial", 14))
        layout.addWidget(self.lineEdit)

        self.okButton = QPushButton("确定")
        self.okButton.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: #ffffff;
                border: none;
                border-radius: 0;
                padding: 5px 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005ea6;
            }
        """)
        self.okButton.clicked.connect(self.accept)
        self.okButton.setFixedHeight(30)
        layout.addWidget(self.okButton)

        self.cancelButton = QPushButton("取消")
        self.cancelButton.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: #ffffff;
                border: none;
                border-radius: 0 5px 5px 0;
                padding: 5px 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005ea6;
            }
        """)
        self.cancelButton.clicked.connect(self.reject)
        self.cancelButton.setFixedHeight(30)
        layout.addWidget(self.cancelButton)

        self.setLayout(layout)

    def getText(self):
        if self.exec_() == QDialog.Accepted:
            return self.lineEdit.text(), True
        else:
            return "", False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super(InputDialog, self).keyPressEvent(event)


import sys

from PyQt5.QtWidgets import QApplication

from widget.widget import Widget

if __name__ == "__main__":
    app: QApplication = QApplication(sys.argv)
    widget: Widget = Widget()
    widget.show()
    app.exec_()

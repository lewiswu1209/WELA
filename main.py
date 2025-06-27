
import sys

# This is useless, just to load funasr.AutoModel in the first place, because loading it after PyQt5.QtWidgets.QApplication will cause an exception, and I don't know why
import gui.speech_recognition_thread

from PyQt5.QtWidgets import QApplication

from gui.wela_widget import WelaWidget

if __name__ == "__main__":
    application: QApplication = QApplication(sys.argv)
    widget: WelaWidget = WelaWidget()
    widget.show()
    sys.exit(application.exec_())

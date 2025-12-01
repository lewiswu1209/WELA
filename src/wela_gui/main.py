
import sys
import qasync
import asyncio

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from wela_gui.gui import AssistantAvatar

def main():
    application = QApplication(sys.argv)
    application.setQuitOnLastWindowClosed(True)

    loop = qasync.QEventLoop(application)
    asyncio.set_event_loop(loop)

    avatar = AssistantAvatar()
    avatar.show()

    QTimer.singleShot(0, lambda: asyncio.ensure_future(avatar.async_task()))

    with loop:
        try:
            loop.run_forever()
        finally:
            loop.stop()

if __name__ == "__main__":
    main()

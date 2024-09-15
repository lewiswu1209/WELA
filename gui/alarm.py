
import time

from PyQt5.QtCore import QTimer
from PyQt5.QtCore import QObject

from PyQt5.QtCore import pyqtSignal

class Alarm(QTimer):

    alarm = pyqtSignal(int, str)

    def __init__(self, parent: QObject | None = ...) -> None:
        super().__init__(parent)

        self.timeout.connect(self.__on_timer)
        self.__schedule = {}

    def __on_timer(self):
        timestamp = int(time.time())
        reason = self.__schedule.get(timestamp, None)
        if reason:
            self.alarm.emit(timestamp, reason)

    def schedule(self, time_str, reason):
        timestamp = time.mktime(time.strptime(time_str, "%Y-%m-%d %H:%M"))
        self.__schedule[timestamp] = reason

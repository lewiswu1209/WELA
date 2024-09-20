
import os
import json
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
        timestamp = int(time.mktime(time.strptime(time_str, "%Y-%m-%d %H:%M")))
        self.__schedule[timestamp] = reason

    def dump(self, path = os.environ["LOCALAPPDATA"] + "\\alarm.json"):
        with open(path, "w", encoding="utf-8") as file:
            json.dump(self.__schedule, file)

    def load(self, path = os.environ["LOCALAPPDATA"] + "\\alarm.json"):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as file:
                schedule_json = json.load(file)
                for key, value in schedule_json.items():
                    key_int = int(key)
                    timestamp = int(time.time())
                    if key_int > timestamp:
                        self.__schedule[key_int] = value
        else:
            self.__schedule = {}

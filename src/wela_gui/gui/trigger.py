
import os
import json
import time
import asyncio
import platform

from typing import Dict
from typing import List
from pathlib import Path
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import QObject

class Trigger(QTimer):
    def __init__(self, trigger_message_queue: asyncio.Queue[str] = None, parent: QObject | None = ...) -> None:
        super().__init__(parent)

        self.timeout.connect(self.__on_timer)
        self.__triggers: List[Dict] = []
        self.__trigger_message_queue = trigger_message_queue

        if platform.system() == "Windows":
            self.__path = Path(os.environ["LOCALAPPDATA"]) / "alarm.json"
        elif platform.system() == "Linux":
            self.__path = Path(os.environ["HOME"]) / ".alarm.json"

    def __on_timer(self):
        for idx in reversed(range(len(self.__triggers))):
            trigger = self.__triggers[idx]
            if trigger.get("type", None) == "alarm":
                timestamp = trigger.get("timestamp", None)
                if timestamp and time.time() > timestamp:
                    reason = trigger.get("reason", "")
                    message = f"""There is a alarm at {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))}
It's time for remind user'{reason}'"""
                    self.__trigger_message_queue.put_nowait(message)
                    del self.__triggers[idx]

    def set_alarm(self, time_str, reason):
        timestamp = int(time.mktime(time.strptime(time_str, "%Y-%m-%d %H:%M")))
        print(time_str, reason)
        self.__triggers.append(
            {
                "type": "alarm",
                "timestamp": timestamp,
                "reason": reason
            }
        )

    def dump(self) -> None:
        with open(self.__path, "w", encoding="utf-8") as file:
            json.dump(self.__triggers, file)

    def load(self) -> None:
        if self.__path.exists():
            with open(self.__path, "r", encoding="utf-8") as file:
                self.__triggers = json.load(file)

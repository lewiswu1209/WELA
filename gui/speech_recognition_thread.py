
import pyaudio
import keyboard
import threading

from typing import List
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal
from modelscope.pipelines import Pipeline

class SpeechRecognitionThread(QThread):

    record_completed = pyqtSignal(str)

    def __init__(self, parent: QObject = None, speech_recognition_pipeline: Pipeline = None) -> None:
        super().__init__(parent)
        self.__recording: bool = False
        self.__speech_recognition_pipeline = speech_recognition_pipeline
        self.__audio: pyaudio.PyAudio = pyaudio.PyAudio()
        self.__record_data: List[bytes] = []
        self.__channels: int = 1
        self.__sample_rate: int = 16000
        self.__chunk_size: int = 1024
        self.__record_finished_signal = threading.Event()

    def run(self) -> None:
        keyboard.hook_key(key="caps lock", callback=self.__on_hotkey)

    def __on_hotkey(self, event: keyboard.KeyboardEvent) -> None:
        if event.event_type == "down":
            if self.__recording:
                return
            self.__recording = True
            threading.Thread(target=self.__record).start()
        elif event.event_type == "up":
            self.__recording = False
            keyboard.press_and_release("caps lock")
            self.__record_finished_signal.wait()
            self.__process_record_data()

    def __process_record_data(self) -> None:
        res = self.__speech_recognition_pipeline(input=b"".join(self.__record_data))
        text = res[0]["text"]
        self.record_completed.emit(text)

    def __record(self) -> None:
        self.__record_finished_signal.clear()
        stream = self.__audio.open(
            channels=self.__channels,
            format=pyaudio.paInt16,
            rate=self.__sample_rate,
            input=True,
            frames_per_buffer=self.__chunk_size
        )
        self.__record_data.clear()
        while self.__recording:
            self.__record_data.append(stream.read(self.__chunk_size))
        if stream.is_active():
            stream.stop_stream()
            stream.close()
        self.__record_finished_signal.set()

__all__ = [
    "SpeechRecognitionThread"
]

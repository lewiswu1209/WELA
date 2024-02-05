
import os
import wave
import pyaudio
import keyboard
import tempfile
import threading

from typing import List
from funasr import AutoModel
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal

class SpeechRecognitionThread(QThread):

    record_completed = pyqtSignal(str)

    def __init__(self, parent: QObject = None) -> None:
        super().__init__(parent)
        self.__recording: bool = False
        self.__model: AutoModel = AutoModel(
            model="paraformer-zh",
            model_revision="v2.0.4",
            vad_model="fsmn-vad",
            vad_model_revision="v2.0.4",
            punc_model="ct-punc-c",
            punc_model_revision="v2.0.4"
        )
        self.__audio: pyaudio.PyAudio = pyaudio.PyAudio()
        self.__record_data: List[bytes] = []
        self.__channels: int = 1
        self.__sample_width: int = self.__audio.get_sample_size(pyaudio.paInt16)
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
        file_name: str = None
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        file_name = temp_file.name
        temp_file.close()
        wav_file = wave.open(file_name, "wb")
        wav_file.setnchannels(self.__channels)
        wav_file.setsampwidth(self.__sample_width)
        wav_file.setframerate(self.__sample_rate)
        wav_file.writeframes(b"".join(self.__record_data))
        wav_file.close()
        res = self.__model.generate(input=file_name)
        text = res[0]["text"]
        self.record_completed.emit(text)
        os.remove(file_name)

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

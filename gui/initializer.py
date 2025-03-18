
import os
import sys
import yaml

from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import pyqtSignal
from modelscope.pipelines import pipeline
from modelscope.pipelines import Pipeline
from modelscope.utils.constant import Tasks
from qdrant_client.http.exceptions import UnexpectedResponse

from agents.meta import Meta
from qdrant_client import QdrantClient
from gui.whiteboard import Whiteboard
from models.openai_chat import OpenAIChat
from toolkit.quit import Quit
from toolkit.toolkit import Toolkit
from toolkit.weather import Weather
from toolkit.definition import Definition
from toolkit.duckduckgo import DuckDuckGo
from toolkit.web_browser import WebBrowser
from toolkit.alarm_clock import AlarmClock
from memory.window_qdrant_memory import WindowQdrantMemory

class InitializerSignal(QObject):
    meta_created = pyqtSignal(Meta)
    speech_recognition_created = pyqtSignal(Pipeline)
    whiteboard_created = pyqtSignal(Whiteboard)
    conversation_started = pyqtSignal()
    conversation_changed = pyqtSignal(str)
    conversation_finished= pyqtSignal()
    initialize_completed = pyqtSignal()

class Initializer(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.signal = InitializerSignal()

    @pyqtSlot()
    def initialize(self):
        self.signal.conversation_started.emit()
        self.signal.conversation_changed.emit("开始初始化")
        with open(os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), "config.yaml"), encoding="utf-8") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

        self.signal.conversation_changed.emit("加载记忆模块")
        if config.get("memory", None):
            memory_key = config.get("memory").get("memory_key", "memory")
            limit = config.get("memory").get("limit", 15)
            window_size = config.get("memory").get("window_size", 5)
            score_threshold = config.get("memory").get("score_threshold", 0.6)
            if config.get("memory").get("qdrant").get("type") == "cloud":
                qdrant_client = QdrantClient(
                    url=config.get("memory").get("qdrant").get("url"),
                    api_key=config.get("memory").get("qdrant").get("api_key")
                )
            elif config.get("memory").get("qdrant").get("type") == "local":
                qdrant_client = QdrantClient(
                    path=config.get("memory").get("qdrant").get("path")
                )
            else:
                qdrant_client = QdrantClient(":memory:")

            try:
                memory = WindowQdrantMemory(
                    memory_key=memory_key, 
                    qdrant_client=qdrant_client,
                    limit=limit,
                    window_size=window_size,
                    score_threshold=score_threshold
                )
            except (UnexpectedResponse, ValueError) as _:
                self.signal.conversation_changed.emit("记忆模块加载失败，将在没有记忆模块的情况下工作")
                memory = None
        else:
            self.signal.conversation_changed.emit("未设置记忆模块，将在没有记忆模块的情况下工作")
            memory = None
        self.signal.conversation_changed.emit("加载工具箱")
        if config.get("proxy", None):
            proxies = {
                "http": config.get("proxy"),
                "https": config.get("proxy")
            }
        else:
            proxies = None
        tool_model = OpenAIChat(model_name=config.get("openai").get("model_name"), stream=False, api_key=config.get("openai").get("api_key"), base_url=config.get("openai").get("base_url"))
        toolkit = Toolkit([AlarmClock(), Quit(), Weather(), Definition(proxies), DuckDuckGo(proxies), WebBrowser(tool_model, proxies)], None)
        self.signal.conversation_changed.emit("加载人物性格")
        meta_model = OpenAIChat(model_name=config.get("openai").get("model_name"),stream=True, api_key=config.get("openai").get("api_key"), base_url=config.get("openai").get("base_url"))
        meta = Meta(model=meta_model, prompt=config.get("prompt"),memory=memory, toolkit=toolkit)
        self.signal.meta_created.emit(meta)
        self.signal.conversation_changed.emit("加载语音识别")
        try:
            speech_recognition_pipeline = pipeline(
                task=Tasks.auto_speech_recognition,
                model='iic/speech_paraformer_asr_nat-zh-cn-16k-common-vocab8358-tensorflow1',
                vad_model='iic/speech_fsmn_vad_zh-cn-16k-common-pytorch',
                punc_model='iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch'
            )
            self.signal.speech_recognition_created.emit(speech_recognition_pipeline)
        except Exception as _:
            self.signal.conversation_changed.emit("语音识别加载失败，语音识别将无法使用")
        self.signal.conversation_changed.emit("加载白板")
        self.signal.whiteboard_created.emit(Whiteboard())
        self.signal.conversation_changed.emit("加载通知图标")
        self.signal.initialize_completed.emit()
        self.signal.conversation_changed.emit("初始化完成")
        self.signal.conversation_finished.emit()

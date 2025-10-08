
import io
import os
import sys
import yaml

from funasr import AutoModel
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import pyqtSignal
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from pexpect.popen_spawn import PopenSpawn

from toolkit.quit import Quit
from toolkit.weather import Weather
from toolkit.term.term import TermReader
from toolkit.term.term import TermWriter
from toolkit.term.term import TermControl
from toolkit.write_file import WriteFile
from toolkit.screen_shot import ScreenShot
from toolkit.web_browser import WebBrowser
from toolkit.web_browser import WebBrowserScreenshot
from toolkit.alarm_clock import AlarmClock
from toolkit.google_search import GoogleSearch
from gui.whiteboard import Whiteboard
from gui.speech_recognition_thread import model
from wela_agents.agents.meta import Meta
from wela_agents.models.openai_chat import OpenAIChat
from wela_agents.toolkit.toolkit import Toolkit
from wela_agents.embedding.text_embedding import TextEmbedding
from wela_agents.embedding.openai_embedding import OpenAIEmbedding
from wela_agents.retriever.qdrant_retriever import QdrantRetriever
from wela_agents.reranker.siliconflow_reranker import SiliconflowReRanker
from wela_agents.memory.openai_chat.window_qdrant_memory import WindowQdrantMemory

class InitializerSignal(QObject):
    meta_created = pyqtSignal(Meta)
    speech_recognition_created = pyqtSignal(AutoModel)
    whiteboard_created = pyqtSignal(Whiteboard)
    conversation_started = pyqtSignal()
    conversation_changed = pyqtSignal(str)
    conversation_finished= pyqtSignal()
    initialize_completed = pyqtSignal()

class Initializer(QObject):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.signal = InitializerSignal()

    @pyqtSlot()
    def initialize(self) -> None:
        self.signal.conversation_started.emit()
        self.signal.conversation_changed.emit("开始初始化")
        with open(os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), "config.yaml"), encoding="utf-8") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

        embedding = None

        self.signal.conversation_changed.emit("加载记忆模块")
        if config.get("memory", None):
            memory_key = config.get("memory").get("memory_key", "memory")
            limit = config.get("memory").get("limit", 15)
            window_size = config.get("memory").get("window_size", 5)
            score_threshold = config.get("memory").get("score_threshold", 0.6)
            if config.get("retriever").get("embedding").get("type") == "openai":
                embedding = OpenAIEmbedding(
                    model_name=config.get("retriever").get("embedding").get("model_name"),
                    base_url=config.get("retriever").get("embedding").get("base_url"),
                    api_key=config.get("retriever").get("embedding").get("api_key")
                )
            else:
                embedding = TextEmbedding(model="iic/nlp_gte_sentence-embedding_chinese-small") if embedding is None else embedding
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
                    embedding=embedding,
                    qdrant_client=qdrant_client,
                    vector_size=config.get("memory").get("vector_size"),
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

        self.signal.conversation_changed.emit("加载知识库")
        if config.get("retriever", None):
            retriever_key = config.get("retriever").get("retriever_key", "retriever")
            limit = config.get("retriever").get("limit", 4)
            score_threshold = config.get("retriever").get("score_threshold", 0.6)
            if config.get("retriever").get("embedding").get("type") == "openai":
                embedding = OpenAIEmbedding(
                    model_name=config.get("retriever").get("embedding").get("model_name"),
                    base_url=config.get("retriever").get("embedding").get("base_url"),
                    api_key=config.get("retriever").get("embedding").get("api_key")
                )
            else:
                embedding = TextEmbedding(model="iic/nlp_gte_sentence-embedding_chinese-small") if embedding is None else embedding
            if config.get("retriever").get("qdrant").get("type") == "cloud":
                qdrant_client = QdrantClient(
                    url=config.get("retriever").get("qdrant").get("url"),
                    api_key=config.get("retriever").get("qdrant").get("api_key")
                )
            elif config.get("retriever").get("qdrant").get("type") == "local":
                qdrant_client = QdrantClient(
                    path=config.get("retriever").get("qdrant").get("path")
                )
            else:
                qdrant_client = QdrantClient(":memory:")
            try:
                retriever = QdrantRetriever(retriever_key=retriever_key, embedding=embedding, qdrant_client=qdrant_client, vector_size=config.get("retriever").get("vector_size"))
            except (UnexpectedResponse, ValueError):
                self.signal.conversation_changed.emit("知识库加载失败，将在没有知识库的情况下工作")
                retriever = None
        else:
            self.signal.conversation_changed.emit("未设置知识库，将在没有知识库的情况下工作")
            retriever = None

        self.signal.conversation_changed.emit("加载工具箱")
        proxy = config.get("proxy", None)
        if proxy:
            proxies = {
                "http": proxy,
                "https": proxy
            }
        else:
            proxies = None
        tool_model = OpenAIChat(model_name=config.get("openai").get("model_name"),stream=False, api_key=config.get("openai").get("api_key"), base_url=config.get("openai").get("base_url"))
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        shell = PopenSpawn("cmd.exe", encoding="gbk")
        reranker = SiliconflowReRanker(
            model_name=config.get("google_custom_search").get("reranker").get("model_name"),
            api_key=config.get("google_custom_search").get("reranker").get("api_key")
        )
        toolkit = Toolkit(
            [
                ScreenShot(),
                AlarmClock(),
                Quit(),
                Weather(),
                GoogleSearch(reranker, config.get("google_custom_search").get("api_key"), config.get("google_custom_search").get("search_engine_id"), proxies),
                WebBrowser(headless=False, proxy=proxy),
                WebBrowserScreenshot(model=tool_model, headless=False, proxy=proxy),
                WriteFile(),
                TermWriter(shell=shell),
                TermReader(),
                TermControl(shell=shell)
            ],
            None
        )
        self.signal.conversation_changed.emit("加载人物性格")
        meta_model = OpenAIChat(model_name=config.get("openai").get("model_name"),stream=True, api_key=config.get("openai").get("api_key"), base_url=config.get("openai").get("base_url"))
        meta = Meta(
            model=meta_model,
            prompt=config.get("prompt"),
            reasoning_effort=config.get("openai").get("reasoning_effort"),
            verbosity=config.get("openai").get("verbosity"),
            memory=memory,
            toolkit=toolkit,
            retriever=retriever
        )
        self.signal.meta_created.emit(meta)
        self.signal.conversation_changed.emit("加载语音识别")
        self.signal.speech_recognition_created.emit(model)
        self.signal.conversation_changed.emit("加载白板")
        self.signal.whiteboard_created.emit(Whiteboard())
        self.signal.conversation_changed.emit("加载通知图标")
        self.signal.initialize_completed.emit()
        self.signal.conversation_changed.emit("初始化完成")
        self.signal.conversation_finished.emit()


import yaml

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from pathlib import Path
from dataclasses import field
from dataclasses import dataclass
from qdrant_client import QdrantClient
from autogen_core.models import ModelInfo
from autogen_ext.models.openai import OpenAIChatCompletionClient

from ..tools import McpWorkbench
from ..memory.env_memory import EnvMemory
from ..memory.qdrant_memory import QdrantMemory
from ..memory.profiles_memory import ProfilesMemory
from ..embedding.openai_embedding import OpenAIEmbedding
from ..reranker.siliconflow_reranker import SiliconflowReRanker
from ..model_context.qdrant_chat_completion_context import QdrantChatCompletionContext

@dataclass
class ModelInfoConfig:
    vision: bool = False
    function_calling: bool = False
    json_output: bool = False
    family: str = "unknown"
    structured_output: bool = False
    multiple_system_messages: bool = False

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["ModelInfoConfig"]:
        if not data:
            return None
        return cls(**data)

@dataclass
class OpenAIClientConfig:
    model: str
    api_key: str
    base_url: str
    reasoning_effort: str = None
    verbosity: str = None
    model_info: Optional[ModelInfoConfig] = None

@dataclass
class EmbeddingConfig:
    model_name: str
    api_key: str
    base_url: str

@dataclass
class RerankerConfig:
    model_name: str
    api_key: str
    score_threshold: float

@dataclass
class QdrantConfig:
    url: str
    api_key: str

@dataclass
class RAGConfig:
    collection_name: str
    vector_size: int
    score_threshold: float

@dataclass
class ContextConfig:
    collection_name: str
    vector_size: int
    score_threshold: float

@dataclass
class WelaConfig:
    openai_client: OpenAIClientConfig
    embedding: EmbeddingConfig
    reranker: RerankerConfig
    qdrant: QdrantConfig
    rag: RAGConfig
    context: ContextConfig
    mcps: List[Dict[str, Any]]
    system_prompt: str = ""
    profiles: List[str] = field(default_factory=list)

    runtime: Dict[str, Any] = field(default_factory=dict)

class ConfigLoader:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self._validate_config_file()

    def _validate_config_file(self) -> None:
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path.absolute()}")
        if not self.config_path.is_file():
            raise IsADirectoryError(f"{self.config_path.absolute()} 不是一个文件")

    def _load_yaml(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"YAML文件解析错误: {e}")
        except Exception as e:
            raise RuntimeError(f"读取配置文件失败: {e}")

    def _parse_openai_client(self, data: Dict[str, Any]) -> OpenAIClientConfig:
        required = ["model", "api_key", "base_url"]
        for f in required:
            if f not in data:
                raise ValueError(f"openai_client 缺少字段: {f}")

        model_info = ModelInfoConfig.from_dict(data.get("model_info"))

        return OpenAIClientConfig(
            model=data["model"],
            api_key=data["api_key"],
            base_url=data["base_url"],
            reasoning_effort=data.get("reasoning_effort", None),
            verbosity=data.get("verbosity", None),
            model_info=model_info
        )

    def _parse_embedding(self, data: Dict[str, Any]) -> EmbeddingConfig:
        required = ["model_name", "api_key", "base_url"]
        for f in required:
            if f not in data:
                raise ValueError(f"embedding 配置缺少字段: {f}")
        return EmbeddingConfig(**data)

    def _parse_reranker(self, data: Dict[str, Any]) -> RerankerConfig:
        required = ["model_name", "api_key", "score_threshold"]
        for f in required:
            if f not in data:
                raise ValueError(f"reranker 配置缺少字段: {f}")
        return RerankerConfig(**data)

    def _parse_qdrant(self, data: Dict[str, Any]) -> QdrantConfig:
        required = ["url", "api_key"]
        for f in required:
            if f not in data:
                raise ValueError(f"qdrant 配置缺少字段: {f}")
        return QdrantConfig(**data)

    def _parse_rag(self, data: Dict[str, Any]) -> RAGConfig:
        required = ["collection_name", "vector_size", "score_threshold"]
        for f in required:
            if f not in data:
                raise ValueError(f"memory 配置缺少字段: {f}")
        return RAGConfig(**data)

    def _parse_context(self, data: Dict[str, Any]) -> ContextConfig:
        required = ["collection_name", "vector_size", "score_threshold"]
        for f in required:
            if f not in data:
                raise ValueError(f"context 配置缺少字段: {f}")
        return ContextConfig(**data)

    def _parse_config(self, yaml_data: Dict[str, Any]) -> WelaConfig:
        openai_cfg = self._parse_openai_client(yaml_data.get("openai_client", {}))
        embedding_cfg = self._parse_embedding(yaml_data.get("embedding", {}))
        reranker_cfg = self._parse_reranker(yaml_data.get("reranker", {}))
        qdrant_cfg = self._parse_qdrant(yaml_data.get("qdrant", {}))
        rag_cfg = self._parse_rag(yaml_data.get("rag", {}))
        context_cfg = self._parse_context(yaml_data.get("context", {}))

        mcps = yaml_data.get("mcps", [])
        if not isinstance(mcps, list):
            mcps = [mcps]

        system_prompt = yaml_data.get("system_prompt", "")
        profiles = yaml_data.get("profiles", "")

        config = WelaConfig(
            openai_client=openai_cfg,
            embedding=embedding_cfg,
            reranker=reranker_cfg,
            qdrant=qdrant_cfg,
            rag=rag_cfg,
            context=context_cfg,
            mcps=mcps,
            system_prompt=system_prompt,
            profiles = profiles
        )

        self._build_runtime_objects(config)
        return config

    def _build_runtime_objects(self, config: WelaConfig):
        embedding = OpenAIEmbedding(
            model_name=config.embedding.model_name,
            api_key=config.embedding.api_key,
            base_url=config.embedding.base_url,
        )
        reranker = SiliconflowReRanker(
            model_name=config.reranker.model_name,
            api_key=config.reranker.api_key,
            score_threshold=config.reranker.score_threshold
        )
        qdrant_client = QdrantClient(
            url=config.qdrant.url,
            api_key=config.qdrant.api_key,
        )
        environment = EnvMemory()
        rag = QdrantMemory(
            qdrant_client=qdrant_client,
            collection_name=config.rag.collection_name,
            vector_size=config.rag.vector_size,
            embed_func=embedding.embed,
            score_threshold=config.rag.score_threshold
        )
        profile = ProfilesMemory(reranker, config.profiles)
        context = QdrantChatCompletionContext(
            qdrant_client=qdrant_client,
            collection_name=config.context.collection_name,
            vector_size=config.context.vector_size,
            embed_func=embedding.embed,
            score_threshold=config.context.score_threshold
        )
        model_info = config.openai_client.model_info
        if model_info:
            model_info = ModelInfo(**model_info.__dict__)
        model_client = OpenAIChatCompletionClient(
            model=config.openai_client.model,
            api_key=config.openai_client.api_key,
            max_retries=10,
            model_info=model_info,
            base_url=config.openai_client.base_url,
            reasoning_effort=config.openai_client.reasoning_effort
        )
        mcps = [McpWorkbench(mcp_params) for mcp_params in config.mcps]
        config.runtime["rag"] = rag
        config.runtime["memory"] = [profile, rag, environment]
        config.runtime["context"] = context
        config.runtime["model_client"] = model_client
        config.runtime["mcp"] = mcps

    def load_config(self) -> WelaConfig:
        yaml_data = self._load_yaml()
        return self._parse_config(yaml_data)

def get_wela_config(config_path: str = "config.yaml") -> WelaConfig:
    loader = ConfigLoader(config_path)
    return loader.load_config()

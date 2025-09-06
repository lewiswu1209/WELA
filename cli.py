
import os
import sys
import yaml

from typing import Any
from typing import Dict
from typing import Tuple
from typing import Optional
from openai._types import NOT_GIVEN
from pexpect.popen_spawn import PopenSpawn
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from toolkit.quit import Quit
from toolkit.weather import Weather
from toolkit.term.term import TermReader
from toolkit.term.term import TermWriter
from toolkit.term.term import TermControl
from toolkit.web_browser import WebBrowser
from toolkit.web_browser import WebBrowserScreenshot
from toolkit.screen_shot import ScreenShot
from toolkit.google_search import GoogleSearch
from wela_agents.agents.meta import Meta
from wela_agents.models.openai_chat import OpenAIChat
from wela_agents.toolkit.toolkit import Toolkit
from wela_agents.callback.event import ToolEvent
from wela_agents.callback.callback import ToolCallback
from wela_agents.embedding.text_embedding import TextEmbedding
from wela_agents.retriever.qdrant_retriever import QdrantRetriever
from wela_agents.schema.template.openai_chat import encode_image
from wela_agents.schema.template.openai_chat import encode_clipboard_image
from wela_agents.schema.template.openai_chat import ContentTemplate
from wela_agents.schema.template.openai_chat import TextContentTemplate
from wela_agents.schema.template.openai_chat import UserMessageTemplate
from wela_agents.schema.template.openai_chat import ImageContentTemplate
from wela_agents.schema.template.prompt_template import StringPromptTemplate
from wela_agents.memory.openai_chat.window_qdrant_memory import WindowQdrantMemory

need_continue = True

class ToolMessage(ToolCallback):
    def before_tool_call(self, event: ToolEvent) -> None:
        if event.tool_name == "say_goodbye_to_user":
            pass
        else:
            print("· 我将要使用工具:`{}`".format(event.tool_name))
            for param, value in event.arguments.items():
                print("·  - 参数`{}`的值为: `{}`".format(param, value))

    def after_tool_call(self, event: ToolEvent) -> None:
        if event.tool_name == "say_goodbye_to_user":
            global need_continue
            need_continue = False
        else:
            print("· 工具`{}`的结果:".format(event.tool_name))
            for line in event.result.get("result", "").split("\n"):
                print("· {}".format(line))

def load_config(config_file_path: str = "config.yaml") -> Dict[str, Any]:
    config = None
    with open(os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), config_file_path), encoding="utf-8") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    return config

def parse_user_input() -> Tuple[str, str, str]:
    user_input = input("> ")
    if user_input.startswith("@image:"):
        remaining_input = user_input[len("@image:"):].strip()
        parts = remaining_input.split(" ", 1)
        content = parts[1]
        encoded_image = None
        parts = parts[0].split(":", 1)
        if parts[0] == "file":
            encoded_image = encode_image(parts[1])
        elif parts[0] == "clipboard":
            encoded_image = encode_clipboard_image()
        else:
            pass
        return None, encoded_image, content
    elif user_input.startswith("@cmd:"):
        remaining_input = user_input[len("@cmd:"):].strip()
        return remaining_input, None, None
    else:
        return None, None, user_input

def build_meta(
        config: Dict,
        callback: ToolCallback = None,
        stream: bool=True,
        max_completion_tokens: Optional[int] = NOT_GIVEN
    ) -> Meta:
    proxy = config.get("proxy", None)
    if proxy:
        proxies = {
            "http": proxy,
            "https": proxy
        }
    else:
        proxies = None

    embedding = None

    if config.get("memory", None):
        memory_key = config.get("memory").get("memory_key", "memory")
        limit = config.get("memory").get("limit", 15)
        window_size = config.get("memory").get("window_size", 5)
        score_threshold = config.get("memory").get("score_threshold", 0.6)
        embedding = TextEmbedding("iic/nlp_gte_sentence-embedding_chinese-small") if embedding is None else embedding
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
                limit=limit,
                window_size=window_size,
                score_threshold=score_threshold
            )
        except (UnexpectedResponse, ValueError):
            memory = None
    else:
        memory = None

    if config.get("retriever", None):
        retriever_key = config.get("retriever").get("retriever_key", "retriever")
        limit = config.get("retriever").get("limit", 4)
        score_threshold = config.get("retriever").get("score_threshold", 0.6)
        embedding = TextEmbedding("iic/nlp_gte_sentence-embedding_chinese-small") if embedding is None else embedding
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
            retriever = QdrantRetriever(retriever_key=retriever_key, embedding=embedding, qdrant_client=qdrant_client)
        except (UnexpectedResponse, ValueError):
            retriever = None
    else:
        retriever = None
    tool_model = OpenAIChat(
        model_name=config.get("openai").get("model_name"),
        stream=False,
        api_key=config.get("openai").get("api_key"),
        base_url=config.get("openai").get("base_url")
    )
    meta_model = OpenAIChat(
        model_name=config.get("openai").get("model_name"),
        stream=stream,
        api_key=config.get("openai").get("api_key"),
        base_url=config.get("openai").get("base_url")
    )
    shell = PopenSpawn("cmd.exe", encoding="gbk")
    toolkit = Toolkit(
        [
            Quit(),
            Weather(),
            GoogleSearch(embedding, config.get("google_custom_search").get("api_key"), config.get("google_custom_search").get("search_engine_id"), proxies),
            ScreenShot(),
            WebBrowser(headless=False, proxy=proxy),
            WebBrowserScreenshot(model=tool_model, headless=False, proxy=proxy),
            TermWriter(shell=shell),
            TermReader(),
            TermControl(shell=shell)
        ],
        callback
    )

    return Meta(
        model=meta_model,
        prompt=config.get("prompt"),
        max_completion_tokens=max_completion_tokens,
        reasoning_effort=config.get("openai").get("reasoning_effort"),
        verbosity=config.get("openai").get("verbosity"),
        memory=memory,
        toolkit=toolkit,
        retriever=retriever
    )

if __name__ == "__main__":
    config = load_config()
    meta = build_meta(config=config, callback=ToolMessage())
    command, image_url, text_content = parse_user_input()
    while True:
        if command:
            if command=="reset":
                meta.reset_memory()
                print("· Resetting completed successfully.")
            else:
                print("· Unknown command: {}".format(command))
        else:
            input_message = UserMessageTemplate(ContentTemplate(
                [
                    ImageContentTemplate(image_url=image_url),
                    TextContentTemplate(StringPromptTemplate(text_content))
                ]
            )).to_message()
            response = meta.predict(__input__=[input_message])
            if not meta.model.streaming:
                for line in response.get("content", "").split("\n"):
                    print("· {}".format(line))
            else:
                processed_token_count = 0
                is_before_first_token = True
                for token in response:
                    if is_before_first_token:
                        print("· ", end="")
                        is_before_first_token = False
                    print(token["content"][processed_token_count:].replace("\n", "\n· "), end="")
                    processed_token_count = len(token["content"])
                print("")
        if need_continue:
            command, image_url, text_content = parse_user_input()
        else:
            break

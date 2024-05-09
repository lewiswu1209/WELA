
import yaml

from qdrant_client import QdrantClient

from meta import Meta
from models import OpenAIChat
from memory import WindowQdrantMemory
from toolkit import Quit
from toolkit import Toolkit
from toolkit import Browser
from toolkit import Definition
from toolkit import DuckDuckGo
from callback import ToolEvent
from callback import ToolCallback

need_continue = True

class ToolMessage(ToolCallback):
    def before_tool_call(self, event: ToolEvent) -> None:
        if event.tool_name == "duckduckgo_search":
            print("正在搜索\"{}\"".format(event.arguments.get("query")))
        elif event.tool_name == "get_definition":
            print("正在查找\"{}\"的定义".format(event.arguments.get("english_keywords")))
        elif event.tool_name == "browser":
            print("正在浏览网页:{}".format(event.arguments.get("url")))
        elif event.tool_name == "quit":
            pass
        else:
            print("准备使用工具:{}\n参数:{}".format(event.tool_name, event.arguments))

    def after_tool_call(self, event: ToolEvent) -> None:
        if event.tool_name == "quit":
            global need_continue
            need_continue = False
        else:
            print("结果:{}".format(event.result))

if __name__ == "__main__":
    with open("config.yaml") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    if config.get("proxy", None):
        proxies = {
            "http": config.get("proxy"),
            "https": config.get("proxy")
        }
    else:
        proxies = None
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
            
        memory = WindowQdrantMemory(
            memory_key=memory_key, 
            qdrant_client=qdrant_client,
            limit=limit,
            window_size=window_size,
            score_threshold=score_threshold
        )
    else:
        memory = None
    toolkit = Toolkit([Quit(), DuckDuckGo(proxies), Definition(proxies), Browser()], ToolMessage())
    model = OpenAIChat(stream=True, api_key=config.get("openai").get("api_key"), base_url=config.get("openai").get("base_url"))
    meta_human = Meta(model=model, prompt=config.get("prompt"),memory=memory, toolkit=toolkit)
    user_text = input("> ")
    while True:
        response = meta_human.run(user_text)
        if not model.streaming:
            print("- {}".format(response))
        else:
            pre_len = 0
            is_before_first_token = True
            for token in response:
                if is_before_first_token:
                    print("- ", end="")
                    is_before_first_token = False
                print(token[pre_len:], end="")
                pre_len = len(token)
            print("")
        if need_continue:
            user_text = input("> ")
        else:
            break

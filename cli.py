
import yaml

from qdrant_client import QdrantClient

from meta.meta import Meta
from models.openai_chat import OpenAIChat
from memory.window_qdrant_memory import WindowQdrantMemory

from toolkit.quit import Quit
from toolkit.toolkit import Toolkit
from toolkit.definition import Definition
from toolkit.browsing.browsing import Browsing

from callback.event import ToolEvent
from callback.callback import ToolCallback

need_continue = True

class ToolMessage(ToolCallback):
    def before_tool_call(self, event: ToolEvent) -> None:
        if event.tool_name == "quit":
            pass
        else:
            print("准备使用工具:{}\n参数:\n{}".format(event.tool_name, event.arguments))

    def after_tool_call(self, event: ToolEvent) -> None:
        if event.tool_name == "quit":
            global need_continue
            need_continue = False
        else:
            print("工具'{}'的结果:\n{}".format(event.tool_name, event.result))

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
    meta_model = OpenAIChat(stream=True, api_key=config.get("openai").get("api_key"), base_url=config.get("openai").get("base_url"))
    tool_model = OpenAIChat(stream=False, api_key=config.get("openai").get("api_key"), base_url=config.get("openai").get("base_url"))
    toolkit = Toolkit([Quit(), Definition(proxies), Browsing(tool_model, proxies)], ToolMessage())
    meta_human = Meta(model=meta_model, prompt=config.get("prompt"),memory=memory, toolkit=toolkit)
    user_text = input("> ")
    while True:
        response = meta_human.run(user_text)
        if not meta_model.streaming:
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

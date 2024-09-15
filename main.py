
import os
import sys
import yaml

from qdrant_client import QdrantClient
from PyQt5.QtWidgets import QApplication

from agents.meta import Meta
from gui.wela_widget import WelaWidget
from models.openai_chat import OpenAIChat
from callback.event import ToolEvent
from callback.callback import ToolCallback
from memory.window_qdrant_memory import WindowQdrantMemory
from toolkit.quit import Quit
from toolkit.toolkit import Toolkit
from toolkit.weather import Weather
from toolkit.definition import Definition
from toolkit.browsing.browsing import Browsing
from schema.template.openai_chat import encode_image
from schema.template.openai_chat import encode_clipboard_image
from schema.template.openai_chat import ContentTemplate
from schema.template.openai_chat import TextContentTemplate
from schema.template.openai_chat import UserMessageTemplate
from schema.template.openai_chat import ImageContentTemplate
from schema.template.prompt_template import StringPromptTemplate

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

def parse_user_input():
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
        return encoded_image, content
    else:
        return None, user_input

def build_meta(config_file_path: str = "config.yaml", callback: ToolCallback = None):
    with open(os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), config_file_path), encoding="utf-8") as f:
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

    meta_model = OpenAIChat(model_name=config.get("openai").get("model_name"),stream=True, api_key=config.get("openai").get("api_key"), base_url=config.get("openai").get("base_url"))
    tool_model = OpenAIChat(model_name=config.get("openai").get("model_name"),stream=False, api_key=config.get("openai").get("api_key"), base_url=config.get("openai").get("base_url"))
    toolkit = Toolkit([Quit(), Weather(), Definition(proxies), Browsing(tool_model, proxies)], callback)

    return Meta(model=meta_model, prompt=config.get("prompt"),memory=memory, toolkit=toolkit)

if __name__ == "__main__":
    if "--gui" in sys.argv[1:]:
        app: QApplication = QApplication(sys.argv)
        widget: WelaWidget = WelaWidget()
        widget.show()
        app.exec_()
    else:
        meta = build_meta(callback=ToolMessage())
        encoded_image, user_text = parse_user_input()
        while True:
            input_message = UserMessageTemplate(ContentTemplate(
                [
                    ImageContentTemplate(image_url=encoded_image),
                    TextContentTemplate(StringPromptTemplate(user_text))
                ]
            )).to_message()
            response = meta.predict(__input__=[input_message])
            if not meta.model.streaming:
                print("- {}".format(response["content"]))
            else:
                pre_len = 0
                is_before_first_token = True
                for token in response:
                    if is_before_first_token:
                        print("- ", end="")
                        is_before_first_token = False
                    print(token["content"][pre_len:], end="")
                    pre_len = len(token["content"])
                print("")
            if need_continue:
                encoded_image, user_text = parse_user_input()
            else:
                break

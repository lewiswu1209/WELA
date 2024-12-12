
import os
import sys
import time
import yaml
import hashlib
import markdown

from flask import Flask
from flask import request
from flask import make_response
from typing import Any
from typing import Dict
from typing import Tuple
from typing import Optional
from xml.etree import ElementTree
from expiringdict import ExpiringDict
from openai._types import NOT_GIVEN
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
from toolkit.duckduckgo import DuckDuckGo
# from toolkit.browsing.browsing import Browsing
from schema.template.openai_chat import encode_image
from schema.template.openai_chat import encode_clipboard_image
from schema.template.openai_chat import ContentTemplate
from schema.template.openai_chat import TextContentTemplate
from schema.template.openai_chat import UserMessageTemplate
from schema.template.openai_chat import ImageContentTemplate
from schema.template.prompt_template import StringPromptTemplate

need_continue = True
app = Flask(__name__)
output_xml = '''<xml>
    <ToUserName><![CDATA[%s]]></ToUserName>
    <FromUserName><![CDATA[%s]]></FromUserName>
    <CreateTime>%s</CreateTime>
    <MsgType><![CDATA[text]]></MsgType>
    <Content><![CDATA[%s]]></Content>
</xml>'''

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

def build_meta(config: Dict, callback: ToolCallback = None, stream: bool=True, max_tokens: Optional[int] = NOT_GIVEN) -> Meta:
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

    meta_model = OpenAIChat(model_name=config.get("openai").get("model_name"), stream=stream, api_key=config.get("openai").get("api_key"), base_url=config.get("openai").get("base_url"))
    # tool_model = OpenAIChat(model_name=config.get("openai").get("model_name"), stream=False, api_key=config.get("openai").get("api_key"), base_url=config.get("openai").get("base_url"))
    toolkit = Toolkit([Quit(), Weather(), Definition(proxies), DuckDuckGo(proxies)], callback)

    return Meta(model=meta_model, prompt=config.get("prompt"), memory=memory, toolkit=toolkit, max_tokens=max_tokens)

@app.route("/gh", methods=["GET"])
def gh_verify():
    signature = request.args.get("signature")
    timestamp = request.args.get("timestamp")
    nonce = request.args.get("nonce")
    echostr = request.args.get("echostr")

    temp = [timestamp, nonce, wechat_token]
    temp.sort()
    temp = "".join(temp)

    if (hashlib.sha1(temp.encode("utf8")).hexdigest() == signature):
        return echostr
    else:
        return "error", 403

@app.route("/gh", methods=["POST"])
def gh_process():
    msg_tree = ElementTree.fromstring(request.data)
    from_user = msg_tree.find("FromUserName").text
    to_user = msg_tree.find("ToUserName").text
    if from_user not in openids:
        return "success"
    else:
        nonce = request.args.get("nonce")
        if nonce in cache:
            for _ in range(4000):
                if cache[nonce] != "":
                    gh_response = make_response(output_xml % (from_user, to_user, str(int(time.time())), cache[nonce]))
                    gh_response.content_type = "application/xml"
                    return gh_response
                else:
                    time.sleep(0.001)
            gh_response = make_response(output_xml % (from_user, to_user, str(int(time.time())), f"https://wela.aetheriaverse.us.kg/msg?nonce={nonce}"))
            gh_response.content_type = "application/xml"
            return gh_response
        else:
            cache[nonce] = ""
            msg_type = msg_tree.find("MsgType").text
            if msg_type == "text":
                msg_content = msg_tree.find("Content").text
                if msg_content == "@cmd:reset":
                    meta.reset_memory()
                    meta_response = {
                        "role": "assistant",
                        "content": "Resetting completed successfully."
                    }
                else:
                    input_message = UserMessageTemplate(StringPromptTemplate(msg_content)).to_message()
                    meta_response = meta.predict(__input__=[input_message])
            elif msg_type == "image":
                pic_url = msg_tree.find("PicUrl").text
                input_message = UserMessageTemplate(ContentTemplate(
                    [
                        ImageContentTemplate(image_url=pic_url),
                        TextContentTemplate(StringPromptTemplate(""))
                    ]
                )).to_message()
                meta_response = meta.predict(__input__=[input_message])
            else:
                meta_response = {
                    "role": "assistant",
                    "content": "暂不支持此类消息"
                }
            cache[nonce] = meta_response["content"]
            time.sleep(5)
            return "success"

@app.route("/msg", methods=["GET"])
def gh_msg():
    nonce = request.args.get("nonce")
    if nonce in cache:
        html = markdown.markdown(cache[nonce])
        gh_response = make_response(html)
        # gh_response.content_type = "application/xml"
        return gh_response
    else:
        gh_response = make_response("参数无效")
        # gh_response.content_type = "application/xml"
        return gh_response

if __name__ == "__main__":
    if "--gui" in sys.argv[1:]:
        app: QApplication = QApplication(sys.argv)
        widget: WelaWidget = WelaWidget()
        widget.show()
        app.exec_()
    elif "--wechat" in sys.argv[1:]:
        config = load_config()
        meta = build_meta(config, stream=False)
        wechat_token = config.get("wechat_token")
        openids = config.get("openids")
        cache = ExpiringDict(max_len=100, max_age_seconds=360)
        app.run(host=config.get("host"), port=config.get("port"), debug=False)
    else:
        config = load_config()
        meta = build_meta(config=config, callback=ToolMessage())
        command, image_url, text_content = parse_user_input()
        while True:
            if command:
                if command=="reset":
                    meta.reset_memory()
                    print("- Resetting completed successfully.")
            else:
                input_message = UserMessageTemplate(ContentTemplate(
                    [
                        ImageContentTemplate(image_url=image_url),
                        TextContentTemplate(StringPromptTemplate(text_content))
                    ]
                )).to_message()
                response = meta.predict(__input__=[input_message])
                if not meta.model.streaming:
                    print("- {}".format(response["content"]))
                else:
                    processed_token_count = 0
                    is_before_first_token = True
                    for token in response:
                        if is_before_first_token:
                            print("- ", end="")
                            is_before_first_token = False
                        print(token["content"][processed_token_count:], end="")
                        processed_token_count = len(token["content"])
                    print("")
            if need_continue:
                command, image_url, text_content = parse_user_input()
            else:
                break

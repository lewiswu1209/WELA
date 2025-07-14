
import os
import sys
import time
import yaml
import hashlib

from flask import Flask
from flask import request
from flask import make_response
from typing import Any
from typing import Dict
from typing import Optional
from xml.etree import ElementTree
from expiringdict import ExpiringDict
from openai._types import NOT_GIVEN
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from toolkit.quit import Quit
from toolkit.weather import Weather
from toolkit.web_browser import WebBrowser
from toolkit.web_browser import WebBrowserScreenshot
from toolkit.google_search import GoogleSearch
from wela_agents.agents.meta import Meta
from wela_agents.models.openai_chat import OpenAIChat
from wela_agents.toolkit.toolkit import Toolkit
from wela_agents.callback.event import ToolEvent
from wela_agents.callback.callback import ToolCallback
from wela_agents.retriever.qdrant_retriever import QdrantRetriever
from wela_agents.schema.template.openai_chat import ContentTemplate
from wela_agents.schema.template.openai_chat import TextContentTemplate
from wela_agents.schema.template.openai_chat import UserMessageTemplate
from wela_agents.schema.template.openai_chat import ImageContentTemplate
from wela_agents.schema.template.prompt_template import StringPromptTemplate
from wela_agents.memory.openai_chat.window_qdrant_memory import WindowQdrantMemory

need_continue = True
flask = Flask(__name__)
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
            if "--debug" in sys.argv[1:]:
                print("准备使用工具:{}\n参数:\n{}".format(event.tool_name, event.arguments))

    def after_tool_call(self, event: ToolEvent) -> None:
        if event.tool_name == "quit":
            global need_continue
            need_continue = False
        else:
            if "--debug" in sys.argv[1:]:
                print("工具'{}'的结果:\n{}".format(event.tool_name, event.result))

def load_config(config_file_path: str = "config.yaml") -> Dict[str, Any]:
    config = None
    with open(os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), config_file_path), encoding="utf-8") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    return config

def build_meta(config: Dict, callback: ToolCallback = None, stream: bool=True, max_tokens: Optional[int] = NOT_GIVEN) -> Meta:
    proxy = config.get("proxy", None)
    if proxy:
        proxies = {
            "http": proxy,
            "https": proxy
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
        try:
            memory = WindowQdrantMemory(
                memory_key=memory_key, 
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
            retriever = QdrantRetriever(retriever_key=retriever_key, qdrant_client=qdrant_client)
        except (UnexpectedResponse, ValueError):
            retriever = None
    else:
        retriever = None
    # tool_model = OpenAIChat(model_name=config.get("openai").get("model_name"),stream=False, api_key=config.get("openai").get("api_key"), base_url=config.get("openai").get("base_url"))
    meta_model = OpenAIChat(model_name=config.get("openai").get("model_name"), stream=stream, api_key=config.get("openai").get("api_key"), base_url=config.get("openai").get("base_url"))
    # toolkit = Toolkit([Quit(), Weather(), GoogleSearch(proxies), WebBrowser(headless=False, proxy=proxy), WebBrowserScreenshot(model=tool_model, headless=False, proxy=proxy)], callback)

    return Meta(model=meta_model, prompt=config.get("prompt"), memory=memory, toolkit=None, retriever=retriever, max_tokens=max_tokens)

@flask.route("/gh", methods=["GET"])
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

@flask.route("/gh", methods=["POST"])
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
            time.sleep(5)
            return "success"
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

if __name__ == "__main__":
    config = load_config()
    meta = build_meta(config, stream=False, max_tokens=170)
    wechat_token = config.get("wechat_token")
    openids = config.get("openids")
    cache = ExpiringDict(max_len=100, max_age_seconds=360)
    flask.run(host=config.get("host"), port=config.get("port"), debug=False)

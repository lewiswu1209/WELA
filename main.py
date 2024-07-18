
import sys

import common

from PyQt5.QtWidgets import QApplication

from gui.widget.widget import Widget
from callback.event import ToolEvent
from callback.callback import ToolCallback
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
            encoded_image = common.encode_image(parts[1])
        elif parts[0] == "clipboard":
            encoded_image = common.encode_clipboard_image()
        else:
            pass
        return encoded_image, content
    else:
        return None, user_input

if __name__ == "__main__":
    if "--gui" in sys.argv[1:]:
        app: QApplication = QApplication(sys.argv)
        widget: Widget = Widget()
        widget.show()
        app.exec_()
    else:
        meta_gpt_3_5, meta_gpt_4o = common.build_meta(callback=ToolMessage())
        encoded_image, user_text = parse_user_input()
        while True:
            if encoded_image:
                input_message = UserMessageTemplate(ContentTemplate(
                    [
                        ImageContentTemplate(image_url=encoded_image),
                        TextContentTemplate(StringPromptTemplate(user_text))
                    ]
                )).to_message()
                meta = meta_gpt_4o
            else:
                input_message = UserMessageTemplate(StringPromptTemplate(user_text)).to_message()
                meta = meta_gpt_3_5
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

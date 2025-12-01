
import re
import asyncio

from PIL import Image
from PIL import ImageGrab
from typing import List
from typing import Union

from autogen_core import Image as AGImage
from autogen_core import CancellationToken
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.messages import ThoughtEvent
from autogen_agentchat.messages import BaseAgentEvent
from autogen_agentchat.messages import BaseChatMessage
from autogen_agentchat.messages import ToolCallRequestEvent
from autogen_agentchat.messages import ToolCallExecutionEvent
from autogen_agentchat.messages import ToolCallSummaryMessage
from autogen_agentchat.messages import ModelClientStreamingChunkEvent
from autogen_agentchat.conditions import TextMentionTermination

from wela_agent import Wela
from wela_agent.tools import McpWorkbench
from wela_agent.config_loader import get_app_config

from autogen_core.model_context import BufferedChatCompletionContext

class WelaCLI:

    def __init__(self):
        self.__old_full_message_id = None
        self.__last_token = ""

    async def user_input(self, prompt: str, cancellation_token: CancellationToken | None = None) -> str:
        user_input = ""
        while not user_input:
            user_input = input("user > ")
        if user_input.startswith("@image:"):
            remaining_input = user_input[len("@image:"):].strip()
            parts = remaining_input.split(" ", 1)
            content = parts[1]
            image = None
            parts = parts[0].split(":", 1)
            if parts[0] == "file":
                org = Image.open(parts[1])
                image = AGImage(org)
                org.close()
            elif parts[0] == "clipboard":
                image = AGImage(ImageGrab.grabclipboard())
            else:
                pass
            return [image, content]
        # elif user_input.startswith("@cmd:"):
        #     remaining_input = user_input[len("@cmd:"):].strip()
        #     return remaining_input, None, None
        else:
            return user_input

    def assistant_output(self, message: Union[BaseAgentEvent,BaseChatMessage,TaskResult]):
        if isinstance(message, ModelClientStreamingChunkEvent):
            prompt = "wela > "
            indent = " " * len(prompt)
            if self.__old_full_message_id != message.full_message_id:
                print(prompt, end="")
                self.__old_full_message_id = message.full_message_id
                self.__last_token = ""
            content = message.content
            if content:
                if self.__last_token.endswith("\n"):
                    content = re.sub(r"\n?(?!\n)", f"\n{indent}", content)
                else:
                    content = re.sub(r"\n(?!\n)", f"\n{indent}", content)
                print(content, end="")
                self.__last_token = content
        elif isinstance(message, TextMessage):
            print("")
        elif isinstance(message, ToolCallRequestEvent):
            prompt = "function_call > "
            for function_call in message.content:
                print( f"{prompt}name='{function_call.name}' arguments='{function_call.arguments}'" )
        elif isinstance(message, ToolCallExecutionEvent):
            prompt = "function_exec > "
            indent = " " * len(prompt)
            for function_result in message.content:
                print( f"{prompt}name='{function_result.name}' iserror={function_result.is_error}")
                print( f"{indent}", end="")
                print( re.sub("\n(?!\n)", f"\n{indent}",function_result.content) )
        elif isinstance(message, ToolCallSummaryMessage):
            print("tool > " + str(message))
        elif isinstance(message, ThoughtEvent):
            pass

async def main():
    config = get_app_config("config.yaml")
    memory = config.runtime["memory"]
    context = config.runtime["context"]
    model_client = config.runtime["model_client"]
    mcps: List[McpWorkbench] = config.runtime["mcp"]

    welacli = WelaCLI()
    await asyncio.gather(*[mcp.start() for mcp in mcps])
    wela = Wela(
        model_client=model_client,
        workbench=mcps,
        model_context=context,
        system_prompt=config.system_prompt,
        max_tool_iterations=5,
        memory=memory,
        termination=TextMentionTermination("exit")
    )
    await wela.chat(input_func=welacli.user_input, output_func=welacli.assistant_output)
    await asyncio.gather(*[mcp.stop() for mcp in mcps])

if __name__ == "__main__":
    asyncio.run(main())

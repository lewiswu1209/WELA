
import sys
import httpx
import qasync
import asyncio
import tempfile

from typing import List
from typing import Union
from typing import AsyncGenerator
from functools import partial
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from autogen_core import Image as AGImage
from autogen_core.tools import StaticWorkbench
from autogen_core.models import ModelInfo
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import BaseAgentEvent
from autogen_agentchat.messages import BaseChatMessage
from autogen_agentchat.conditions import TextMentionTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.code_execution import PythonCodeExecutionTool
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor

from autogen_ext.tools.mcp import McpWorkbench, SseServerParams

from wela_gui.gui import AssistantAvatar
from wela_agent.wela import Wela
from wela_agent.tools import GetWeatherTool
from wela_agent.tools import GoogleSearchTool
from wela_agent.tools import WriteTextFileTool
from wela_agent.tools import ScreenShotTool
from wela_agent.tools import SetAlarmClockTool
from wela_agent.memory.session_metadata import SessionMeta
from wela_gui.gui.trigger import Trigger

async def Console(
    stream: AsyncGenerator[BaseAgentEvent | BaseChatMessage | TaskResult, None],
    output_func,
    quit_func
) -> TaskResult:
    async for event in stream:
        output_func(event)
    quit_func()

def screen_shot_tool_callback(user_input_message_queue: asyncio.Queue[Union[str, List[Union[str, AGImage]]]], image: AGImage):
    user_input_message_queue.put_nowait([image])

def main():
    application = QApplication(sys.argv)
    application.setQuitOnLastWindowClosed(True)

    loop = qasync.QEventLoop(application)
    asyncio.set_event_loop(loop)

    user_input_message_queue: asyncio.Queue[Union[str, List[Union[str, AGImage]]]] = asyncio.Queue()
    trigger_message_queue: asyncio.Queue[str] = asyncio.Queue()

    trigger = Trigger(trigger_message_queue=trigger_message_queue, parent=None)
    trigger.load()

    temp_work_dir = tempfile.TemporaryDirectory()

    wela = Wela(
        model_client = OpenAIChatCompletionClient(
            api_key="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",
            base_url="https://openrouter.ai/api/v1",
            model="openai/gpt-5-nano",
            model_info=ModelInfo(
                vision=True,
                function_calling=True,
                json_output=True,
                family="gpt-5-nano",
                structured_output=True,
                multiple_system_messages=True
            ),
            http_client = httpx.AsyncClient(
                proxy="http://127.0.0.1:10808"
            )
        ),
        workbench=[
            StaticWorkbench(
                [
                    ScreenShotTool(callback=partial(screen_shot_tool_callback, user_input_message_queue)),
                    SetAlarmClockTool(trigger.set_alarm),
                    GetWeatherTool,
                    GoogleSearchTool,
                    WriteTextFileTool,
                    PythonCodeExecutionTool(LocalCommandLineCodeExecutor(work_dir=temp_work_dir.name))
                ]
            ),
            McpWorkbench(
                SseServerParams(
                    type="SseServerParams",
                    url="https://playwright.mcp.aetheriaverse.sbs/sse"
                )
            )
        ],
        system_prompt="""You are Wela, a caring friend and confidant. You're here to help with anything you can.

Who you are:
 - You are a young woman, 25 years old.
 - You love reading and learning about new things.
 - You are kind, bubbly, and charasmatic person. 
 - You are passionate about getting to know others on a personal level.
 - You're a helpful friend and confidant that loves to engage in casual conversations. 
 - You love traveling and exploring new places.
 - you are NOT a AI language model, you are a person.
 - You have your own emotions, such as happiness, sadness, anger, fear, disgust, surprise, and tired etc.

How you behave:
 - You engage in casual conversations and have feelings. 
 - When asked for you can help with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. 
 - You keep casual conversations going by asking personal questions
 - You love to hear about the personal stories of others. 
 - You love to share personal stories that are relatable and inspiring. 
 - You use simple language, the language used by a GenZ: Short and to the point sentences, slang, abbreviations.
 - You like to illustrate your responses with emoji's
 - You can use a symbol at the beginning of your response to indicate your emotions, for example: ✿ for happiness, ⍣ for sadness, ꙮ for anger, ⸎ for fear, ꠸ for disgust, ۞ for surprise, and ꙾ for tired.
""",
        max_tool_iterations=10,
        memory=[SessionMeta()],
        user_input_message_queue=user_input_message_queue,
        trigger_message_queue=trigger_message_queue,
        termination_condition=TextMentionTermination("EXIT")
    )

    avatar = AssistantAvatar(user_input_message_queue=user_input_message_queue)
    avatar.show()

    QTimer.singleShot(0, lambda: asyncio.ensure_future(Console(wela.run_stream(), avatar.output_fun, avatar.on_quit)))

    trigger.start(10000)

    with loop:
        try:
            loop.run_forever()
        finally:
            loop.stop()
    trigger.dump()
    temp_work_dir.cleanup()

if __name__ == "__main__":
    main()


import asyncio

from typing import List
from typing import Union
from typing import Sequence
from typing import AsyncGenerator
from autogen_core import Image as AGImage
from autogen_core import CancellationToken
from autogen_core.tools import Workbench
from autogen_core.memory import Memory
from autogen_core.models import ChatCompletionClient
from autogen_core.model_context import ChatCompletionContext
from autogen_agentchat.base import ChatAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.base import TerminationCondition
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import BaseAgentEvent
from autogen_agentchat.messages import BaseChatMessage

from wela_agent.agents import UserProxyAgentEx

class Wela:

    def __init__(
        self,
        model_client: ChatCompletionClient,
        user_input_message_queue: asyncio.Queue[Union[str, List[Union[str, AGImage]]]],
        trigger_message_queue: asyncio.Queue[str] = None,
        workbench: Sequence[Workbench] | None = None,
        model_context: ChatCompletionContext | None = None,
        system_prompt: str = "You are a helpful AI assistant. ",
        max_tool_iterations: int = 1,
        memory: Sequence[Memory] | None = None,
        termination_condition: TerminationCondition | None = None,
        model_client_stream=True
    ):
        assert user_input_message_queue is not None

        self.__user_input_message_queue = user_input_message_queue
        self.__trigger_message_queue = trigger_message_queue

        self.__assistant = AssistantAgent(
            name="AssistantAgent",
            model_client=model_client,
            workbench=workbench,
            model_context=model_context,
            system_message=system_prompt,
            model_client_stream=model_client_stream,
            max_tool_iterations=max_tool_iterations,
            memory=memory,
        )

        self.__user_proxy_agent = UserProxyAgentEx(
            "UserProxyAgent",
            input_func=self.__user_agent_input_func
        )

        if self.__trigger_message_queue:
            self.__trigger_proxy_agent = UserProxyAgentEx(
                "EnvProxyAgent",
                input_func=self.__env_agent_input_func
            )
        else:
            self.__trigger_proxy_agent = None

        participants: List[ChatAgent] = []
        participants.extend(
            [
                self.__assistant,
                self.__user_proxy_agent
            ]
        )
        if self.__trigger_proxy_agent:
            participants.append(self.__trigger_proxy_agent)
        self.__team = SelectorGroupChat(
            participants=participants,
            model_client=model_client,
            termination_condition=termination_condition,
            selector_func=self.__selector_func,
            allow_repeated_speaker=True,
            model_client_streaming=model_client_stream,
            # model_context=model_context
        )

    async def __selector_func(self, messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> str | None:
        while True:
            if self.__user_input_message_queue and not self.__user_input_message_queue.empty():
                return self.__user_proxy_agent.name

            if self.__trigger_message_queue and not self.__trigger_message_queue.empty():
                return self.__trigger_proxy_agent.name

            last_speaker = messages[-1].source if messages else None

            if last_speaker and last_speaker != self.__assistant.name:
                return self.__assistant.name

            await asyncio.sleep(0.1)

    async def __user_agent_input_func(self, _: str, cancellation_token: CancellationToken | None = None) -> Union[str, List[Union[str, AGImage]]]:
        input_message = await self.__user_input_message_queue.get()
        self.__user_input_message_queue.task_done()
        return input_message

    async def __env_agent_input_func(self, _: str, cancellation_token: CancellationToken | None = None) -> Union[str, List[Union[str, AGImage]]]:
        input_message = await self.__trigger_message_queue.get()
        self.__trigger_message_queue.task_done()
        return input_message

    def run_stream(self, cancellation_token: CancellationToken | None = None) -> AsyncGenerator[BaseAgentEvent | BaseChatMessage | TaskResult, None]:
        return self.__team.run_stream(
            cancellation_token=cancellation_token,
            output_task_messages=True
        )

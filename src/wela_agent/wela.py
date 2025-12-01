
import asyncio

from typing import List
from typing import Callable
from typing import Optional
from typing import Sequence
from typing import Awaitable
from inspect import iscoroutinefunction
from autogen_core import Image
from autogen_core import CancellationToken
from autogen_core.tools import Workbench
from autogen_core.models import ChatCompletionClient
from autogen_core.memory import Memory
from autogen_core.model_context import ChatCompletionContext
from autogen_agentchat.base import TaskResult
from autogen_agentchat.base import TerminationCondition
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.agents import AssistantAgent

from wela_agent.agents import UserProxyAgentEx

class Wela:

    def __init__(
            self,
            model_client: ChatCompletionClient,
            workbench: Sequence[Workbench] | None,
            model_context: ChatCompletionContext | None,
            system_prompt: str,
            model_client_stream: bool,
            max_tool_iterations: int,
            memory: Sequence[Memory] | None,
            input_func: Optional[ Callable[[str, Optional[CancellationToken]], Awaitable[str | List[str|Image]]] ] = None,
            output_func: Optional[Callable[[str], None]] = None,
            termination_condition: TerminationCondition | None = None
        ):
        self.__model_client = model_client
        self.__workbench = workbench
        self.__model_context = model_context
        self.__system_prompt = system_prompt
        self.__model_client_stream = model_client_stream
        self.__max_tool_iterations = max_tool_iterations
        self.__memory = memory
        self.__input_func = input_func
        self.__output_func = output_func
        self.__termination_condition = termination_condition

        self.__assistant = AssistantAgent(
            name="assistant",
            model_client=self.__model_client,
            workbench=self.__workbench,
            model_context=self.__model_context,
            system_message=self.__system_prompt,
            model_client_stream=self.__model_client_stream,
            max_tool_iterations=self.__max_tool_iterations,
            memory=self.__memory
        )
        self.__user_agent = UserProxyAgentEx(
            name="user",
            input_func=self.__input_func
        )
        self.__team = RoundRobinGroupChat(
            [
                self.__user_agent,
                self.__assistant
            ],
            termination_condition=self.__termination_condition
        )

    async def chat(self) -> None:
        if self.__workbench:
            await asyncio.gather(*[workbench.start() for workbench in self.__workbench])

        async for message in self.__team.run_stream():
            if isinstance(message, TaskResult):
                pass
            else:
                if message.source == self.__assistant.name:
                    if iscoroutinefunction(self.__output_func):
                        await self.__output_func(message)
                    else:
                        self.__output_func(message)

        if self.__workbench:
            await asyncio.gather(*[workbench.stop() for workbench in self.__workbench])

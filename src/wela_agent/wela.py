
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
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination

from wela_agent.agents.user_proxy_agent_ex import UserProxyAgentEx

class Wela:

    def __init__(
        self,
        model_client: ChatCompletionClient,
        workbench: Sequence[Workbench] | None,
        model_context: ChatCompletionContext | None,
        system_prompt: str,
        max_tool_iterations: int,
        memory: Sequence[Memory] | None,
        termination: TextMentionTermination        
    ) -> None:
        self.__assistant  = AssistantAgent(
            name                = "assistant",
            model_client        = model_client,
            workbench           = workbench,
            model_context       = model_context,
            system_message      = system_prompt,
            model_client_stream = True,
            max_tool_iterations = max_tool_iterations,
            memory              = memory
        )
        self.__user_proxy = UserProxyAgentEx("user_proxy")
        self.__team       = RoundRobinGroupChat(
            [
                self.__user_proxy,
                self.__assistant
            ],
            termination_condition=termination
        )

    async def chat(
        self,
        input_func: Optional[ Callable[[str, Optional[CancellationToken]], Awaitable[str | List[str|Image]]] ] = None,
        output_func: Optional[Callable[[str], None]] = None
    ):
        self.__user_proxy.input_func = input_func

        stream = self.__team.run_stream()
        async for message in stream:
            if isinstance(message, TaskResult):
                pass
            else:
                if message.source == self.__assistant.name:
                    if iscoroutinefunction(output_func):
                        await output_func(message)
                    else:
                        output_func(message)


import uuid
import asyncio

from typing import Sequence
from typing import AsyncGenerator

from autogen_core import Image
from autogen_core import CancellationToken
from autogen_agentchat.base import Response
from autogen_agentchat.agents import UserProxyAgent
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.messages import BaseAgentEvent
from autogen_agentchat.messages import HandoffMessage
from autogen_agentchat.messages import BaseChatMessage
from autogen_agentchat.messages import MultiModalMessage
from autogen_agentchat.messages import UserInputRequestedEvent

class UserProxyAgentEx(UserProxyAgent):

    async def on_messages_stream(
        self, messages: Sequence[BaseChatMessage], cancellation_token: CancellationToken
    ) -> AsyncGenerator[BaseAgentEvent | BaseChatMessage | Response, None]:
        """Handle incoming messages by requesting user input."""
        try:
            # Check for handoff first
            handoff = self._get_latest_handoff(messages)
            prompt = (
                f"Handoff received from {handoff.source}. Enter your response: " if handoff else "Enter your response: "
            )

            request_id = str(uuid.uuid4())

            input_requested_event = UserInputRequestedEvent(request_id=request_id, source=self.name)
            yield input_requested_event
            with UserProxyAgent.InputRequestContext.populate_context(request_id):
                user_input = await self._get_input(prompt, cancellation_token)

            # Return appropriate message type based on handoff presence
            if handoff:
                yield Response(chat_message=HandoffMessage(content=user_input, target=handoff.source, source=self.name))
            elif isinstance(user_input, str):
                yield Response(chat_message=TextMessage(content=user_input, source=self.name))
            elif isinstance(user_input, list) and all(isinstance(item, str | Image) for item in user_input):
                yield Response(chat_message=MultiModalMessage(content=user_input, source=self.name))

        except asyncio.CancelledError:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to get user input: {str(e)}") from e

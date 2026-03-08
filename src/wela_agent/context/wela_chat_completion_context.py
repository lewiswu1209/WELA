
from typing import List

from autogen_core.models import LLMMessage
from autogen_core.models import UserMessage
from autogen_core.models import SystemMessage
from autogen_core.model_context import ChatCompletionContext

class WelaChatCompletionContext(ChatCompletionContext):

    def __init__(self, initial_messages = None):
        super().__init__(initial_messages)
        self.session_meta_message: SystemMessage = None

    async def add_message(self, message: LLMMessage) -> None:
        if isinstance(message, UserMessage) and message.source == "SessionMeta":
            self.session_meta_message = SystemMessage(content=message.content)
        else:
            await super().add_message(message)

    async def get_messages(self) -> List[LLMMessage]:
        """Get at most `buffer_size` recent messages."""
        return self._messages + [self.session_meta_message]

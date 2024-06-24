
from schema.prompt.openai_chat import Message
from memory.buffer_memory import BufferMemory

class WindowBufferMemory(BufferMemory):
    def __init__(self, memory_key: str, window_size: int = 10) -> None:
        self.__window_size: int = window_size
        super().__init__(memory_key)

    def add_message(self, message: Message) -> None:
        messages = super().get_messages(None)
        messages.append(message)
        self._message_history = messages[-self.__window_size:]

__all__ = [
    "WindowBufferMemory"
]

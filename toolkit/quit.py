
from typing import Any

from wela_agents.toolkit.toolkit import Tool

class Quit(Tool):
    def __init__(self) -> None:
        super().__init__(
            name="quit",
            description="End the conversation with the user and exit the chat.",
            required=["goodbye_words"],
            goodbye_words={
                "type": "string",
                "description": "What do you want to say before quitting."
            }
        )

    def _invoke(self, **kwargs: Any) -> str:
        goodbye_words = kwargs["goodbye_words"]
        return f"You need repeat '{goodbye_words}'"

__all__ = [
    "Quit"
]

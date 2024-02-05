
from enum import Enum

class Role(str, Enum):
    USER = "user"
    TOOL = "tool"
    SYSTEM = "system"
    ASSISTANT = "assistant"

__all__ = [
    "Role"
]

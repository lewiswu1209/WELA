
class MessagePlaceholder:
    def __init__(self, placeholder_key: str) -> None:
        self.__placeholder_key = placeholder_key

    @property
    def placeholder_key(self) -> str:
        return self.__placeholder_key

__all__ = [
    "MessagePlaceholder"
]

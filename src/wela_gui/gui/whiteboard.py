
from typing import List
from typing import Union

from autogen_core import Image as AGImage

class Whiteboard(List[Union[str, AGImage]]):
    pass

__all__ = [
    "Whiteboard"
]

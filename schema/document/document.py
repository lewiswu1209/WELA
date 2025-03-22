
from typing import Dict

from typing_extensions import Required
from typing_extensions import TypedDict

class Document(TypedDict, total=False):

    metadata: Required[Dict]

    page_content: Required[str]


from typing import Any
from typing import Dict
from typing import List
from string import Formatter

class PromptTemplate:

    def __init__(self, template: str) -> None:
        self.__template: str = template

    def format(self, **kwargs: Any) -> str:
        if self.__template is None:
            return None
        return Formatter().format(self.__template, **kwargs)

class FewShotPromptTemplate(PromptTemplate):

    def __init__(self, prefix: str="", suffix: str="", examples: List[Dict]=[], example_template: PromptTemplate="") -> None:
        template = prefix
        for example in examples:
            template +=  example_template.format(**example)
        template += suffix

        PromptTemplate.__init__(self, template=template)

__all__ = [
    "PromptTemplate",
    "FewShotPromptTemplate"
]

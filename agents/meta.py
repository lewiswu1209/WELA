
import time

from typing import Any
from typing import List
from typing import Union
from typing import Optional
from typing import Generator

from memory.memory import Memory
from toolkit.toolkit import Toolkit
from models.model import Model
from models.openai_chat import OpenAIChat
from agents.conversation import ConversationAgent
from retriever.retriever import Retriever
from schema.template.openai_chat import ChatTemplate
from schema.template.openai_chat import MessageTemplate
from schema.template.openai_chat import MessagePlaceholder
from schema.template.openai_chat import SystemMessageTemplate
from schema.template.prompt_template import PromptTemplate
from schema.template.prompt_template import StringPromptTemplate

default_prompt = '''You are ChatGPT, a large language model trained by OpenAI, based on the GPT-3.5 architecture.'''

class Meta(ConversationAgent):
    def __init__(
        self,
        *,
        model: Model,
        prompt: str = default_prompt,
        memory: Memory = None,
        toolkit: Toolkit = None,
        retriever: Retriever = None,
        input_key: str = "__input__",
        output_key: str = "__output__",
        max_tokens: Optional[int] = None
    ) -> None:
        assert isinstance(model, OpenAIChat), "Unsupported model type"

        if isinstance(model, OpenAIChat):
            message_template_list: List[MessageTemplate] = []
            message_template_list.append(SystemMessageTemplate(StringPromptTemplate(prompt)))
            if memory:
                message_template_list.append(MessagePlaceholder(placeholder_key = memory.memory_key))
            if retriever:
                message_template_list.append(MessagePlaceholder(placeholder_key = retriever.retriever_key))
            message_template_list.append(SystemMessageTemplate(StringPromptTemplate("{__system_hint__}")))
            message_template_list.append(MessagePlaceholder(placeholder_key = input_key))
            prompt_template: PromptTemplate = ChatTemplate(message_template_list)

        super().__init__(
            model = model,
            prompt_template = prompt_template,
            toolkit = toolkit,
            memory = memory,
            retriever = retriever,
            input_key = input_key,
            output_key = output_key,
            max_tokens = max_tokens
        )

    def predict(self, **kwargs: Any) -> Union[Any, Generator[Any, None, None]]:
        kwargs["__system_hint__"] = "Current time is: {}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        return super().predict(**kwargs)

__all__ = [
    "Meta"
]

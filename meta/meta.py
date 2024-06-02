
import time

from typing import List
from typing import Generator

from meta.prompt import default_prompt
from memory.memory import Memory
from models.openai_chat import OpenAIChat
from toolkit.toolkit import Toolkit
from agents.conversation import ConversationAgent
from prompts.prompt_template import PromptTemplate
from prompts.messages_template import ChatTemplate
from prompts.messages_template import MessageTemplate
from prompts.messages_template import UserMessageTemplate
from prompts.messages_template import SystemMessageTemplate
from schema.message_placeholder import MessagePlaceholder

class Meta:
    def __init__(self, model: OpenAIChat, prompt: str = default_prompt, memory: Memory = None, toolkit: Toolkit = None) -> None:
        message_template_list: List[MessageTemplate] = []
        message_template_list.append(SystemMessageTemplate(PromptTemplate(prompt)))
        if memory:
            message_template_list.append(MessagePlaceholder(placeholder_key = memory.memory_key))
        message_template_list.append(SystemMessageTemplate(PromptTemplate("{system_hint}")))
        message_template_list.append(UserMessageTemplate(PromptTemplate("{input}")))

        self.__chat_template: ChatTemplate = ChatTemplate(message_template_list)
        self.__memory: Memory = memory

        self.__chain = ConversationAgent(
            model=model,
            chat_template=self.__chat_template,
            toolkit=toolkit,
            memory=self.__memory
        )
    def run(self, input: str) -> str | Generator:
        return self.__chain.run(
            input=input,
            system_hint="Current time is: {}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        )

__all__ = [
    "Meta"
]

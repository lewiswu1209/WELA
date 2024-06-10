
import re
import time

from typing import Any
from typing import List
from typing import Dict

from agents.llm import LLMAgent
from toolkit.toolkit import Tool
from toolkit.toolkit import Toolkit
from models.openai_chat import OpenAIChat

from schema.prompt.openai_chat import AIMessage
from schema.message_placeholder import MessagePlaceholder
from toolkit.weather import Weather
from toolkit.browsing.duckduckgo import DuckDuckGo
from toolkit.browsing.web_browser import WebBrowser
from prompts.prompt_template import PromptTemplate
from prompts.openai_chat import ChatTemplate
from prompts.openai_chat import MessageTemplate
from prompts.openai_chat import UserMessageTemplate
from prompts.openai_chat import SystemMessageTemplate

class Planner(Tool):
    def __init__(self, model: OpenAIChat) -> None:
        super().__init__(
            name="browsing",
            description="This tool is used to solve problems that need Internet information or complex problems that need to be solved step by step.",
            required=["problem"],
            problem={
                "type": "string",
                "description": "Problems that need to be solved"
            }
        )
        self.__model: OpenAIChat = model

    def __make_plan(self, problem: str):
        message_template_list: List[MessageTemplate] = [
            SystemMessageTemplate(
                PromptTemplate(
"Let's first understand the problem and devise a plan to solve the problem. "
"Please output the plan starting with the header 'Plan:' and then followed by a numbered list of steps. "
"Please make the plan the minimum number of steps required to accurately complete the task. "
"At the end of your plan, say '<END_OF_PLAN>'"
                )
            ),
            UserMessageTemplate(PromptTemplate("{problem}"))
        ]
        chat_template: ChatTemplate = ChatTemplate(message_template_list)
        agent = LLMAgent(
            model=self.__model,
            chat_template=chat_template,
            stop="<END_OF_PLAN>"
        )
        response_message = agent.run(problem=problem)
        return response_message
        # steps = []
        # for step in re.split("\n\s*\d+\. ", response_message)[1:]:
        #     steps.append( step.strip() )
        # return steps

    def _invoke(self, **kwargs: Any) -> str:
        problem = kwargs["problem"]
        return self.__make_plan(problem)

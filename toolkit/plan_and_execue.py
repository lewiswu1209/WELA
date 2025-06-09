
import re
import time

from typing import Any
from typing import Dict
from typing import Union
from typing import Generator
from collections import deque

from wela_agents.agents.llm import LLMAgent
from wela_agents.callback.event import ToolEvent
from wela_agents.toolkit.toolkit import Tool
from wela_agents.toolkit.toolkit import Toolkit
from wela_agents.toolkit.weather import Weather
from wela_agents.toolkit.definition import Definition
from wela_agents.toolkit.duckduckgo import DuckDuckGo
from wela_agents.toolkit.web_browser import WebBrowser
from wela_agents.models.openai_chat import OpenAIChat
from wela_agents.callback.callback import ToolCallback
from wela_agents.schema.template.openai_chat import ChatTemplate
from wela_agents.schema.template.openai_chat import MessagePlaceholder
from wela_agents.schema.template.openai_chat import UserMessageTemplate
from wela_agents.schema.template.openai_chat import SystemMessageTemplate
from wela_agents.schema.template.openai_chat import StringPromptTemplate

class ToolMessage(ToolCallback):
    def before_tool_call(self, event: ToolEvent) -> None:
        print("准备使用工具:{}\n参数:\n{}".format(event.tool_name, event.arguments))

    def after_tool_call(self, event: ToolEvent) -> None:
        print("工具'{}'的结果:\n{}".format(event.tool_name, event.result))

class Plan_And_Execute(Tool):
    def __init__(self, model, proxies) -> None:
        super().__init__(
            name="plan_and_execute",
            description="Plan and execute a series of tasks to achieve an objective",
            required=["objective"],
            objective={
                "type": "string",
                "description": "The objective to achieve"
            },
            additional ={
                "type": "string",
                "description": "Additional information for this task, such as the context of the task"
            },
        )
        self.__model = model
        self.__proxies = proxies

    def _invoke(self, **kwargs: Any) -> str:
        objective = kwargs["objective"]
        additional=kwargs.get("additional", ""),
        result = ""

        task_list = deque()
        compiled_tasks = deque()

        result = Planner(self.__model).predict(
            objective=objective
        )["content"]
        steps = [{"task_name": step.strip(), "result": ""} for step in re.split("\n\\s*\\d+\\.\\s", result)[1:]]
        task_list.extend(steps)
        compiled_tasks.append({"task_name": "Make a todo list", "result": result})

        while task_list:
            current_task = task_list.popleft()
            print("Current task: ", current_task)
            print("Compiled task_names: ", [task["task_name"] for task in compiled_tasks])
            print("Task list: ", task_list)
            result = Executor(self.__model, self.__proxies).predict(
                objective=objective,
                additional=additional,
                current_task=current_task["task_name"],
                context=ChatTemplate(
                    [
                        SystemMessageTemplate(
                            StringPromptTemplate("# Task name: {}\n# Result:\n{}".format(task["task_name"], task["result"]))
                        )
                        for task in compiled_tasks
                    ]
                ).format(),
                __system_hint__="Current time is: {}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            )["content"]
            current_task.update({"result": result})
            compiled_tasks.append(current_task)

        return result

class Planner(LLMAgent):
    def __init__(self, model: OpenAIChat) -> None:
        prompt_template = ChatTemplate(
            [
                SystemMessageTemplate(
                    StringPromptTemplate('''Let's first understand the problem and devise a plan to solve the problem.
Please output the plan starting with the header 'Plan:' and then followed by a numbered list of steps.
Please make the plan the minimum number of steps required to accurately complete the task.
At the end of your plan, say '<END_OF_PLAN>'.''')
                ),
                UserMessageTemplate(
                    StringPromptTemplate("{objective}")
                )
            ]
        )
        super().__init__(model, prompt_template, stop=["<END_OF_PLAN>"])

    def predict(self, **kwargs: Any) -> Union[Any, Generator[Any, None, None]]:
        return super().predict(**kwargs)

class Executor(LLMAgent):
    def __init__(self, model: OpenAIChat, proxies: Dict = None) -> None:
        prompt_template = ChatTemplate(
            [
                MessagePlaceholder(placeholder_key = "context"),
                UserMessageTemplate(
                    StringPromptTemplate('''Perform the following tasks: {current_task}.
Take into account previously completed tasks above.

This task is a step based on the following objectives: {objective}.
And here is the additional information you need to know: \n{additional}.
But for now, you just need to focus on the current task.''')
                ),
                SystemMessageTemplate(
                    StringPromptTemplate("{__system_hint__}")
                )
            ]
        )
        toolkit = Toolkit([Weather(), Definition(proxies), DuckDuckGo(proxies), WebBrowser(model, proxies), Plan_And_Execute(model, proxies)], callback=ToolMessage())
        super().__init__(model, prompt_template, toolkit=toolkit)

    def predict(self, **kwargs: Any) -> Union[Any, Generator[Any, None, None]]:
        return super().predict(**kwargs)

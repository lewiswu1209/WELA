
import re
import yaml

from typing import Any
from typing import Dict

from wela_agents.agents.llm import LLMAgent
from wela_agents.models.model import Model
from wela_agents.callback.event import ToolEvent
from wela_agents.agents.sequential import SimpleSequentialAgent
from wela_agents.agents.sequential import CycleSequentialAgent
from wela_agents.toolkit.toolkit import Tool
from wela_agents.toolkit.toolkit import Toolkit
from wela_agents.toolkit.weather import Weather
from wela_agents.toolkit.definition import Definition
from wela_agents.toolkit.duckduckgo import DuckDuckGo
from wela_agents.toolkit.web_browser import WebBrowser
from wela_agents.callback.callback import ToolCallback
from wela_agents.schema.template.openai_chat import ChatTemplate
from wela_agents.schema.template.openai_chat import MessagePlaceholder
from wela_agents.schema.template.openai_chat import UserMessageTemplate
from wela_agents.schema.template.openai_chat import StringPromptTemplate
from wela_agents.schema.template.prompt_template import PromptTemplate

def compare_plan(**kwargs) -> bool:
    inputs = kwargs["status"]
    completed_steps = inputs["completed_steps"]
    plan = inputs["plan"]

    # changed = False
    # if len(original) != len(fixed_plan):
    #     print(f"Step count changed from {len(original)} to {len(fixed_plan)}")
    #     changed = True
    # else:
    #     for i, (orig_step, fixed_step) in enumerate(zip(original, fixed_plan)):
    #         if orig_step != fixed_step:
    #             print(f"Step {i} changed: {orig_step} -> {fixed_step}")
    #             changed = True
    return len(completed_steps) < len(plan)

class ToolMessage(ToolCallback):
    def before_tool_call(self, event: ToolEvent) -> None:
        print("准备使用工具:{}\n参数:\n{}".format(event.tool_name, event.arguments))

    def after_tool_call(self, event: ToolEvent) -> None:
        print("工具'{}'的结果:\n{}".format(event.tool_name, event.result))

class Planner(LLMAgent):

    def __init__(self, model: Model, input_key: str, output_key: str) -> None:
        prompt_template = ChatTemplate(
            [
                UserMessageTemplate(
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
        super().__init__(
            model = model,
            prompt_template = prompt_template,
            stop = ["<END_OF_PLAN>"],
            input_key = input_key,
            output_key = output_key
        )

    def predict(self, **kwargs):
        response = super().predict(**kwargs)
        if not self.model.streaming:
            plan_response = response["content"]
        else:
            plan_response = ""
            for i in response:
                plan_response = i["content"]
        plan = [step.strip() for step in re.split("\n\\s*\\d+\\.\\s", plan_response)[1:]]

        return {
            "objective": kwargs["objective"],
            "infomation": [],
            "completed_steps": [],
            "plan": plan,
            "next_step": ""
        }

class Selector(LLMAgent):

    def __init__(self, model: Model, input_key: str, output_key: str) -> None:
        prompt_template: PromptTemplate = ChatTemplate(
            [
                MessagePlaceholder("infomation"),
                UserMessageTemplate(
                    StringPromptTemplate(
                        """# Objective
{objective}

# Completed Task
{completed_steps}

# Plan
{plan}

# Task
1. Repeat the given plan in the "Original Plan" section of the output
2. Select the next step to be completed based on the information and given plan with number
3. If the selected step is complex, please **replace** it with several sub steps
4. Reselect the next step to be completed based on the information and fixed plan with number
5. Output the modified plan in the "Fixed Plan" section of the output
6. Re numbering the 'Fixed Plan' section of the output from 1 to N

# Format
Please output the plan and the next step to be completed in the following format:
original_plan:
  - X. first step
  - X. second step
selected_step: X. the selected step to be completed
fixed_plan:
  - X. first step
  - X. second step
reselected_step: X. the selected step to be completed
<END_OF_PLAN>"""
                    )
                )
            ]
        )
        super().__init__(
            model = model,
            prompt_template = prompt_template,
            stop = ["<END_OF_PLAN>"],
            input_key = input_key,
            output_key = output_key,
        )

    def predict(self, **kwargs):
        inputs = kwargs[self.input_key]
        objective = inputs["objective"]
        infomation = inputs["infomation"]
        completed_steps = inputs["completed_steps"]
        plan = inputs["plan"]

        response_content = super().predict(
            objective = objective,
            infomation = "\n".join(f"{index+1}. {step}" for index, step in enumerate(infomation)),
            completed_steps = "\n".join(f"{index+1}. {step}" for index, step in enumerate(completed_steps)),
            plan = "\n".join(f"{index+1}. {step}" for index, step in enumerate(plan))
        )["content"]
        response_content = response_content.split('<END_OF_PLAN>', 1)[0]
        response_content = re.sub(r'^<think>.*?</think>', '', response_content, count=1, flags=re.DOTALL)
        response_content = response_content.strip('```yaml').strip('```').strip()
        response = yaml.safe_load(response_content)
        fixed_plan = [re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", item, count=1).strip() for item in response["fixed_plan"]]
        reselected_step = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", response["reselected_step"], count=1).strip()

        return {
            "objective": objective,
            "infomation": infomation,
            "completed_steps": completed_steps,
            "plan": fixed_plan,
            "next_step": reselected_step
        }

class Executor(LLMAgent):

    def __init__(self, model: Model, input_key: str, output_key: str, proxies: Dict = None) -> None:
        prompt_template = ChatTemplate(
            [
                MessagePlaceholder("infomation"),
                UserMessageTemplate(
                    StringPromptTemplate(
                        '''# Objective
{objective}

# Infomation
{infomation}

# Completed Task
{completed_steps}

# Plan
{plan}

# Current Step
{step}

# Constraint
1. You just need to focus on the current task without worrying about achieving the objective'''
                    )
                )
            ]
        )
        toolkit = Toolkit([Weather(), Definition(proxies), DuckDuckGo(proxies), WebBrowser(model, proxies)], callback=ToolMessage())
        super().__init__(
            model = model,
            prompt_template = prompt_template,
            input_key = input_key,
            output_key = output_key,
            toolkit = toolkit
        )

    def predict(self, **kwargs):
        inputs = kwargs[self.input_key]
        objective = inputs["objective"]
        infomation = inputs["infomation"]
        completed_steps = inputs["completed_steps"]
        plan = inputs["plan"]
        current_step = inputs["next_step"]

        response_content = super().predict(
            objective = objective,
            infomation = "\n".join(f"{index+1}. {step}" for index, step in enumerate(infomation)),
            completed_steps = "\n".join(f"{index+1}. {step}" for index, step in enumerate(completed_steps)),
            plan = "\n".join(f"{index+1}. {step}" for index, step in enumerate(plan)),
            step = current_step
        )["content"]
        completed_steps.append(current_step)
        infomation.append(response_content)
        return {
            "objective": objective,
            "infomation": infomation,
            "completed_steps": completed_steps,
            "plan": plan,
            "next_step": ""
        }

class Research(Tool):
    def __init__(self, model, model_reasoner, proxies) -> None:
        super().__init__(
            name="research",
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
        self.__model_reasoner = model_reasoner
        self.__proxies = proxies

    def _invoke(self, **kwargs: Any) -> str:
        objective = kwargs["objective"]
        result = ""

        planner = Planner(
            model=self.__model,
            input_key="objective",
            output_key="status"
        )
        selector = Selector(
            model=self.__model_reasoner,
            input_key="status",
            output_key="status"
        )
        executor = Executor(
            model=self.__model,
            input_key="status",
            output_key="status",
            proxies=self.__proxies
        )
        cycle_agent = CycleSequentialAgent(
            agents=[selector, executor],
            condition=compare_plan
        )
        agent = SimpleSequentialAgent(
            agents=[planner, cycle_agent]
        )
        result = agent.predict(
            objective = objective
        )

        return result["infomation"][-1] if result["infomation"] else "No information available."

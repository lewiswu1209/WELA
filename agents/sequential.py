
from typing import List

from agents.agent import Agent
from schema.prompt.openai_chat import Message

class SimpleSequentialAgent(Agent):
    def __init__(self, agents: List[Agent], input_key: str = "__input__", output_key: str = "__output__") -> None:
        self.__agents: List[Agent] = agents
        super().__init__(input_key, output_key)

    def predict(self, **kwargs: any) -> Message:
        prediction = None
        for agent in self.__agents:
            prediction = agent.predict(**kwargs)
            kwargs[agent.output_key] = prediction["content"]
        return prediction

__all__ = [
    "SimpleSequentialAgent"
]

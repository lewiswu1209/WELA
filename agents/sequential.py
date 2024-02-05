
from typing import List

from agents import Agent
from schema.message import AIMessage

class SimpleSequentialAgent(Agent):
    def __init__(self, agents: List[Agent], input_key: str = "input", output_key: str = "output") -> None:
        self.__agents: List[Agent] = agents
        super().__init__(input_key, output_key)

    def predict(self, **kwargs: any) -> AIMessage:
        predict = None
        for agent in self.__agents:
            predict = agent.predict(**kwargs)
            kwargs[agent.output_key] = predict["content"]
        return predict

__all__ = [
    "SimpleSequentialAgent"
]


from typing import List

from agents.agent import Agent
from schema.message import AIMessage

class SimpleSequentialAgent(Agent):
    def __init__(self, agents: List[Agent], input_key: str = "input", output_key: str = "output") -> None:
        self.__agents: List[Agent] = agents
        super().__init__(input_key, output_key)

    def predict(self, **kwargs: any) -> AIMessage:
        prediction = None
        for agent in self.__agents:
            prediction = agent.predict(**kwargs)
            kwargs[agent.output_key] = prediction["content"]
        return prediction

__all__ = [
    "SimpleSequentialAgent"
]

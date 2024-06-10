
import requests

from typing import Any

from toolkit.toolkit import Tool

class Weather(Tool):
    def __init__(self) -> None:
        super().__init__(
            name="get_weather_forecast",
            description="Get the weather forecast in a given location",
            required=["location"],
            location={
                "type": "string",
                "description": "The city. e.g. San+Francisco"
            }
        )

    def _invoke(self, **kwargs: Any) -> str:
        location = kwargs["location"]
        url: str = f"https://wttr.in/{location}?T"
        try:
            return requests.get(url).content.decode(encoding="utf-8")
        except Exception as e:
            return f"{e}"

__all__ = [
    "Weather"
]

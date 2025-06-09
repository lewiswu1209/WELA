
import json

from typing import Any
from curl_cffi import requests

from wela_agents.toolkit.toolkit import Tool

def convert_time_format(time_str: str) -> str:
    time_int = int(time_str)
    hours = time_int // 100
    minutes = time_int % 100

    return f"{hours:02d}:{minutes:02d}"

class Weather(Tool):
    def __init__(self) -> None:
        super().__init__(
            name="get_weather_forecast",
            description="Get the weather forecast for a given city",
            required=["city"],
            city={
                "type": "string",
                "description": "The city. e.g. San+Francisco"
            }
        )

    def _invoke(self, **kwargs: Any) -> str:
        city = kwargs["city"]
        url: str = f"https://wttr.in/{city}?format=j1"
        try:
            response = requests.get(url).content.decode(encoding="utf-8")
            data = json.loads(response)

            current_condition = data["current_condition"][0]
            weather = data["weather"]
            nearest_area = data["nearest_area"][0]

            forecast_str = f'''# Weather forecast
## Location
{nearest_area["areaName"][0]["value"]},{nearest_area["region"][0]["value"]},{nearest_area["country"][0]["value"]}
## Real-time Weather
- Weather: {current_condition["weatherDesc"][0]["value"]}
- Temperature (Feels like): {current_condition["temp_C"]}({current_condition["FeelsLikeC"]})°C
- Wind Direction/Speed: {current_condition["winddir16Point"]} {current_condition["windspeedKmph"]}km/h
'''

            for each_day in weather:
                date = f'''## {each_day["date"]}
|Time|Weather|Temperature (Feels like)|Wind Direction/Speed|
|-|-|-|-|
'''
                forecast_str += date
                for hourly in each_day["hourly"]:
                    hourly_time = convert_time_format(hourly["time"])
                    forecast_str += f'''|{hourly_time}|{hourly["weatherDesc"][0]["value"]}|{hourly["tempC"]}({hourly["FeelsLikeC"]})°C|{hourly["winddir16Point"]} {hourly["windspeedKmph"]}-{hourly["WindGustKmph"]} km/h|
'''
            return forecast_str
        except Exception as e:
            return f"{e}"

__all__ = [
    "Weather"
]

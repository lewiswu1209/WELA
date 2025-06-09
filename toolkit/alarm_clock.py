
from typing import Any

from wela_agents.toolkit.toolkit import Tool

class AlarmClock(Tool):
    def __init__(self) -> None:
        super().__init__(
            name="set_alarm_clock",
            description="Set an alarm to notify at a specific date and time for you.",
            required=["date_time", "reason"],
            date_time={
                "type": "string",
                "description": "The date and time to set the alarm, in the format 'YYYY-MM-DD HH:MM'."
            },
            reason={
                "type": "string",
                "description": "The reason for setting the alarm. IMPORTANT!!! You SHOULD take note of all information that might be needed."
            }
        )

    def _invoke(self, **kwargs: Any) -> str:
        return "Alarm clock set successfully"

__all__ = [
    "AlarmClock"
]


from functools import partial
from typing_extensions import Annotated
from autogen_core.tools import FunctionTool

def __set_alarm_clock(
        callback,
        date_time: Annotated[str, "The date and time to set the alarm, in the format 'YYYY-MM-DD HH:MM'."],
        reason: Annotated[str, "The reason for setting the alarm. IMPORTANT!!! You SHOULD take note of all information that might be needed."]
    ):
    callback(date_time, reason)
    return "Alarm clock set successfully"

def SetAlarmClockTool(callback):
    return FunctionTool(
        func=partial(__set_alarm_clock, callback),
        name="set_alarm_clock",
        description="Set an alarm to notify at a specific date and time for you.",
        strict=True
    )

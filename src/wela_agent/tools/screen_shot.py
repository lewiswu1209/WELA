
import pygetwindow

from PIL import Image
from PIL import ImageGrab
from typing import Literal
from functools import partial
from autogen_core import Image as AGImage
from autogen_core.tools import FunctionTool
from typing_extensions import Annotated

def __screen_shot(
    callback,
    mode: Annotated[Literal["current_window", "full_screen"], "Screenshot mode: current_window = capture active window, full_screen = capture full screen"]
):
    target_width = 600
    try:
        if mode == 'current_window':
            active_window = pygetwindow.getActiveWindow()
            if not active_window:
                raise Exception("Can not get active window.")

            left, top = active_window.topleft
            right, bottom = active_window.bottomright
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
        else:
            screenshot = ImageGrab.grab()
        screenshot = screenshot.convert('RGB')

        original_width, original_height = screenshot.size
        if original_width > target_width:
            scale_ratio = target_width / original_width
            target_height = int(original_height * scale_ratio)
            screenshot = screenshot.resize(
                (target_width, target_height), 
                Image.Resampling.LANCZOS
            )
        callback(AGImage(screenshot))
        return "Screenshot taken successfully. You should repeat 'Okay, I will wait to receive the screenshot'."
    except Exception as e:
        return repr(e)

def ScreenShotTool(callback):
    return FunctionTool(
        partial(__screen_shot, callback),
        name="capture_user_screen",
        description="Get the user's screenshot."
    )

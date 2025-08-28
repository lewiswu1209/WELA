
import base64
import pygetwindow as gw

from io import BytesIO
from PIL import Image
from PIL import ImageGrab
from typing import Any
from typing import Callable

from wela_agents.toolkit.toolkit import Tool
from wela_agents.toolkit.tool_result import ToolResult
from wela_agents.toolkit.tool_result import Attachment

class ScreenShot(Tool):
    def __init__(self) -> None:
        super().__init__(
            name="capture_user_screenshot",
            description="Get the user's screenshot.",
            required=["mode"],
            mode={
                "type": "string",
                "description": "`current_window` or `full_screen`",
            }
        )

    def _invoke(self, callback: Callable = None, **kwargs: Any) -> str:
        mode = kwargs["mode"]
        jpg_quality = 80
        target_width = 600
        try:
            # 根据模式捕获不同范围的截图
            if mode == 'current_window':
                # 获取当前活动窗口
                active_window = gw.getActiveWindow()
                if not active_window:
                    raise Exception("无法获取当前活动窗口")
                
                # 捕获窗口区域
                left, top = active_window.topleft
                right, bottom = active_window.bottomright
                screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
            else:  # 默认全屏
                screenshot = ImageGrab.grab()

            # 转换为RGB模式(因为JPG不支持透明通道)
            screenshot = screenshot.convert('RGB')
            # 计算缩放尺寸：宽度固定为600，等比例缩放，宽度不足600则不缩放
            original_width, original_height = screenshot.size
            
            if original_width > target_width:
                scale_ratio = target_width / original_width
                target_height = int(original_height * scale_ratio)
                # 使用高质量缩放算法
                screenshot = screenshot.resize(
                    (target_width, target_height), 
                    Image.Resampling.LANCZOS
                )

            buffer = BytesIO()
            screenshot.save(
                buffer,
                format='JPEG',
                quality=jpg_quality,  # 设置JPG质量
                optimize=True,  # 优化Huffman编码
                progressive=True  # 渐进式JPG，提升加载体验
            )

            buffer.seek(0)
            image_data = buffer.read()
            base64_encoded = base64.b64encode(image_data).decode('utf-8')

            data_url = f"data:image/jpeg;base64,{base64_encoded}"

            return ToolResult(
                result="Screenshot taken successfully. User will send it to you soon.",
                attachment=[
                    Attachment(type="image_url", content=data_url)
                ]
            )

        except Exception as e:
            raise RuntimeError(f"Failed to take screenshot: {e}")

__all__ = [
    "ScreenShot"
]

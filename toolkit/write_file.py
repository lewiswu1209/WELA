
from typing import Any
from typing import Callable
from pathlib import Path

from wela_agents.toolkit.toolkit import Tool
from wela_agents.toolkit.tool_result import ToolResult

class WriteFile(Tool):
    def __init__(self) -> None:
        super().__init__(
            name="write_file",
            description="Write content to a file (creates new file if it doesn't exist, overwrites if it does).",
            required=["file_path", "content"],
            file_path={
                "type": "string",
                "description": "The full path and name of the file to write to, including file extension."
            },
            content={
                "type": "string",
                "description": "The content to be written into the file. Can include text, numbers, or symbols as needed."
            }
        )

    def _invoke(self, callback: Callable = None, **kwargs: Any) -> str:
        file_path = kwargs.get("file_path")
        content = kwargs.get("content")

        if not file_path or not content:
            return ToolResult(
                result="Failed to write file: missing required parameters (file_path and content are required)"
            )

        try:
            file_path_obj = Path(file_path)

            if not file_path_obj.parent.exists():
                file_path_obj.parent.mkdir(parents=True, exist_ok=True)

            file_path_obj.write_text(content, encoding='utf-8')

            if file_path_obj.exists():
                file_size = file_path_obj.stat().st_size
                return ToolResult(
                    result=f"File written successfully:\n"
                           f"Path: {file_path}\n"
                           f"Size: {file_size} bytes"
                )
            else:
                return ToolResult(
                    result="File write reported success but file not found"
                )
        except PermissionError:
            return ToolResult(
                result=f"Permission denied: Unable to write file at {file_path}. Check your permissions."
            )
        except IsADirectoryError:
            return ToolResult(
                result=f"Cannot write file: {file_path} is a directory"
            )
        except Exception as e:
            return ToolResult(
                result=f"Failed to write file: {str(e)}"
            )

__all__ = [
    "WriteFile"
]

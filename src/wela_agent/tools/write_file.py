
from pathlib import Path

from typing_extensions import Annotated
from autogen_core.tools import FunctionTool

def __write_text_file(
        file_path: Annotated[str, "Path to the file to write to (relative to project directory)"],
        content: Annotated[str, "Content to write to the file"]
    ) -> str:
        if not file_path or not content:
            return "Failed to write file: missing required parameters (file_path and content are required)"

        try:
            file_path_obj = Path(file_path)

            if not file_path_obj.parent.exists():
                file_path_obj.parent.mkdir(parents=True, exist_ok=True)

            file_path_obj.write_text(content, encoding='utf-8')

            if file_path_obj.exists():
                file_size = file_path_obj.stat().st_size
                result =f"""File written successfully:
Path: {file_path}
Size: {file_size} bytes
"""
                return result
            else:
                return "File write reported success but file not found"
        except PermissionError:
            return f"Permission denied: Unable to write file at {file_path}. Check your permissions."
        except IsADirectoryError:
            return f"Cannot write file: {file_path} is a directory"
        except Exception as e:
            return f"Failed to write file: {str(e)}"

WriteTextFileTool = FunctionTool(
    func=__write_text_file,
    name="write_text_file",
    description="Write content to a file.",
    strict=True
)

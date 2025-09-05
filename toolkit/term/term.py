
import asyncio

from typing import Any
from typing import Callable

from wela_agents.toolkit.toolkit import Tool
from wela_agents.toolkit.tool_result import ToolResult

from toolkit.term.tools.command_executor import CommandExecutor
from toolkit.term.tools.tty_output_reader import TtyOutputReader
from toolkit.term.tools.send_control_character import SendControlCharacter

class TermWriter(Tool):

    def __init__(self, shell) -> None:
        super().__init__(
            name="write_to_terminal",
            description="Writes text to the active terminal session (like running a command).",
            required=["command"],
            command={
                "type": "string",
                "description": "The command to run or text to write. Note that you are using Windows."
            }
        )
        self.__shell = shell

    def _invoke(self, callback: Callable = None, **kwargs: Any) -> str:
        command = kwargs["command"]
        if not command:
            return ToolResult(
                result=f"command is required"
            )

        executor = CommandExecutor(self.__shell)

        async def do_write():
            before_buffer = TtyOutputReader.get_buffer()
            before_lines = len(before_buffer.split("\n"))

            await executor.execute_command(command)

            after_buffer = TtyOutputReader.get_buffer()
            after_lines = len(after_buffer.split("\n"))
            diff = after_lines - before_lines

            msg = (f"{diff} lines were output after sending the command to the terminal. "
                   f"Read the last {diff} lines of terminal contents to orient yourself. "
                   f"Never assume that the command was executed or that it was successful.")
            return msg

        result_msg = asyncio.run(do_write())
        return ToolResult(
            result=result_msg
        )

class TermReader(Tool):

    def __init__(self) -> None:
        super().__init__(
            name="read_terminal_output",
            description="Reads the output from the active terminal session",
            required=["linesOfOutput"],
            linesOfOutput={
                "type": "number",
                "description": "How many lines from the bottom to read"
            }
        )

    def _invoke(self, callback: Callable = None, **kwargs: Any) -> str:
        lines_of_output = kwargs["linesOfOutput"]
        if not lines_of_output:
            return ToolResult(
                result=f"command is required"
            )

        output = TtyOutputReader.call(lines_of_output)
        return ToolResult(
            result=output
        )

class TermControl(Tool):

    def __init__(self, shell) -> None:
        super().__init__(
            name="send_control_character",
            description="Sends a control character to the active terminal (like Ctrl-C)",
            required=["letter"],
            letter={
                "type": "string",
                "description": "Letter for the control char (e.g. 'C' for Ctrl-C)"
            }
        )
        self.__shell = shell

    def _invoke(self, callback: Callable = None, **kwargs: Any) -> str:
        letter = kwargs["letter"]
        if not letter:
            return ToolResult(
                result=f"command is required"
            )

        sender = SendControlCharacter(self.__shell)
        try:
            sender.send(letter)
        except Exception as e:
            return ToolResult(
                result={"error": str(e)}
            )

        return ToolResult(
            result=f"Sent control character: Control-{letter.upper()}"
        )

__all__ = [
    "TermWriter",
    "TermReader",
    "TermControl"
]

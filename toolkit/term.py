
import re
import pexpect

from typing import Any
from typing import Callable
from pexpect.popen_spawn import PopenSpawn

from wela_agents.toolkit.toolkit import Tool
from wela_agents.toolkit.tool_result import ToolResult

class CommandPrompt(PopenSpawn):

    prompt_pattern = r"[A-Za-z]:\\[^(\r\n)]+?>"

    def __init__(self, timeout = 30, maxread = 2000, searchwindowsize = None, logfile = None, cwd = None, env = None, encoding = None, codec_errors = "strict", preexec_fn = None):
        super().__init__("cmd.exe", timeout, maxread, searchwindowsize, logfile, cwd, env, encoding, codec_errors, preexec_fn)
        self.last_prompt = None
        self.expect(CommandPrompt.prompt_pattern, timeout=10)

    def expect(self, pattern, timeout=-1, searchwindowsize=-1, async_=False):
        pre_prompt = self.last_prompt
        index = super().expect(pattern, timeout, searchwindowsize, async_)
        if isinstance(self.match, re.Match):
            self.last_prompt = self.after
        else:
            self.last_prompt = pre_prompt
        return index

class TermWriter(Tool):

    def __init__(self, shell: CommandPrompt) -> None:
        super().__init__(
            name="write_to_terminal",
            description="Writes text to the active terminal session (like running a command).",
            required=["command"],
            command={
                "type": "string",
                "description": "The command to run or text to write. Note that you are using Windows Command Line Prompt."
            }
        )
        self.__shell = shell

    def _invoke(self, callback: Callable = None, **kwargs: Any) -> str:
        command = kwargs["command"]
        if not command:
            return ToolResult(
                result=f"command is required"
            )

        buff = self.__shell.last_prompt

        continuous_idle_count = 0
        new_output = ""
        self.__shell.sendline(command)
        index = self.__shell.expect([CommandPrompt.prompt_pattern, pexpect.TIMEOUT], timeout=0.2)

        while index != 0:
            old_output = new_output
            new_output = self.__shell.before
            if new_output == old_output:
                continuous_idle_count += 1
                if continuous_idle_count >= 25:
                    break
            else:
                continuous_idle_count = 0
            index = self.__shell.expect([CommandPrompt.prompt_pattern, pexpect.TIMEOUT], timeout=0.2)

        return ToolResult(
            result = buff + self.__shell.before + (self.__shell.after if isinstance(self.__shell.match, re.Match) else "")
        )

class TermReader(Tool):

    def __init__(self, shell: CommandPrompt) -> None:
        super().__init__(
            name="read_terminal_output",
            description="Reads the output from the active terminal session",
            required=[]
        )
        self.__shell = shell

    def _invoke(self, callback: Callable = None, **kwargs: Any) -> str:
        buff = self.__shell.last_prompt
        self.__shell.expect([CommandPrompt.prompt_pattern, pexpect.TIMEOUT], timeout=0.2)

        return ToolResult(
            result = buff + self.__shell.before + (self.__shell.after if isinstance(self.__shell.match, re.Match) else "")
        )

__all__ = [
    "TermWriter",
    "TermReader"
]

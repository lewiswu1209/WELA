
from typing import Any
from typing import Dict
from typing import Union
from typing import Literal
from typing import Optional
from pydantic import BaseModel
from autogen_ext.tools.mcp import McpWorkbench as BaseMcpWorkbench
from autogen_ext.tools.mcp import SseServerParams
from autogen_ext.tools.mcp import StdioServerParams
from autogen_ext.tools.mcp import StreamableHttpServerParams

class StdioParams(BaseModel):
    type: Literal["stdio"] = "stdio"
    command: str
    args: list[str] = []
    env: Optional[Dict[str, str]] = None
    read_timeout_seconds: float = 5

class SseParams(BaseModel):
    type: Literal["sse"] = "sse"
    url: str
    headers: Optional[Dict[str, Any]] = None
    timeout: float = 5
    sse_read_timeout: float = 300

class HttpParams(BaseModel):
    type: Literal["http"] = "http"
    url: str
    headers: Optional[Dict[str, Any]] = None
    timeout: float = 30.0
    sse_read_timeout: float = 300.0
    terminate_on_close: bool = True

class McpWorkbench(BaseMcpWorkbench):

    def __init__(self, params: Union[StdioParams, SseParams, HttpParams, Dict[str, Any]]) -> None:

        if isinstance(params, dict):
            p_type = params.get("type")
            if p_type == "stdio":
                params = StdioParams(**params)
            elif p_type == "sse":
                params = SseParams(**params)
            elif p_type == "http":
                params = HttpParams(**params)
            else:
                raise ValueError(f"未知的 params.type: {p_type}")

        if isinstance(params, StdioParams):
            server_params = StdioServerParams(
                command=params.command,
                args=params.args,
                env=params.env,
                read_timeout_seconds=params.read_timeout_seconds,
            )

        elif isinstance(params, SseParams):

            server_params = SseServerParams(
                url=params.url,
                headers=params.headers,
                timeout=params.timeout,
                sse_read_timeout=params.sse_read_timeout,
            )

        elif isinstance(params, HttpParams):
            server_params = StreamableHttpServerParams(
                url=params.url,
                headers=params.headers,
                timeout=params.timeout,
                sse_read_timeout=params.sse_read_timeout,
                terminate_on_close=params.terminate_on_close,
            )

        else:
            raise TypeError(f"params 类型错误: {type(params)}")

        super().__init__(server_params)

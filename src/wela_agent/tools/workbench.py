
from typing import Any
from typing import Dict
from typing import Union
from typing import Optional
from pydantic import Field
from pydantic import BaseModel
from autogen_ext.tools.mcp import McpWorkbench as BaseMcpWorkbench
from autogen_ext.tools.mcp import StdioServerParams
from autogen_ext.tools.mcp import StreamableHttpServerParams

class StdioParams(BaseModel):
    type: str = Field("stdio")
    command: str
    args: list[str]
    env: Optional[Dict[str, str]] = None

class HttpParams(BaseModel):
    type: str = Field("http")
    url: str
    headers: Optional[Dict[str, str]] = None

class McpWorkbench(BaseMcpWorkbench):
    def __init__(self, params: Union[StdioParams, HttpParams, Dict[str, Any]]) -> None:
        if isinstance(params, dict):
            if params.get("type") == "stdio":
                params = StdioParams(**params)
            elif params.get("type") == "http":
                params = HttpParams(**params)
            else:
                raise ValueError("无效的 params 类型")

        if isinstance(params, StdioParams):
            server_params = StdioServerParams(
                command=params.command, args=params.args, env=params.env
            )
        elif isinstance(params, HttpParams):
            server_params = StreamableHttpServerParams(
                url=params.url, headers=params.headers
            )
        else:
            raise TypeError("params 类型错误")
        
        super().__init__(server_params)

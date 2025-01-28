from helpers.tool import Tool, Response
from extensions.system_prompt.system_prompt import (
    get_tools_prompt,
)


class Unknown(Tool):
    async def execute(self, **kwargs):
        tools = get_tools_prompt(self.agent)
        return Response(
            message=self.agent.read_prompt(
                "fw.tool_not_found.md", tool_name=self.name, tools_prompt=tools
            ),
            break_loop=False,
        )

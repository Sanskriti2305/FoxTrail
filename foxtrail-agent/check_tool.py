import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="tigergraph-mcp",
        args=["-v"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            for t in tools.tools:
                if t.name == "tigergraph__install_query":
                    print(t.input_schema)

if __name__ == "__main__":
    asyncio.run(main())
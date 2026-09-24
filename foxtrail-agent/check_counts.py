import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(command="tigergraph-mcp", args=["-v"])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                "tigergraph__get_edge_count",
                arguments={"graph_name": "FoxTrail", "edge_type": "MADE"}
            )
            print("MADE edge count:", result)

if __name__ == "__main__":
    asyncio.run(main())
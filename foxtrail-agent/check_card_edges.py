import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(command="tigergraph-mcp", args=["-v"])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                "tigergraph__get_node_edges",
                arguments={
                    "graph_name": "FoxTrail",
                    "vertex_type": "Card",
                    "vertex_id": "21139242.0150.0visa166.0debit"
                }
            )
            print(result)

if __name__ == "__main__":
    asyncio.run(main())
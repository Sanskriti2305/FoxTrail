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
            print("✅ Connected to MCP server.")

            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")

            result = await session.call_tool(
                "tigergraph__run_installed_query",
                arguments={
                    "graph_name": "FoxTrail",
                    "query_name": "get_transaction_details",
                    "params": {"txn_id": "3000001"}
                }
            )
            print("Query result:")
            print(result)

if __name__ == "__main__":
    asyncio.run(main())
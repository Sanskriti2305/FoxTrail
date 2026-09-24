import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(command="tigergraph-mcp", args=["-v"])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                "tigergraph__run_installed_query",
                arguments={
                    "graph_name": "FoxTrail",
                    "query_name": "resolve_case_card_id",
                    "params": {"customer_id": "C12382", "k_index": 1}
                }
            )
            print(result)

if __name__ == "__main__":
    asyncio.run(main())
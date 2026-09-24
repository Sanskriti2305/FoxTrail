import asyncio
from tg_tools import call_tg_tool

async def main():
    result = await call_tg_tool(
        "tigergraph__get_query_metadata",
        {"graph_name": "FoxTrail", "query_name": "resolve_case_card_id"}
    )
    print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(main())
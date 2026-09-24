import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

QUERIES = {
    "get_transaction_details": """
CREATE QUERY get_transaction_details(STRING txn_id) {
  Txn = {Transaction.*};
  Txn = SELECT t FROM Txn:t WHERE t.transaction_id == txn_id;
  PRINT Txn;
}
""",
    "get_card_timeline": """
CREATE QUERY get_card_timeline(STRING card_id) {
  Start = {Card.*};
  Start = SELECT c FROM Start:c WHERE c.card_id == card_id;
  Txns = SELECT t FROM Start:c -(MADE)-> Transaction:t
         ORDER BY t.ts ASC;
  PRINT Txns;
}
""",
    "find_shared_device_cards": """
CREATE QUERY find_shared_device_cards(STRING device_id) {
  Dev = {DeviceProfile.*};
  Dev = SELECT d FROM Dev:d WHERE d.device_profile_id == device_id;
  Txns = SELECT t FROM Dev:d -(reverse)-> Transaction:t;
  Cards = SELECT c FROM Txns:t -(rev_MADE)-> Card:c;
  PRINT Cards;
}
""",
    "find_similar_closed_cases": """
CREATE QUERY find_similar_closed_cases(STRING card_id) {
  Start = {Card.*};
  Start = SELECT c FROM Start:c WHERE c.card_id == card_id;
  Cases = SELECT cc FROM Start:c -(ON_CARD)- ClosedCase:cc;
  PRINT Cases;
}
""",
}

async def main():
    server_params = StdioServerParameters(
        command="tigergraph-mcp",
        args=["-v"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Connected to MCP server.")

            for name, gsql in QUERIES.items():
                print(f"\nInstalling: {name}")
                result = await session.call_tool(
                    "tigergraph__install_query",
                    arguments={
                        "graph_name": "FoxTrail",
                        "query_text": gsql,
                    }
                )
                print(result)

if __name__ == "__main__":
    asyncio.run(main())
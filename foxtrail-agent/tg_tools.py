import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def call_tg_tool(tool_name: str, arguments: dict):
    server_params = StdioServerParameters(command="tigergraph-mcp", args=["-v"])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments)
            return result

async def run_query(query_name: str, params: dict):
    result = await call_tg_tool(
        "tigergraph__run_installed_query",
        {"graph_name": "FoxTrail", "query_name": query_name, "params": params}
    )
    return result

import json
import re

def extract_json(result):
    """Pull the first ```json ... ``` block out of an MCP tool result and parse it."""
    text = result.content[0].text
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON block found in result: {text}")
    return json.loads(match.group(1))

def summarize_timeline(timeline_data):
    txns = timeline_data["data"]["result"][0]["Txns"]
    if not txns:
        return {"count": 0}

    amounts = [t["attributes"]["amount"] for t in txns]
    risk_scores = [t["attributes"]["risk_score"] for t in txns]
    channels = [t["attributes"]["channel"] for t in txns]

    return {
        "count": len(txns),
        "total_amount": round(sum(amounts), 2),
        "avg_amount": round(sum(amounts) / len(amounts), 2),
        "min_amount": min(amounts),
        "max_amount": max(amounts),
        "risk_score_min": min(risk_scores),
        "risk_score_max": max(risk_scores),
        "channel_counts": {c: channels.count(c) for c in set(channels)},
        "first_ts": txns[0]["attributes"]["ts"],
        "last_ts": txns[-1]["attributes"]["ts"],
    }
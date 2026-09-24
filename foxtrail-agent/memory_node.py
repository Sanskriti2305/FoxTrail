from tg_tools import run_query, extract_json


def map_outcome(verdict: str) -> str:
    # ClosedCase.outcome expects "confirmed_fraud" or "cleared", per closed_cases_history.csv
    if verdict == "fraud":
        return "confirmed_fraud"
    return "cleared"


async def memory_node(state: dict) -> dict:
    graph_case_id = f"CASE-{state['case_id']}"

    txn_ts = None
    for e in state["evidence"]:
        if e["ref"] == "query:get_transaction_details":
            try:
                txn_ts = e["raw"]["data"]["result"][0]["Txn"][0]["attributes"]["ts"]
            except (KeyError, IndexError):
                pass

    params = {
        "case_id": graph_case_id,
        "card_id": state["resolved_card_id"],
        "flagged_txn_id": state["flagged_txn_id"],
        "outcome": map_outcome(state["verdict"]),
        "pattern": state["pattern"] if state["pattern"] else "none",
        "opened_at": state.get("opened_at", ""),
        "closed_at": txn_ts or "",
        "exposure_usd": state["exposure_usd"],
        "n_txns": len(state["affected_txn_ids"]),
        "analyst_notes": state["summary"],
    }

    result = await run_query("write_case_to_graph", params)
    state["tool_calls"] = state.get("tool_calls", 0) + 1
    result_data = extract_json(result)

    write_succeeded = result_data.get("success", False)
    state["written_to_graph"] = write_succeeded
    state["graph_case_id"] = graph_case_id if write_succeeded else ""

    state["evidence"].append({
        "claim": f"Case written to graph as {graph_case_id}" if write_succeeded
                  else "Failed to write case to graph",
        "source": "graph",
        "ref": "query:write_case_to_graph",
        "entity_ids": [graph_case_id],
        "raw": result_data
    })

    return state
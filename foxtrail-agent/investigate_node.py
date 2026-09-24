from tg_tools import run_query, extract_json
import json

def parse_card_hint(hint: str):
    # "C12382-K1" -> ("C12382", 1)
    customer_id, k_part = hint.split("-K")
    return customer_id, int(k_part)


async def investigate_node(state: dict) -> dict:
    state["evidence"] = state.get("evidence", [])
    state["tool_calls"] = state.get("tool_calls", 0)

    # 1. Fetch the flagged transaction's full details
    txn_result = await run_query(
        "get_transaction_details",
        {"txn_id": state["flagged_txn_id"]}
    )
    state["tool_calls"] += 1
    txn_data = extract_json(txn_result)
    state["evidence"].append({
        "claim": "Flagged transaction details retrieved",
        "source": "graph",
        "ref": "query:get_transaction_details",
        "entity_ids": [state["flagged_txn_id"]],
        "raw": txn_data
    })

    # 2. Resolve the "-K1"/"-K2" hint into real customer_id + k_index
    customer_id, k_index = parse_card_hint(state["card_id_hint"])
    resolved_result = await run_query(
        "resolve_case_card_id",
        {"customer_id": customer_id, "k_index": k_index}
    )
    state["tool_calls"] += 1
    resolved_data = extract_json(resolved_result)
    print("DEBUG resolved_data:", json.dumps(resolved_data, indent=2))
    state["evidence"].append({
        "claim": "Card ID resolved from case hint",
        "source": "graph",
        "ref": "query:resolve_case_card_id",
        "entity_ids": [state["card_id_hint"]],
        "raw": resolved_data
    })

    # 3. Pull the real card_id out of the query result
    if not resolved_data.get("success", True):
        raise RuntimeError(
            f"resolve_case_card_id failed for {state['card_id_hint']}: "
            f"{resolved_data.get('summary', 'unknown error')}"
        )

    if "data" in resolved_data:
        result_list = resolved_data["data"]["result"]
    else:
        result_list = resolved_data["result"]

    cards = result_list[0]["Cards"] if result_list else []

    # Cards come back sorted by first transaction time (per the query's ORDER BY).
    # k_index is 1-based ("-K1", "-K2", ...), so card k_index maps to cards[k_index - 1].
    if len(cards) >= k_index:
        state["resolved_card_id"] = cards[k_index - 1]["attributes"]["card_id"]
    else:
        raise RuntimeError(
            f"Expected at least {k_index} card(s) for customer {customer_id}, "
            f"but only found {len(cards)}"
        )

    # 4. Initialize fields that later nodes will build on
    state.setdefault("similar_prior_cases", [])
    state.setdefault("shared_device_cards", [])
    state.setdefault("connected_card_ids", [])
    state.setdefault("connected_device_profiles", [])
    state.setdefault("affected_txn_ids", [state["flagged_txn_id"]])
    state.setdefault("first_suspicious_txn_id", state["flagged_txn_id"])

    # A single flagged transaction with no other evidence yet counts as one signal
    state["is_single_signal"] = True

    return state
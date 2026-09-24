from tg_tools import run_query, extract_json, summarize_timeline

# A device profile shared by many cards is a generic fingerprint
# (same OS/browser/screen), not evidence of one shared physical device.
# Real device-sharing rings are small; treat large clusters as noise.
SHARED_DEVICE_SUSPICIOUS_MAX = 5
async def gather_evidence_node(state: dict) -> dict:
    state["evidence"] = state.get("evidence", [])
    state["tool_calls"] = state.get("tool_calls", 0)
    card_id = state["resolved_card_id"]

    # 1. Card timeline (summarized — see tg_tools.summarize_timeline)
    timeline_result = await run_query("get_card_timeline", {"card_id": card_id})
    state["tool_calls"] += 1
    timeline_data = extract_json(timeline_result)
    timeline_summary = summarize_timeline(timeline_data)
    state["evidence"].append({
        "claim": "Card transaction timeline retrieved",
        "source": "graph",
        "ref": "query:get_card_timeline",
        "entity_ids": [card_id],
        "raw": timeline_summary
    })

    # 2. Similar closed cases
    cases_result = await run_query("find_similar_closed_cases", {"card_id": card_id})
    state["tool_calls"] += 1
    cases_data = extract_json(cases_result)
    cases_list = cases_data["data"]["result"][0]["Cases"]
    own_case_id = f"CASE-{state['case_id']}"
    case_ids = [
        c["attributes"].get("case_id", c["v_id"])
        for c in cases_list
        if c["attributes"].get("case_id", c["v_id"]) != own_case_id
    ]
    state["evidence"].append({
        "claim": f"Checked for similar past closed cases ({len(case_ids)} found)",
        "source": "graph",
        "ref": "query:find_similar_closed_cases",
        "entity_ids": [card_id],
        "raw": cases_data
    })
    state["similar_prior_cases"] = case_ids
    if case_ids:
        state["is_single_signal"] = False

    # 3. Device lookup (may be empty — that's a valid outcome)
    device_result = await run_query(
        "get_transaction_device",
        {"txn_id": state["flagged_txn_id"]}
    )
    state["tool_calls"] += 1
    device_data = extract_json(device_result)
    dev_list = device_data["data"]["result"][0]["Dev"]

    if dev_list:
        device_id = dev_list[0]["attributes"]["device_profile_id"]
        state["evidence"].append({
            "claim": "Device profile found for flagged transaction",
            "source": "graph",
            "ref": "query:get_transaction_device",
            "entity_ids": [state["flagged_txn_id"], device_id],
            "raw": device_data
        })

        # 4. Shared device cards — only runs if we found a device
        shared_result = await run_query("find_shared_device_cards", {"device_id": device_id})
        state["tool_calls"] += 1
        shared_data = extract_json(shared_result)
        shared_cards = shared_data["data"]["result"][0]["Cards"]
        shared_card_ids = [c["attributes"].get("card_id", c["v_id"]) for c in shared_cards]
        # Exclude this case's own card from the "shared with others" list
        other_shared_cards = [c for c in shared_card_ids if c != card_id]

        is_suspicious_cluster = 0 < len(other_shared_cards) <= SHARED_DEVICE_SUSPICIOUS_MAX

        if len(other_shared_cards) > SHARED_DEVICE_SUSPICIOUS_MAX:
            note = (f"Device profile shared by {len(other_shared_cards)} cards — "
                     f"treated as a generic OS/browser/screen fingerprint, not a ring signal")
        else:
            note = f"Checked for other cards sharing this device ({len(other_shared_cards)} found)"

        state["evidence"].append({
            "claim": note,
            "source": "graph",
            "ref": "query:find_shared_device_cards",
            "entity_ids": [device_id],
            "raw": shared_data
        })

        if is_suspicious_cluster:
            state["shared_device_cards"] = other_shared_cards
            state["connected_device_profiles"] = [device_id]
            state["connected_card_ids"] = other_shared_cards
            state["is_single_signal"] = False
        else:
            # Either no sharing, or too widespread to be meaningful — don't
            # let decide_node's R6 fire on it, and don't count it as corroboration.
            state["shared_device_cards"] = []
            state["connected_device_profiles"] = []
    else:
        state["evidence"].append({
            "claim": "No device profile linked to this transaction (in-person or unlinked online txn)",
            "source": "graph",
            "ref": "query:get_transaction_device",
            "entity_ids": [state["flagged_txn_id"]],
            "raw": device_data
        })

    return state
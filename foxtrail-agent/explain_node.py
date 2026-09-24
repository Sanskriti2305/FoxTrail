import json
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

def extract_text(response) -> str:
    content = response.content
    if isinstance(content, list):
        text = "".join(
            block if isinstance(block, str) else block.get("text", "")
            for block in content
        ).strip()
    else:
        text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return text


def get_flagged_txn_details(state: dict) -> dict:
    for e in state["evidence"]:
        if e["ref"] == "query:get_transaction_details":
            try:
                return e["raw"]["data"]["result"][0]["Txn"][0]["attributes"]
            except (KeyError, IndexError):
                pass
    return {}


SUMMARY_PROMPT = """Write a case summary for a fraud analyst, 2 to 6 sentences, in plain language.

Case: {case_id}
Verdict: {verdict}
Pattern: {pattern}
Fraud probability: {fraud_probability}
Exposure: ${exposure_usd}
Evidence found: {evidence_summary}
Evidence requested: {evidence_requests}
Final actions: {final_actions}
What changed between initial and final recommendation: {what_changed}

Write ONLY the summary text, no preamble, no markdown, no labels. An analyst should be able to read
just this and understand what happened and why.
"""

SAR_PROMPT = """Write a Suspicious Activity Report (SAR) narrative. This goes to a bank regulator and
must stand on its own — the regulator has no other context.

Cover, in 6 to 12 sentences: WHO (customer, cards, devices involved), WHAT happened, WHEN (dates),
WHERE (channel, region), HOW it was carried out, and WHY it is suspicious.

Case: {case_id}
Customer: {customer_id}
Card: {card_id}
Pattern: {pattern}
Fraud probability: {fraud_probability}
Flagged transaction: {flagged_txn_id}, amount ${amount}, on {ts}, channel {channel}
Exposure: ${exposure_usd}
Evidence: {evidence_summary}
Customer response (simulated): {assumed_response}
Actions taken: {final_actions}

Write ONLY the narrative text, no preamble, no markdown, no labels. Plain prose, factual, no rule
numbers or internal jargon like "R2" — a regulator reading this has never seen our policy document.
"""


def build_evidence_summary(evidence: list) -> str:
    lines = []
    for e in evidence:
        lines.append(f"- {e['claim']}")
    return "\n".join(lines)


async def explain_node(state: dict) -> dict:
    evidence_summary = build_evidence_summary(state["evidence"])

    # --- case.summary (always required) ---
    summary_prompt = SUMMARY_PROMPT.format(
        case_id=state["case_id"],
        verdict=state["verdict"],
        pattern=state["pattern"],
        fraud_probability=state["fraud_probability"],
        exposure_usd=state["exposure_usd"],
        evidence_summary=evidence_summary,
        evidence_requests=json.dumps(state["evidence_requests"]),
        final_actions=json.dumps(state["final_action"]),
        what_changed=state["what_changed"],
    )
    response = await llm.ainvoke(summary_prompt)
    state["summary"] = extract_text(response)

    # --- sar.narrative (only when sar_file is True) ---
    if state["sar_file"]:
        txn = get_flagged_txn_details(state)
        assumed_response = (
            state["evidence_requests"][0]["assumed_response"]
            if state["evidence_requests"] else "Not requested"
        )

        sar_prompt = SAR_PROMPT.format(
            case_id=state["case_id"],
            customer_id=state["customer_id"],
            card_id=state["resolved_card_id"],
            pattern=state["pattern"],
            fraud_probability=state["fraud_probability"],
            flagged_txn_id=state["flagged_txn_id"],
            amount=txn.get("amount", "unknown"),
            ts=txn.get("ts", "unknown"),
            channel=txn.get("channel", "unknown"),
            exposure_usd=state["exposure_usd"],
            evidence_summary=evidence_summary,
            assumed_response=assumed_response,
            final_actions=json.dumps(state["final_action"]),
        )
        response = await llm.ainvoke(sar_prompt)
        state["sar_narrative"] = extract_text(response)

        state["sar_subjects"] = [state["customer_id"], state["resolved_card_id"]] + state["connected_card_ids"]
        state["sar_total_amount_usd"] = state["exposure_usd"]
        txn_date = txn.get("ts", "")[:10] if txn.get("ts") else ""
        state["sar_activity_dates"] = [txn_date, txn_date] if txn_date else []
    else:
        state["sar_narrative"] = ""
        state["sar_subjects"] = []
        state["sar_total_amount_usd"] = 0.0
        state["sar_activity_dates"] = []

    return state
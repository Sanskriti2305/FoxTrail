import json
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

PATTERN_VALUES = [
    "card_testing", "card_not_present_fraud", "card_not_present_new_device",
    "out_of_region_use", "account_takeover", "undocumented", "none"
]

ASSESS_PROMPT = """You are a fraud analyst assistant. Given the evidence below, assess this case.

Case trigger: {trigger_type}
Trigger text: {trigger_text}
Initial risk score (NOT a verdict, just a signal): {initial_risk_score}

Evidence gathered:
{evidence_summary}

Known fraud patterns you may choose from: {pattern_values}
- card_testing: 3+ tiny online authorizations then a larger purchase, same card, short window
- card_not_present_fraud: unusual amounts/products online, doesn't fit cardholder history
- card_not_present_new_device: same as above, from a device marked New for this account
- out_of_region_use: card-present purchases in a new billing region while home activity continues
- account_takeover: mixed-channel activity, device/match-flag anomalies
- undocumented: fits none of the above but shows real coordinated/repeated abuse
- none: no fraud pattern found

Respond with ONLY valid JSON, no markdown fences, no preamble:
{{
  "fraud_probability": <float 0-1>,
  "pattern": "<one of the pattern values above>",
  "pattern_description": "<always give one concise sentence explaining why this pattern (or 'none') fits the evidence, regardless of which pattern you chose>",
  "confidence_notes": "<1-3 sentences: what evidence drove this number, citing sources>"
}}
"""


def build_evidence_summary(evidence: list) -> str:
    lines = []
    for e in evidence:
        lines.append(f"- {e['claim']} (source: {e['source']}, ref: {e['ref']})")
        lines.append(f"  detail: {json.dumps(e['raw'])[:800]}")
    return "\n".join(lines)


async def assess_node(state: dict) -> dict:
    prompt = ASSESS_PROMPT.format(
        trigger_type=state["trigger_type"],
        trigger_text=state["trigger_text"],
        initial_risk_score=state.get("initial_risk_score"),
        evidence_summary=build_evidence_summary(state["evidence"]),
        pattern_values=PATTERN_VALUES,
    )

    response = await llm.ainvoke(prompt)

    if isinstance(response.content, list):
        # Gemini 3.6 can return content as a list of blocks; join any text parts
        raw_text = "".join(
            block if isinstance(block, str) else block.get("text", "")
            for block in response.content
        ).strip()
    else:
        raw_text = response.content.strip()

    # Strip markdown fences if the model added them anyway
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    result = json.loads(raw_text)

    state["fraud_probability"] = result["fraud_probability"]
    state["pattern"] = result["pattern"]
    state["pattern_description"] = result.get("pattern_description", "")
    state["confidence_notes"] = result.get("confidence_notes", "")

    return state
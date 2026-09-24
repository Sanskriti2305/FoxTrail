"""
Reusable test runner. Loads a case straight from case_pack.csv by case_id,
runs it through the full pipeline, and prints every stage's output.

Usage:
    python run_case.py HHG-005
    python run_case.py HHG-001 HHG-005 HHG-014   (runs several in sequence)
"""
from dotenv import load_dotenv
load_dotenv()

import sys
import csv
import json
import asyncio

from graph import build_graph

_graph = build_graph()


def load_case(case_id: str) -> dict:
    with open("case_pack.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["case_id"] == case_id:
                risk_score = row["risk_score"].strip()
                return {
                    "case_id": row["case_id"],
                    "customer_id": row["customer_id"],
                    "flagged_txn_id": row["flagged_txn_id"],
                    "card_id_hint": row["card_id"],
                    "trigger_type": row["trigger_type"],
                    "trigger_text": row["trigger_text"],
                    "initial_risk_score": float(risk_score) if risk_score else None,
                    "opened_at": row["opened_at"],
                }
    raise ValueError(f"Case {case_id} not found in case_pack.csv")


async def run_one_case(case_id: str):
    print(f"\n{'=' * 60}")
    print(f"CASE: {case_id}")
    print(f"{'=' * 60}")

    state = load_case(case_id)
    state = await _graph.ainvoke(state)

    print("\n--- KEY STATE FIELDS ---")
    for key in ["resolved_card_id", "is_single_signal", "similar_prior_cases",
                "shared_device_cards", "connected_card_ids", "tool_calls"]:
        print(f"{key}: {state[key]}")

    print("\n--- ASSESSMENT ---")
    print(f"fraud_probability: {state['fraud_probability']}")
    print(f"pattern: {state['pattern']}")
    print(f"pattern_description: {state['pattern_description']}")
    print(f"confidence_notes: {state['confidence_notes']}")

    print("\n--- DECISION ---")
    print(f"verdict: {state['verdict']}")
    print(f"status: {state['status']}")
    print(f"exposure_usd: {state['exposure_usd']}")
    print(f"initial_action: {state['initial_action']}")
    print(f"final_action: {state['final_action']}")
    print(f"evidence_requests: {state['evidence_requests']}")
    print(f"what_changed: {state['what_changed']}")
    print(f"sar_file: {state['sar_file']}")
    print(f"sar_reason: {state['sar_reason']}")
    print(f"stop_reason: {state['stop_reason']}")

    print("\n--- MEMORY ---")
    print(f"written_to_graph: {state['written_to_graph']}")
    print(f"graph_case_id: {state['graph_case_id']}")

    print("\n--- EXPLANATION ---")
    print(f"summary: {state['summary']}")
    if state['sar_file']:
        print(f"\nsar_narrative: {state['sar_narrative']}")
        print(f"sar_subjects: {state['sar_subjects']}")
        print(f"sar_total_amount_usd: {state['sar_total_amount_usd']}")
        print(f"sar_activity_dates: {state['sar_activity_dates']}")

    return state


async def main():
    case_ids = sys.argv[1:]
    if not case_ids:
        print("Usage: python run_case.py <CASE_ID> [<CASE_ID> ...]")
        return

    for case_id in case_ids:
        await run_one_case(case_id)


if __name__ == "__main__":
    asyncio.run(main())
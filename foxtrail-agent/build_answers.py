"""
Phase 7: runs every case in case_pack.csv through the full pipeline and writes
one answer JSON file per case into cases/, in the format the hackathon requires.

Usage:
    python build_cases.py            # all cases in case_pack.csv
"""
from dotenv import load_dotenv
load_dotenv()

import sys
import csv
import json
import asyncio
import traceback
from pathlib import Path

from graph import build_graph

_graph = build_graph()
OUTPUT_DIR = Path("cases")
DELAY_BETWEEN_CASES = 5  # seconds, gentle on rate limits


def load_all_cases() -> list[dict]:
    cases = []
    with open("case_pack.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            risk_score = row["risk_score"].strip()
            cases.append({
                "case_id": row["case_id"],
                "customer_id": row["customer_id"],
                "flagged_txn_id": row["flagged_txn_id"],
                "card_id_hint": row["card_id"],
                "trigger_type": row["trigger_type"],
                "trigger_text": row["trigger_text"],
                "initial_risk_score": float(risk_score) if risk_score else None,
                "opened_at": row["opened_at"],
            })
    return cases


def build_answer_json(state: dict) -> dict:
    """Shapes final state into the hackathon's required answer format."""
    return {
        "case": {
            "case_id": state["case_id"],
            "customer_id": state["customer_id"],
            "card_id": state["resolved_card_id"],
            "status": state["status"],
            "verdict": state["verdict"],
            "fraud_probability": state["fraud_probability"],
            "pattern": state["pattern"],
            "pattern_description": state["pattern_description"],
            "exposure_usd": state["exposure_usd"],
            "summary": state["summary"],
            "evidence": [
                {
                    "claim": e["claim"],
                    "source": e["source"],
                    "ref": e["ref"],
                    "entity_ids": e["entity_ids"],
                }
                for e in state["evidence"]
            ],
            "similar_prior_cases": state["similar_prior_cases"],
            "connected_card_ids": state["connected_card_ids"],
            "stop_reason": state["stop_reason"],
            "written_to_graph": state["written_to_graph"],
            "graph_case_id": state["graph_case_id"],
        },
        "sar": {
            "file_required": state["sar_file"],
            "reason": state["sar_reason"],
            "narrative": state["sar_narrative"],
            "subjects": state["sar_subjects"],
            "total_amount_usd": state["sar_total_amount_usd"],
            "activity_dates": state["sar_activity_dates"],
        } if state["sar_file"] else {
            "file_required": False,
            "reason": state["sar_reason"],
        },
        "next_best_actions": {
            "initial": state["initial_action"],
            "final": state["final_action"],
            "what_changed": state["what_changed"],
        },
        "evidence_requests": state["evidence_requests"],
        "metrics": {
            "tool_calls": state["tool_calls"],
        },
    }


async def run_and_save(case: dict) -> tuple[str, bool, str]:
    case_id = case["case_id"]
    try:
        final_state = await _graph.ainvoke(case)
        answer = build_answer_json(final_state)

        OUTPUT_DIR.mkdir(exist_ok=True)
        out_path = OUTPUT_DIR / f"{case_id}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(answer, f, indent=2)

        return case_id, True, f"OK -> {out_path}"
    except Exception as e:
        error_detail = f"{type(e).__name__}: {e}"
        return case_id, False, error_detail


async def main():
    only_ids = sys.argv[1:]
    all_cases = load_all_cases()
    cases_to_run = (
        [c for c in all_cases if c["case_id"] in only_ids]
        if only_ids else all_cases
    )

    print(f"Running {len(cases_to_run)} case(s)...\n")

    results = []
    for i, case in enumerate(cases_to_run):
        print(f"[{i + 1}/{len(cases_to_run)}] {case['case_id']}...", end=" ", flush=True)
        case_id, success, message = await run_and_save(case)
        print(message)
        results.append((case_id, success, message))

        if i < len(cases_to_run) - 1:
            await asyncio.sleep(DELAY_BETWEEN_CASES)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    succeeded = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]
    print(f"Succeeded: {len(succeeded)}/{len(results)}")
    if failed:
        print("\nFailed cases:")
        for case_id, _, message in failed:
            print(f"  {case_id}: {message}")


if __name__ == "__main__":
    asyncio.run(main())
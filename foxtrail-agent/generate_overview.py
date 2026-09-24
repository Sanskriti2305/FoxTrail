"""
Reads all answers/*.json + case_pack.csv and produces the exact
demo-overview.json shape the frontend expects.

Usage:
    python generate_overview.py
Output:
    overview.json  (copy this into frontend/public/demo-overview.json)
"""
import json
import csv
from pathlib import Path

ANSWERS_DIR = Path("answers")
CASE_PACK = Path("case_pack.csv")
OUTPUT = Path("overview.json")


def load_case_pack_lookup():
    lookup = {}
    with open(CASE_PACK, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lookup[row["case_id"]] = {
                "trigger_type": row["trigger_type"],
                "opened_at": row["opened_at"],
                "flagged_txn_id": row["flagged_txn_id"],
            }
    return lookup


def build_case_row(answer: dict, pack_info: dict) -> dict:
    case = answer["case"]
    sar = answer["sar"]
    actions = answer["next_best_actions"]

    return {
        "case_id": case["case_id"],
        "customer_id": case["customer_id"],
        "verdict": case["verdict"],
        "status": case["status"],
        "pattern": case["pattern"],
        "exposure_usd": case["exposure_usd"],
        "fraud_probability": case["fraud_probability"],
        "sar": sar["file_required"],
        "written_to_graph": case["written_to_graph"],
        "trigger_type": pack_info["trigger_type"],
        "summary": case["summary"],
        "final_actions": actions["final"],
        "initial_actions": actions["initial"],
        "opened_at": pack_info["opened_at"],
        "flagged_txn_id": pack_info["flagged_txn_id"],
    }


def main():
    pack_lookup = load_case_pack_lookup()
    case_rows = []

    answer_files = sorted(ANSWERS_DIR.glob("HHG-*.json"))
    if not answer_files:
        print(f"No answer files found in {ANSWERS_DIR}/")
        return

    for path in answer_files:
        with open(path, encoding="utf-8") as f:
            answer = json.load(f)

        case_id = answer["case"]["case_id"]
        pack_info = pack_lookup.get(case_id)
        if not pack_info:
            print(f"WARNING: {case_id} not found in case_pack.csv, skipping")
            continue

        case_rows.append(build_case_row(answer, pack_info))

    total = len(case_rows)
    fraud_cases = [c for c in case_rows if c["verdict"] == "fraud"]
    legitimate_cases = [c for c in case_rows if c["verdict"] == "legitimate"]
    uncertain_cases = [c for c in case_rows if c["verdict"] not in ("fraud", "legitimate")]
    sar_cases = [c for c in case_rows if c["sar"]]
    graph_written = [c for c in case_rows if c["written_to_graph"]]

    overview = {
        "metrics": {
            "total_cases": total,
            "fraud_cases": len(fraud_cases),
            "legitimate_cases": len(legitimate_cases),
            "uncertain_cases": len(uncertain_cases),
            "fraud_exposure_usd": round(sum(c["exposure_usd"] for c in fraud_cases), 2),
            "reported_exposure_usd": round(sum(c["exposure_usd"] for c in case_rows), 2),
            "sar_cases": len(sar_cases),
            "graph_written": len(graph_written),
        },
        "cases": case_rows,
    }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(overview, f, indent=2)

    print(f"Wrote {OUTPUT} — {total} cases ({len(fraud_cases)} fraud, {len(legitimate_cases)} legitimate)")


if __name__ == "__main__":
    main()
"""Thin web/API layer for the Foxtrail investigation console.

Keeps the existing LangGraph/TigerGraph investigation pipeline untouched.
Page 1 reads the completed case records from cases/ until the live runner
is connected in the next UI phase.
"""
from pathlib import Path
import json
import csv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent
ANSWERS = ROOT / "cases"
CASE_PACK = ROOT / "case_pack.csv"

app = FastAPI(title="Foxtrail Fraud Investigation API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def read_cases():
    pack = {}
    if CASE_PACK.exists():
        with CASE_PACK.open(newline="", encoding="utf-8") as f:
            pack = {r["case_id"]: r for r in csv.DictReader(f)}

    cases = []
    for path in sorted(ANSWERS.glob("HHG-*.json")):
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        case = data.get("case", {})
        sar = data.get("sar", {})
        actions = data.get("next_best_actions", {})
        cid = case.get("case_id", path.stem)
        source = pack.get(cid, {})
        cases.append({
            "case_id": cid,
            "customer_id": case.get("customer_id", source.get("customer_id", "")),
            "verdict": case.get("verdict", ""),
            "status": case.get("status", ""),
            "pattern": case.get("pattern", ""),
            "pattern_description": case.get("pattern_description", ""),
            "exposure_usd": case.get("exposure_usd", 0),
            "fraud_probability": case.get("fraud_probability", 0),
            "sar": bool(sar.get("file_required", sar.get("file", False))),
            "written_to_graph": bool(case.get("written_to_graph", False)),
            "trigger_type": source.get("trigger_type", ""),
            "trigger_text": source.get("trigger_text", ""),
            "opened_at": source.get("opened_at", ""),
            "flagged_txn_id": source.get("flagged_txn_id", ""),
            "summary": case.get("summary", ""),
            "evidence": case.get("evidence", []),
            "similar_prior_cases": case.get("similar_prior_cases", []),
            "connected_card_ids": case.get("connected_card_ids", []),
            "connected_device_profiles": case.get("connected_device_profiles", []),
            "initial_actions": actions.get("initial", []),
            "final_actions": actions.get("final", []),
            "what_changed": actions.get("what_changed", ""),
            "evidence_requests": data.get("evidence_requests", []),
            "sar_data": sar,
            "stop_reason": data.get("stop_reason", case.get("stop_reason", "")),
            "graph_case_id": case.get("graph_case_id", ""),
            "tool_calls": data.get("tool_calls", data.get("metrics", {}).get("tool_calls", 0)),
            "tokens": data.get("tokens", data.get("metrics", {}).get("tokens", 0)),
        })
    return cases


@app.get("/api/overview")
def overview():
    cases = read_cases()
    fraud = [c for c in cases if c["verdict"] == "fraud"]
    legit = [c for c in cases if c["verdict"] == "legitimate"]
    uncertain = [c for c in cases if c["verdict"] == "uncertain"]
    return {
        "metrics": {
            "total_cases": len(cases),
            "fraud_cases": len(fraud),
            "legitimate_cases": len(legit),
            "uncertain_cases": len(uncertain),
            "fraud_exposure_usd": round(sum(c["exposure_usd"] for c in fraud), 2),
            "reported_exposure_usd": round(sum(c["exposure_usd"] for c in cases), 2),
            "sar_cases": sum(c["sar"] for c in cases),
            "graph_written": sum(c["written_to_graph"] for c in cases),
        },
        "cases": cases,
    }


@app.get("/api/cases")
def cases():
    return read_cases()


@app.get("/api/cases/{case_id}")
def case(case_id: str):
    found = next((c for c in read_cases() if c["case_id"] == case_id), None)
    if not found:
        raise HTTPException(status_code=404, detail="Case not found")
    return found

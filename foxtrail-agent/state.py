from typing import TypedDict, List, Dict, Any, Optional


class EvidenceItem(TypedDict):
    claim: str
    source: str          # "graph" | "document" | "customer" | "external"
    ref: str
    entity_ids: List[str]
    raw: Any              # full/summarized tool output, not shown in final answer


class ActionItem(TypedDict):
    action: str            # from the policy's action list
    route: str              # "auto" | "L1" | "L2"
    reason: str              # cites a rule, e.g. "R1"


class EvidenceRequest(TypedDict):
    type: str                # "customer_validation" | "step_up_auth" | "analyst_info"
    asked_after_step: int
    assumed_response: str


class CaseState(TypedDict):
    # --- Input, from case_pack.csv ---
    case_id: str
    customer_id: str
    flagged_txn_id: str
    card_id_hint: str          # raw "-K1"/"-K2" format
    trigger_type: str           # "risk_score" | "customer_report" | "analyst_request"
    trigger_text: str
    initial_risk_score: Optional[float]

    # --- Resolved during investigate_node ---
    resolved_card_id: Optional[str]

    # --- Evidence, built up across nodes ---
    evidence: List[EvidenceItem]
    similar_prior_cases: List[str]         # closed case IDs used as memory
    shared_device_cards: List[str]          # other card_ids sharing a device, if any
    is_single_signal: bool                    # true if only the risk score/one txn supports this

    # --- Assessment (assess_node, LLM) ---
    fraud_probability: float
    pattern: str                # one of the enum values, or "" until decided
    pattern_description: str
    confidence_notes: str

    # --- Facts needed for policy rules (computed, not LLM-guessed) ---
    affected_txn_ids: List[str]
    first_suspicious_txn_id: str
    connected_card_ids: List[str]
    connected_device_profiles: List[str]
    exposure_usd: float

    # --- Decisions (decide_node, deterministic) ---
    verdict: str                # "fraud" | "legitimate" | "uncertain"
    status: str                  # "open" | "closed_fraud" | "closed_legitimate" | "escalated"
    initial_action: List[ActionItem]
    final_action: List[ActionItem]
    what_changed: str
    evidence_requests: List[EvidenceRequest]

    # --- SAR (Part 2) ---
    sar_file: bool
    sar_reason: str
    sar_narrative: str
    sar_subjects: List[str]
    sar_total_amount_usd: float
    sar_activity_dates: List[str]

    # --- Output (explain_node) ---
    summary: str
    stop_reason: str

    # --- Memory / graph write-back ---
    written_to_graph: bool
    graph_case_id: str

    # --- Metrics, for the required output fields ---
    tool_calls: int
    tokens: int
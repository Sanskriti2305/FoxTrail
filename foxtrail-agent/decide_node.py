"""
Deterministic policy engine — implements the Fraud Policy (README) rules R1-R10 exactly.
No LLM involved here. assess_node decides WHAT happened; this decides WHAT TO DO.
"""

def compute_exposure(state: dict) -> float:
    flagged_amount = None
    for e in state["evidence"]:
        if e["source"] == "graph" and "get_transaction_details" in e["ref"]:
            try:
                flagged_amount = e["raw"]["data"]["result"][0]["Txn"][0]["attributes"]["amount"]
            except (KeyError, IndexError):
                pass
    return round(flagged_amount, 2) if flagged_amount is not None else 0.0


def decide_node(state: dict) -> dict:
    prob = state["fraud_probability"]
    pattern = state["pattern"]
    single_signal = state["is_single_signal"]
    exposure = compute_exposure(state)
    state["exposure_usd"] = exposure

    initial_actions = []
    evidence_requests = []

    # --- R5: Card testing ---
    if pattern == "card_testing":
        initial_actions.append({
            "action": "DECLINE_TRANSACTION", "route": "L1",
            "reason": "R5: card testing pattern (3+ small authorizations then a larger purchase)"
        })
        initial_actions.append({
            "action": "STEP_UP_AUTH", "route": "auto",
            "reason": "R5: require step-up before further activity"
        })
        if exposure > 100:
            route = "L1" if exposure <= 2500 else "L2"
            initial_actions.append({
                "action": "BLOCK_CARD", "route": route,
                "reason": "R5: a purchase over $100 has already cleared"
            })

    # --- R6: Shared origin ---
    if state["shared_device_cards"]:
        initial_actions.append({
            "action": "CREATE_CASE", "route": "auto",
            "reason": "R6: shared device profile links this card to others"
        })
        initial_actions.append({
            "action": "FILE_REPORT", "route": "L2",
            "reason": "R6: shared device profile across multiple cards"
        })
        initial_actions.append({
            "action": "MONITOR_CONNECTED_CARDS", "route": "auto",
            "reason": "R6: monitor every card sharing this device profile"
        })

    # --- Is the customer's denial already in hand? ---
    # A customer_report trigger IS a first-hand, unsolicited denial — real evidence,
    # not a probability estimate. It must never be silently overridden by a low
    # model-assessed fraud_probability. Route it straight to R2, same as any other
    # confirmed denial, regardless of what the LLM's probability score says.
    is_customer_report = state.get("trigger_type") == "customer_report"

    if is_customer_report:
        evidence_requests.append({
            "type": "customer_validation",
            "asked_after_step": 0,
            "assumed_response": state.get("trigger_text", "Customer reported the transaction as unauthorized."),
            "response_source": "customer_initiated_report",  # real, not simulated — arrived as the trigger itself
        })
    elif single_signal and 0.15 < prob and not initial_actions:
        # R1 (and its extension to high-confidence, uncorroborated cases)
        if prob < 0.70:
            reason = f"R1: single signal, fraud probability {prob} is below 0.70"
        else:
            reason = (f"R1 (extended): fraud probability {prob} is high, but rests on a "
                      f"single signal with no external corroboration; verify before blocking "
                      f"per the policy's stated intent not to block a legitimate customer")
        initial_actions.append({
            "action": "VERIFY_WITH_CUSTOMER", "route": "auto", "reason": reason
        })
        evidence_requests.append({
            "type": "customer_validation",
            "asked_after_step": len(state["evidence"]),
            "assumed_response": None,
            "response_source": "simulated",
        })

    # --- Baseline: nothing suspicious found, AND no real customer denial on record ---
    if not initial_actions and not is_customer_report and pattern == "none" and prob <= 0.15:
        initial_actions.append({
            "action": "CLOSE_NO_FRAUD", "route": "auto",
            "reason": f"No pattern found; fraud probability {prob} at or below 0.15 (Section 6 stopping threshold)"
        })

    # --- R9: Undocumented pattern ---
    if pattern == "undocumented":
        initial_actions.append({
            "action": "CREATE_CASE", "route": "auto", "reason": "R9: undocumented pattern"
        })
        initial_actions.append({
            "action": "FILE_REPORT", "route": "L2", "reason": "R9: coordinated/repeated abuse, undocumented pattern"
        })
        initial_actions.append({
            "action": "ESCALATE_TO_ANALYST", "route": "auto", "reason": "R9: undocumented pattern needs human review"
        })

    # --- Section 3a: open a case once probability reaches 0.30, if not already opened ---
    already_has_case = any(a["action"] == "CREATE_CASE" for a in initial_actions)
    if prob >= 0.30 and not already_has_case:
        initial_actions.append({
            "action": "CREATE_CASE", "route": "auto",
            "reason": "Section 3a: fraud probability has reached 0.30"
        })

    # --- Preliminary verdict ---
    if is_customer_report:
        verdict = "uncertain"  # pending resolution below, which will always resolve to "fraud"
    elif prob >= 0.85:
        verdict = "fraud"
    elif prob <= 0.15:
        verdict = "legitimate"
    else:
        verdict = "uncertain"

    # --- R8: escalate when uncertain and exposure is meaningful ---
    if verdict == "uncertain" and exposure > 500:
        if not any(a["action"] == "ESCALATE_TO_ANALYST" for a in initial_actions):
            initial_actions.append({
                "action": "ESCALATE_TO_ANALYST", "route": "auto",
                "reason": "R8: verdict uncertain and exposure exceeds $500"
            })

    state["verdict"] = verdict
    state["initial_action"] = initial_actions

    # --- Resolve evidence request: REAL (customer_report) or SIMULATED (R1 zone) ---
    final_actions = list(initial_actions)
    what_changed = "nothing"

    if evidence_requests:
        req = evidence_requests[0]

        if is_customer_report:
            assumed_deny = True  # a real, direct denial — never gated by probability
        else:
            assumed_deny = prob >= 0.5
            req["assumed_response"] = (
                "Customer states they did not make this purchase and still has the card"
                if assumed_deny else
                "Customer confirms they made this purchase"
            )

        final_actions = [a for a in initial_actions if a["action"] != "VERIFY_WITH_CUSTOMER"]

        if assumed_deny:
            # --- R2: customer denies ---
            final_actions.append({
                "action": "BLOCK_CARD", "route": "L1" if exposure <= 2500 else "L2",
                "reason": "R2: customer denied the transaction"
            })
            if not any(a["action"] == "CREATE_CASE" for a in final_actions):
                final_actions.append({
                    "action": "CREATE_CASE", "route": "auto", "reason": "R2: customer denied the transaction"
                })
            if exposure > 1000 or state["shared_device_cards"]:
                final_actions.append({
                    "action": "FILE_REPORT", "route": "L2",
                    "reason": "R2: exposure exceeds $1,000 or links to a shared device"
                })
            verdict = "fraud"
            if is_customer_report:
                what_changed = (
                    f"Customer directly reported this transaction as unauthorized at intake "
                    f"(model-assessed probability was {prob}); the customer's own report takes "
                    f"precedence, and the case was confirmed as fraud."
                )
            else:
                what_changed = f"Customer denial raised the case from probability {prob} to a confirmed fraud verdict."
        else:
            # --- R3: customer confirms ---
            final_actions = [
                {"action": "CLOSE_NO_FRAUD", "route": "auto",
                 "reason": "R3: customer confirmed the transaction"}
            ]
            verdict = "legitimate"
            what_changed = "Customer confirmed the transaction; case closed as legitimate."

    state["verdict"] = verdict
    state["final_action"] = final_actions
    state["evidence_requests"] = evidence_requests
    state["what_changed"] = what_changed

    # --- Status ---
    if any(a["action"] == "ESCALATE_TO_ANALYST" for a in final_actions):
        state["status"] = "escalated"
    elif verdict == "fraud":
        state["status"] = "closed_fraud"
    elif verdict == "legitimate":
        state["status"] = "closed_legitimate"
    else:
        state["status"] = "open"

    # --- SAR ---
    file_report = any(a["action"] == "FILE_REPORT" for a in final_actions)
    state["sar_file"] = file_report
    if file_report:
        reasons = [a["reason"] for a in final_actions if a["action"] == "FILE_REPORT"]
        state["sar_reason"] = "; ".join(reasons)
    
    else:
        reasons_checked = [f"exposure ${exposure:.2f} does not exceed the $1,000 R2 threshold"]
        if state["shared_device_cards"]:
            reasons_checked.append("the shared-device cluster was assessed as generic noise, not a genuine link (R6)")
        else:
            reasons_checked.append("no shared-device link was found (R6)")
        if pattern != "undocumented":
            reasons_checked.append("pattern was not classified as undocumented (R9)")
        state["sar_reason"] = "No FILE_REPORT criteria met: " + "; ".join(reasons_checked) + "."
        
    # --- Stop reason ---
    if evidence_requests:
        if is_customer_report:
            state["stop_reason"] = "Customer's own unsolicited fraud report is decisive (Section 6)."
        else:
            state["stop_reason"] = "Verification response settled the question (Section 6)."
    elif prob >= 0.85 or prob <= 0.15:
        state["stop_reason"] = f"Fraud probability {prob} meets the Section 6 stopping threshold."
    else:
        state["stop_reason"] = "Uncertain verdict; escalated per R8 rather than continuing investigation."

    return state
# FoxTrail — Agentic Fraud Investigation

> *Every fraud leaves a trail. We follow it.*

FoxTrail is an AI agent that investigates fraud signals, gathers evidence from a knowledge graph, applies a deterministic fraud policy, and recommends the next best action — built for the **TigerGraph Agentic Fraud Investigation Hackathon (HHGOA)**.

Given a transaction flagged by a risk score, a customer report, or an analyst request, FoxTrail traces the cardholder's history, checks for shared devices and prior fraud cases, assesses the likely fraud pattern, decides on an action under a written policy, explains its reasoning, and writes the outcome back into the graph as memory for future investigations.

**[Live demo →](https://fox-trail-zeta.vercel.app/)**
---

## Architecture

```
                 ┌──────────────────────────────┐
                 │           TRIGGER             │
                 │  risk score · customer report │
                 │       · analyst request       │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                 ┌──────────────────────────────┐
                 │   LANGGRAPH PIPELINE (6 nodes) │
                 │                                │
                 │  1. investigate                │
                 │  2. gather_evidence   ──────┐   │
                 │  3. assess (LLM)            │   │
                 │  4. decide (policy engine)  │   │
                 │  5. explain (LLM)           │   │
                 │  6. memory (write-back)     │   │
                 └───────────────┬──────────────┘  │
                                 │                  │
                 ┌───────────────┴──────────────┐   │
                 ▼                               ▼   │
      ┌────────────────────┐         ┌──────────────────────┐
      │  TigerGraph Savanna │◄────────┤   Gemini (LLM)        │
      │  via TigerGraph MCP │         │  reasoning + writing  │
      │                     │         │  explanations only —  │
      │  7 GSQL queries +   │         │  never decides actions│
      │  1 GSQL write query │         └──────────────────────┘
      └──────────┬──────────┘
                 │
                 ▼
      ┌─────────────────────┐
      │  Deterministic policy│
      │  engine (R1–R10)     │
      │  — pure Python, no   │
      │    LLM involved      │
      └──────────┬──────────┘
                 │
                 ▼
      ┌─────────────────────┐
      │  FastAPI (api_server)│
      └──────────┬──────────┘
                 │
                 ▼
      ┌─────────────────────┐
      │  React + Vite UI     │
      │  (analyst console)   │
      └─────────────────────┘
```

**The core design decision:** the LLM never decides what action to take. It only estimates a fraud probability, classifies the likely pattern, and later writes a plain-language explanation. A separate, deterministic Python function (`decide_node.py`) applies the bank's actual written fraud policy (rules R1–R10) to that probability and turns it into an action — block, verify, escalate, close, file a report. This keeps every decision auditable and reproducible: the same evidence always produces the same action, and the reasoning can be traced back to a specific policy rule rather than an opaque model output.

---

## The investigation flow

Each case moves through six LangGraph nodes, mapped directly to the hackathon's required 8-step flow:

| Step | Node | What happens |
|---|---|---|
| Trigger | *(input)* | A case arrives from `case_pack.csv` — a risk score, a customer's fraud report, or an analyst request |
| Investigate | `investigate_node` | Resolves the case to a real transaction and card in the graph |
| Gather evidence | `gather_evidence_node` | Pulls the card's transaction timeline, checks for prior closed cases, checks for a shared device across other cards |
| Assess uncertainty | `assess_node` (LLM) | Estimates a fraud probability and names a likely pattern from the evidence |
| Gather more if needed / Decide | `decide_node` (deterministic) | Applies policy rules R1–R10 to decide the next action, requesting customer verification when the signal is weak or high-confidence-but-uncorroborated |
| Explain | `explain_node` (LLM) | Writes the case summary and, when required, a full Suspicious Activity Report narrative |
| Update memory | `memory_node` | Writes the resolved case back into the graph as a `ClosedCase`, so future investigations can find it |

---

## The policy engine, in brief

`decide_node.py` implements the bank's fraud policy exactly as written in the dataset's own README — not the hackathon overview doc, which only summarizes the challenge. Key rules:

- **R1** — never block on a single, uncorroborated signal without first attempting verification, even at high confidence
- **R2 / R3** — a customer's own denial or confirmation is decisive and overrides a lower model-estimated probability
- **R6** — a device shared across a *small* cluster of cards is treated as a fraud ring signal; a device shared across hundreds of cards is recognized as a generic OS/browser fingerprint and correctly ignored
- **R9** — undocumented but clearly coordinated abuse still gets escalated to a human analyst
- **R10** — the agent never recommends blocking every card system-wide

Every action in the output carries the specific rule that justified it, so a reviewer can trace *why* the agent did what it did.

---

## Tech stack

| Layer | Technology |
|---|---|
| Graph database | TigerGraph Savanna (cloud) |
| Graph access | `tigergraph-mcp` (official MCP server) |
| Agent orchestration | LangGraph |
| LLM | Gemini (via `langchain-google-genai`) — reasoning and explanation only |
| Policy engine | Deterministic Python, no LLM |
| API | FastAPI |
| Frontend | React + TypeScript + Vite |

---

## Repository structure

```
foxtrail-agent/
├── state.py                  # shared case state definition
├── tg_tools.py                # MCP query helper + JSON extraction
├── investigate_node.py        # node 1
├── gather_evidence_node.py    # node 2
├── assess_node.py              # node 3 (LLM)
├── decide_node.py              # node 4 (deterministic policy engine)
├── explain_node.py             # node 5 (LLM)
├── memory_node.py              # node 6 (graph write-back)
├── graph.py                    # LangGraph wiring
├── run_case.py                 # run + inspect a single case
├── build_answers.py            # batch-run all cases → answers/*.json
├── api_server.py               # FastAPI server for the UI
├── case_pack.csv               # the 20 benchmark cases
├── answers/                    # one JSON per case (required output)
└── frontend/                   # React analyst console
```

---

## Running it

**Backend**
```bash
python -m venv venv
venv\Scripts\activate          # or source venv/bin/activate on Mac/Linux
pip install -r requirements.txt
```

Create a `.env` file:
```
TG_HOST=https://<your-workspace>.i.tgcloud.io
TG_GRAPHNAME=FoxTrail
TG_SECRET=<your TigerGraph database secret>
TG_TGCLOUD=true
GOOGLE_API_KEY=<your Gemini API key>
```

Run all 20 cases and produce the answer files:
```bash
python build_answers.py
```

Start the API server:
```bash
uvicorn api_server:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

---

## What we learned / what we'd improve with more time

- **Device fingerprinting is a real weakness in this dataset.** `DeviceProfile` IDs are built by concatenating OS, browser, and screen size — fields that are shared by hundreds of unrelated users. We added a threshold (a device shared by more than 5 cards is treated as noise, not a ring) to avoid false positives, but a proper fix would need a genuinely unique device identifier.
- **A first-hand customer report should always outrank a model's probability estimate.** We initially let a low LLM-assessed probability silently override an explicit customer fraud report — a real correctness bug we found and fixed, and a good reminder that deterministic policy should always have the final say over model output, especially when better evidence (the customer's own words) is already in hand.
- **`NEXT` (transaction ordering) and `CONNECTED_TO` edges were never populated** — deferred due to time, and would strengthen card-testing and account-takeover pattern detection.
- **Exposure calculation currently only sums the single flagged transaction.** For multi-transaction patterns like card testing, this should sum every transaction in the suspicious window.
- With more time, we'd extend case memory to match on shared device or region across `ClosedCase`s, not just an exact card ID.

---

## Team

FOXTRAIL
AI FRAUD INVESTIGATION SYSTEM

© 2026 · TEAM KUROMI

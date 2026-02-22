# Banking Scam Triage with LangGraph and Agentic Workflow

This demo is a small but realistic **retail-banking scam triage** workflow implemented as a **stateful LangGraph**.
It uses **two specialist agents** driven by **OpenAI `gpt-4.1-nano`** (Responses API + Structured Outputs via Pydantic).

## What it does

Given a customer transcript (chat/call notes), the workflow:

1. **Support Agent** triages likely scam type/severity and decides what information is missing.
2. If needed, the graph **pauses** to collect missing customer answers (human-in-the-loop).
3. **Fraud Ops Agent** pulls internal evidence (transactions, payee profile, device sessions) using local “bank tools”.
4. Fraud Ops proposes a structured plan of actions; high-impact actions go through an **approval pause**.
5. Approved actions are executed (**simulated, since this is not our focus**), and a final customer message is drafted.

The point is to model a workflow that is:

- **Iterative** (question → answer → re-triage)
- **Tool-using** (evidence gathering)
- **Branching** (different paths based on what the model decides)
- **Resumable** (SQLite checkpoints, interrupt/resume)

Notice that

- At the end of a node, the next step is determined.
- The LLM asks the customer questions depend on (1) case context, (2) existing answers, (3) system prompt, (4) pydantic schema datatype and field description 


## Quickstart

### 1) Setup (Windows CMD)

```
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

Set the API key in `.env` file next to `pyproject.toml`.

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-nano
```

To keep the key out of GitHub, add `.env` to .gitignore:

### 2) Explore the dataset (30 synthetic cases)

```
scam-triage list-cases
scam-triage show-case C0001
```

### 3) Run a case

```
scam-triage run C0001
```

When the graph needs input (customer answers or approval), it prints an `__interrupt__` payload and prompts you.

### 4) Resume an interrupted run

Checkpoints are stored in `.\.scam_triage\checkpoints.sqlite` keyed by `thread_id`.

```
scam-triage resume <thread-id>
```

## Workflow overview

#### Agent

- **Support Agent** (`graph/nodes/support_agent.py`)
  - Infers scam type/severity
  - Produces immediate safety steps
  - Produces a short list of missing questions to be answered by the customer
  - Pass to the `collect_customer_info` node or the Fraud Ops agent

#### Human-in-the-loop

- `collect_customer_info` (a node that uses `interrupt()` and wait for customer answers)
  - Pauses to collect missing answers
  - Pass to the Support agent

#### Agent

- **Fraud Ops Agent** (`graph/nodes/fraud_ops.py`)
  - Reads support triage + customer answers
  - Queries evidence via tools
  - Produces a structured plan of proposed actions
  - Pass to the `approval` node or `execute_actions` node

#### Human-in-the-loop

- `approval` (a node that uses `interrupt()` and wait for the reviewer's approval)
  -  Pauses for approval when the plan contains high-impact actions.
  -  Pass to the `execute_actions` node

## Repo layout

- `src/graph/` LangGraph builder + nodes
- `src/llm/` OpenAI client wrapper (`responses.parse` + Pydantic)
- `src/tools/` CSV-backed “bank tools” (transactions/payees/device sessions)
- `src/cli.py` Typer CLI entrypoint
- `data/` synthetic cases + CSV tables

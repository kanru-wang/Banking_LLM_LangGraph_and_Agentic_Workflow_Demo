from __future__ import annotations

from langgraph.types import interrupt
from state import GraphState


def collect_customer_info_node(state: GraphState) -> dict[str, object]:
    """Pause and collect answers to the Support Agent's questions."""
    triage = state.get("support_triage")
    questions = []
    if triage is not None:
        questions = list(triage.missing_questions)

    payload = {
        "type": "customer_questions",
        "questions": questions,
        "instruction": (
            "Provide answers as a JSON object mapping each question to the customer's answer. "
            "If unknown, write an empty string."
        ),
    }
    answers = interrupt(payload)
    if not isinstance(answers, dict):
        raise ValueError("Resume payload must be a JSON object mapping question->answer.")

    merged = dict(state.get("customer_answers", {}))
    for k, v in answers.items():
        if isinstance(k, str) and isinstance(v, str):
            merged[k] = v
    return {"customer_answers": merged}

from __future__ import annotations

from llm.openai_client import OpenAIStructuredClient
from schemas import SupportTriage
from state import GraphState


def support_agent_node(state: GraphState, llm: OpenAIStructuredClient) -> dict[str, object]:
    """Customer Support Agent: classify + decide what to ask next."""
    conversation = state.get("conversation", "")
    existing_answers = state.get("customer_answers", {})

    system = (
        "You are a retail bank customer support agent handling potential scam reports. "
        "Your goals: (1) identify likely scam type, (2) assess severity, "
        "(3) provide immediate safety steps, (4) ask only the most important missing questions. "
        "Rules: Never ask for passwords, PINs, or one-time codes (OTPs). "
        "If the customer already provided an answer, do not ask again."
    )

    user_payload = {
        "conversation": conversation,
        "existing_answers": existing_answers,
        "linked_transaction_id": state.get("linked_transaction_id"),
        "reported_channel": state.get("reported_channel"),
        "created_date": state.get("created_date"),
    }

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Case context:\n{user_payload}"},
    ]

    triage = llm.parse(messages=messages, schema=SupportTriage)

    support_next = "fraud_ops" if len(triage.missing_questions) == 0 else "collect_customer_info"
    return {"support_triage": triage, "support_next": support_next}

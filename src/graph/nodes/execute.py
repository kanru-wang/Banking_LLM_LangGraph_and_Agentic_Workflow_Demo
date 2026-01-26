from __future__ import annotations

import json
from typing import Any

from llm.openai_client import OpenAIStructuredClient
from schemas import FinalOutcome
from state import GraphState


def execute_actions_node(state: GraphState, llm: OpenAIStructuredClient) -> dict[str, Any]:
    plan=state.get("fraud_ops_plan")
    approved=state.get("approved", False)

    executed=[]
    if plan is not None:
        for a in plan.proposed_actions:
            if a.requires_approval and not approved:
                continue
            executed.append(f"{a.action} {a.parameters}".strip())

    # Ask the model to draft a customer-facing message summarizing next steps.
    system=(
        "You are a retail banking support agent drafting a concise customer message. "
        "Do not include internal-only details like risk tags or IPs. "
        "Never ask for passwords/PINs/OTPs. Provide clear next steps and safety guidance."
    )

    user_payload={
        "support_triage": state.get("support_triage").model_dump() if state.get("support_triage") else None,
        "customer_answers": state.get("customer_answers", {}),
        "executed_actions": executed,
        "proposed_actions": plan.model_dump() if plan else None,
    }

    messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]
    final=llm.parse(messages=messages, schema=FinalOutcome)

    return {
        "executed_actions": executed,
        "final_outcome": final.outcome,
        "final_customer_message": final.customer_message,
    }

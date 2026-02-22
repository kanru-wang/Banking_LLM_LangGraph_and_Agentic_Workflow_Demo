from __future__ import annotations

from langgraph.types import interrupt
from schemas import ApprovalRequest
from state import GraphState


def approval_node(state: GraphState) -> dict[str, object]:
    plan = state.get("fraud_ops_plan")
    if plan is None:
        return {"approved": False}

    req = ApprovalRequest(
        summary=plan.risk_summary,
        actions=plan.proposed_actions,
    )

    decision = interrupt({
        "type": "approval",
        "request": req.model_dump(),
        "instruction": "Approve execution of the proposed actions? Reply with true or false.",
    })
    approved = bool(decision)
    return {"approved": approved}

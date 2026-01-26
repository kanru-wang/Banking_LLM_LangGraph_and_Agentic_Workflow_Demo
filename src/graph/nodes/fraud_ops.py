from __future__ import annotations

import json
from typing import Any

from llm.openai_client import OpenAIStructuredClient
from schemas import FraudOpsPlan
from state import GraphState
from tools.bank_tools import BankTools


def fraud_ops_node(
    state: GraphState,
    llm: OpenAIStructuredClient,
    tools: BankTools,
) -> dict[str, object]:
    """Fraud Ops Agent: gather evidence + propose an action plan."""
    customer_id=state["customer_id"]
    linked_txn_id=state.get("linked_transaction_id")

    customer=tools.get_customer(customer_id) or {}
    txns=tools.get_transactions(customer_id, limit=15)
    linked_txn=tools.get_transaction(linked_txn_id) if linked_txn_id else None
    payee=None
    if linked_txn and linked_txn.get("payee_id"):
        payee=tools.get_payee(str(linked_txn["payee_id"]))
    logins=tools.get_recent_logins(customer_id, limit=10)

    tool_evidence={
        "customer": customer,
        "recent_transactions": txns,
        "linked_transaction": linked_txn,
        "linked_payee": payee,
        "recent_logins": logins,
    }

    system=(
        "You are a retail bank Fraud Operations agent. "
        "You receive a suspected scam report, plus internal evidence (transactions, payee risk tags, logins). "
        "Your goals: (1) summarize risk, (2) list evidence, (3) propose actions. "
        "Rules: Propose actions from the allowed list. Mark high-impact actions as requires_approval=true. "
        "Never request passwords/PINs/OTPs."
    )

    user_payload={
        "support_triage": state.get("support_triage").model_dump() if state.get("support_triage") else None,
        "customer_answers": state.get("customer_answers", {}),
        "conversation": state.get("conversation", ""),
        "tool_evidence": tool_evidence,
    }

    messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]

    plan=llm.parse(messages=messages, schema=FraudOpsPlan)

    needs_approval=any(a.requires_approval for a in plan.proposed_actions)
    goto="approval" if needs_approval else "execute_actions"

    return {
        "tool_evidence": tool_evidence,
        "fraud_ops_plan": plan,
        "fraud_next": goto,
    }

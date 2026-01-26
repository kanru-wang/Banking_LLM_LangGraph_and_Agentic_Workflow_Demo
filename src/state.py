from __future__ import annotations

from typing import Any, Optional, TypedDict

from schemas import FraudOpsPlan, SupportTriage


class GraphState(TypedDict, total=False):
    # Input / case info
    case_id: str
    customer_id: str
    created_date: str
    reported_channel: str
    conversation: str
    linked_transaction_id: Optional[str]

    # Working memory
    support_triage: SupportTriage
    support_next: str
    customer_answers: dict[str, str]
    tool_evidence: dict[str, Any]
    fraud_ops_plan: FraudOpsPlan
    fraud_next: str
    approved: bool
    executed_actions: list[str]

    # Output
    final_outcome: str
    final_customer_message: str

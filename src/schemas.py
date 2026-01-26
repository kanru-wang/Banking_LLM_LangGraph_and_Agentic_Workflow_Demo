from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

ScamType = Literal[
    "sms_phishing_link",
    "bank_impersonation_call",
    "investment_crypto",
    "romance",
    "remote_access_software",
    "invoice_redirection_bec",
    "gift_card_payment",
    "parcel_delivery_phish",
    "tech_support_pop_up",
    "job_scam",
    "unknown",
]

Severity = Literal["low", "medium", "high", "critical"]


class SupportTriage(BaseModel):
    scam_type: ScamType = Field(description="Best guess scam type.")
    severity: Severity = Field(description="How urgent/serious this appears.")
    confidence: float = Field(ge=0.0, le=1.0)
    immediate_safety_steps: list[str] = Field(
        description="Concrete steps the customer should do now (no secrets requested)."
    )
    missing_questions: list[str] = Field(
        description="Questions to ask the customer to fill key missing info."
    )


class CustomerAnswers(BaseModel):
    answers: dict[str, str] = Field(description="Mapping question -> answer.")


ActionType = Literal[
    "freeze_card",
    "lock_digital_banking",
    "block_payee",
    "attempt_transfer_recall",
    "raise_dispute",
    "place_fraud_alert",
    "educate_customer",
]


class ProposedAction(BaseModel):
    action: ActionType
    rationale: str
    requires_approval: bool = Field(
        description="True if this action should be human-approved before execution."
    )
    parameters: dict[str, str] = Field(default_factory=dict)


class FraudOpsPlan(BaseModel):
    risk_summary: str
    evidence: list[str]
    proposed_actions: list[ProposedAction]
    next_questions_for_customer: list[str] = Field(default_factory=list)


class ApprovalRequest(BaseModel):
    summary: str
    actions: list[ProposedAction]


class FinalOutcome(BaseModel):
    outcome: str
    actions_executed: list[str]
    customer_message: str

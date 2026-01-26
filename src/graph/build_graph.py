from __future__ import annotations

from pathlib import Path
from typing import Any

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from data_loader import load_case_by_id
from llm.openai_client import OpenAIStructuredClient
from state import GraphState
from tools.bank_tools import BankTools

from .nodes.approval import approval_node
from .nodes.collect_customer_info import collect_customer_info_node
from .nodes.execute import execute_actions_node
from .nodes.fraud_ops import fraud_ops_node
from .nodes.support_agent import support_agent_node

import sqlite3


def _route_support(state: GraphState) -> str:
    return str(state.get("support_next", "fraud_ops"))


def _route_fraud(state: GraphState) -> str:
    return str(state.get("fraud_next", "execute_actions"))


def _load_case_node(state: GraphState, data_dir: Path) -> dict[str, Any]:
    case_id = state["case_id"]
    row = load_case_by_id(data_dir=data_dir, case_id=case_id)
    return {
        "case_id": row["case_id"],
        "customer_id": row["customer_id"],
        "created_date": row["created_date"],
        "reported_channel": row["reported_channel"],
        "conversation": row["conversation"],
        "linked_transaction_id": row.get("linked_transaction_id"),
    }


def build_graph(
        *,
        llm: OpenAIStructuredClient,
        tools: BankTools,
        data_dir: Path,
        checkpoint_db: Path,
):
    checkpoint_db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(checkpoint_db))
    checkpointer = SqliteSaver(conn)

    builder = StateGraph(GraphState)

    builder.add_node("load_case", lambda s: _load_case_node(s, data_dir=data_dir))
    builder.add_node("support_agent", lambda s: support_agent_node(s, llm=llm))
    builder.add_node("collect_customer_info", collect_customer_info_node)
    builder.add_node("fraud_ops", lambda s: fraud_ops_node(s, llm=llm, tools=tools))
    builder.add_node("approval", approval_node)
    builder.add_node("execute_actions", lambda s: execute_actions_node(s, llm=llm))

    builder.add_edge(START, "load_case")
    builder.add_edge("load_case", "support_agent")

    # Branch based on state (set by the support agent)
    builder.add_conditional_edges(
        "support_agent",
        _route_support,
        {
            "collect_customer_info": "collect_customer_info",
            "fraud_ops": "fraud_ops",
        },
    )
    builder.add_edge("collect_customer_info", "support_agent")

    # Branch based on state (set by Fraud Ops)
    builder.add_conditional_edges(
        "fraud_ops",
        _route_fraud,
        {
            "approval": "approval",
            "execute_actions": "execute_actions",
        },
    )
    builder.add_edge("approval", "execute_actions")

    builder.add_edge("execute_actions", END)

    return builder.compile(checkpointer=checkpointer)

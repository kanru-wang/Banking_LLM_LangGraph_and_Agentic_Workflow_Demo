from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import typer
from dotenv import load_dotenv
from langgraph.types import Command
from rich import print
from rich.console import Console
from rich.table import Table

from config import load_settings
from data_loader import list_cases, load_case_by_id
from graph.build_graph import build_graph
from llm.openai_client import OpenAIStructuredClient
from tools.bank_tools import BankTools

app = typer.Typer(add_completion=False)
console = Console()


def _build_runtime() -> tuple[Any, Path]:
    load_dotenv()
    settings = load_settings()
    data_dir = Path(settings.data_dir)
    llm = OpenAIStructuredClient(api_key=settings.openai_api_key, model=settings.openai_model)
    tools = BankTools(data_dir=data_dir)
    graph = build_graph(
        llm=llm,
        tools=tools,
        data_dir=data_dir,
        checkpoint_db=Path(settings.checkpoint_db),
    )
    return graph, data_dir


def _parse_resume_value(raw: str) -> Any:
    raw = raw.strip()
    if raw.lower() in {"y", "yes", "true"}:
        return True
    if raw.lower() in {"n", "no", "false"}:
        return False
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise typer.BadParameter(
            "Could not parse input. Provide JSON (e.g. {\"q\":\"a\"}) or true/false."
        ) from e


def _peek_interrupt(graph: Any, config: dict[str, Any]) -> Any | None:
    state = graph.get_state(config)
    interrupts = getattr(state, "interrupts", None)
    if interrupts:
        last = interrupts[-1]
        try:
            return last.value
        except AttributeError:
            return last.get("value")
    return None


def _run_until_done(graph: Any, config: dict[str, Any], initial_input: Any) -> dict[str, Any]:
    result = graph.invoke(initial_input, config=config)
    while isinstance(result, dict) and result.get("__interrupt__"):
        interrupt_items = result["__interrupt__"]
        interrupt_value = interrupt_items[0].value if interrupt_items else None
        print("\n[bold yellow]Graph paused for input:[/bold yellow]")
        print(interrupt_value)
        raw = typer.prompt("Resume payload (JSON or true/false)")
        resume_value = _parse_resume_value(raw)
        result = graph.invoke(Command(resume=resume_value), config=config)
    return result


@app.command("list-cases")
def list_cases_cmd() -> None:
    """List available demo cases (30)."""
    graph, data_dir = _build_runtime()
    rows = list_cases(data_dir)
    table = Table(title="Demo scam cases")
    table.add_column("case_id")
    table.add_column("customer_id")
    table.add_column("date")
    table.add_column("channel")
    table.add_column("gt_scam_type")
    table.add_column("gt_severity")
    for r in rows:
        gt = r.get("ground_truth", {})
        table.add_row(
            r.get("case_id", ""),
            r.get("customer_id", ""),
            r.get("created_date", ""),
            r.get("reported_channel", ""),
            str(gt.get("scam_type", "")),
            str(gt.get("severity", "")),
        )
    console.print(table)


@app.command("show-case")
def show_case(case_id: str) -> None:
    """Show a case JSON."""
    graph, data_dir = _build_runtime()
    row = load_case_by_id(data_dir=data_dir, case_id=case_id)
    print_json = json.dumps(row, indent=2, ensure_ascii=False)
    print(print_json)


@app.command()
def run(case_id: str) -> None:
    """Run the LangGraph workflow for a case."""
    graph, _ = _build_runtime()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    print(f"[bold cyan]thread_id:[/bold cyan] {thread_id}")
    result = _run_until_done(graph, config, {"case_id": case_id})
    print("\n[bold green]Done.[/bold green]")
    print(json.dumps(result, indent=2, ensure_ascii=False))


@app.command()
def resume(thread_id: str) -> None:
    """Resume a previously interrupted run by thread_id."""
    graph, _ = _build_runtime()
    config = {"configurable": {"thread_id": thread_id}}

    interrupt_value = _peek_interrupt(graph, config)
    if interrupt_value is not None:
        print("\n[bold yellow]Graph is waiting for input:[/bold yellow]")
        print(interrupt_value)
        raw = typer.prompt("Resume payload (JSON or true/false)")
        resume_value = _parse_resume_value(raw)
        result = _run_until_done(graph, config, Command(resume=resume_value))
    else:
        print("[bold yellow]No pending interrupt found for this thread_id.[/bold yellow]")
        result = graph.get_state(config).values  # Snapshot only.

    print("\n[bold green]Done.[/bold green]")
    print(json.dumps(result, indent=2, ensure_ascii=False))

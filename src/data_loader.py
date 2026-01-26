from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_case_by_id(data_dir: Path, case_id: str) -> dict[str, Any]:
    path = data_dir / "cases.jsonl"
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if row.get("case_id") == case_id:
                return row
    raise KeyError(f"Case not found: {case_id}")


def list_cases(data_dir: Path) -> list[dict[str, Any]]:
    path = data_dir / "cases.jsonl"
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows

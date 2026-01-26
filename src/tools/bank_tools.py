from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BankTools:
    data_dir: Path

    def _read_csv(self, name: str) -> list[dict[str, Any]]:
        path = self.data_dir / name
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return [dict(row) for row in reader]

    def get_customer(self, customer_id: str) -> dict[str, Any] | None:
        customers = self._read_csv("customers.csv")
        for row in customers:
            if row["customer_id"] == customer_id:
                return row
        return None

    def get_transactions(self, customer_id: str, limit: int = 25) -> list[dict[str, Any]]:
        txns = self._read_csv("transactions.csv")
        rows = [t for t in txns if t["customer_id"] == customer_id]
        rows.sort(key=lambda r: r["timestamp"], reverse=True)
        return rows[:limit]

    def get_transaction(self, transaction_id: str) -> dict[str, Any] | None:
        txns = self._read_csv("transactions.csv")
        for t in txns:
            if t["transaction_id"] == transaction_id:
                return t
        return None

    def get_payee(self, payee_id: str) -> dict[str, Any] | None:
        payees = self._read_csv("payees.csv")
        for p in payees:
            if p["payee_id"] == payee_id:
                return p
        return None

    def get_recent_logins(self, customer_id: str, limit: int = 10) -> list[dict[str, Any]]:
        sessions = self._read_csv("device_sessions.csv")
        rows = [s for s in sessions if s["customer_id"] == customer_id]
        rows.sort(key=lambda r: r["timestamp"], reverse=True)
        return rows[:limit]

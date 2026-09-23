"""Append-only in-memory ledger for the observe stub.

Receipts record what the lab stub observed or intended. They are not
Action-plane execution receipts. ``real_gate`` is always false.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from case_api.ids import new_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Receipt:
    receipt_id: str
    tenant_id: str
    action_request_id: str
    case_id: str
    kind: str
    idempotency_key: str
    at: str
    payload: dict[str, Any] = field(default_factory=dict)
    real_gate: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "tenant_id": self.tenant_id,
            "action_request_id": self.action_request_id,
            "case_id": self.case_id,
            "kind": self.kind,
            "idempotency_key": self.idempotency_key,
            "at": self.at,
            "real_gate": self.real_gate,
            "payload": self.payload,
        }


class Ledger:
    def __init__(self) -> None:
        self._items: list[Receipt] = []

    def append(
        self,
        *,
        tenant_id: str,
        action_request_id: str,
        kind: str,
        idempotency_key: str,
        case_id: str | None = None,
        **payload: Any,
    ) -> Receipt:
        receipt = Receipt(
            receipt_id=new_id(),
            tenant_id=tenant_id,
            action_request_id=action_request_id,
            case_id=case_id or action_request_id,
            kind=kind,
            idempotency_key=idempotency_key,
            at=_now(),
            payload=payload,
            real_gate=False,
        )
        self._items.append(receipt)
        return receipt

    def for_action(self, action_request_id: str) -> list[Receipt]:
        return [
            item
            for item in self._items
            if item.action_request_id == action_request_id or item.case_id == action_request_id
        ]

    def export(self, case_id: str) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self.for_action(case_id)]

"""Case state machine — Platform CaseStatus (Approach A overlay).

Ported from the workspace prototype ``case_sm.py`` and localized here.
Do not import ``sandbox.*``.

Invariant: no VERIFIED → ACTION_PENDING skip.
hold_expired → DENIED (never silent allow).
mode=observe forbids ACTION_* (release is intent on the hold demo path only).

real_gate is not a state. This module never executes an action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from case_api.ids import new_id

# Platform CaseStatus — authoritative. Not JSM status_map keys and not
# CTO shorthand (HOLD, CHALLENGE, RELEASED, EXECUTING, AUTHORIZED_PENDING_RELEASE).
STATES = frozenset(
    {
        "RECEIVED",
        "REJECTED",
        "VERIFIED",
        "ENRICHING",
        "ASSESSED",
        "OBSERVE",
        "CHALLENGE_PENDING",
        "HOLD_PENDING",
        "DENIED",
        "ACTION_PENDING",
        "ACTION_SUBMITTED",
        "ACTION_SUCCEEDED",
        "ACTION_FAILED",
        "ACTION_UNKNOWN",
        "RECONCILED",
        "BREAK_GLASS",
    }
)

ALLOWED: dict[str, frozenset[str]] = {
    "RECEIVED": frozenset({"VERIFIED", "REJECTED"}),
    "VERIFIED": frozenset({"ENRICHING"}),  # FORBIDDEN: ACTION_*
    "ENRICHING": frozenset({"ASSESSED"}),
    "ASSESSED": frozenset(
        {"OBSERVE", "CHALLENGE_PENDING", "HOLD_PENDING", "DENIED", "BREAK_GLASS"}
    ),
    "CHALLENGE_PENDING": frozenset(
        {"ENRICHING", "HOLD_PENDING", "DENIED", "OBSERVE"}
    ),
    "HOLD_PENDING": frozenset(
        {"ACTION_PENDING", "DENIED", "CHALLENGE_PENDING", "BREAK_GLASS"}
    ),
    "ACTION_PENDING": frozenset({"ACTION_SUBMITTED"}),
    "ACTION_SUBMITTED": frozenset(
        {"ACTION_SUCCEEDED", "ACTION_FAILED", "ACTION_UNKNOWN"}
    ),
    "OBSERVE": frozenset({"RECONCILED"}),
    "DENIED": frozenset({"RECONCILED"}),
    "ACTION_SUCCEEDED": frozenset({"RECONCILED"}),
    "ACTION_FAILED": frozenset({"HOLD_PENDING", "RECONCILED", "BREAK_GLASS"}),
    "ACTION_UNKNOWN": frozenset({"RECONCILED"}),
    "BREAK_GLASS": frozenset({"ACTION_PENDING", "RECONCILED"}),
    "REJECTED": frozenset(),
    "RECONCILED": frozenset(),
}

DECISION_TO_STATE = {
    "deny": "DENIED",
    "hold": "HOLD_PENDING",
    "challenge": "CHALLENGE_PENDING",
    "allow_reset": "HOLD_PENDING",  # Y1: never auto-execute; hold until release
    "allow_revoke_sessions": "HOLD_PENDING",
    "break_glass": "BREAK_GLASS",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Transition:
    from_state: str
    to_state: str
    at: str
    actor_type: str
    actor_id: str
    reason: str
    ledger_entry_id: str | None = None
    idempotency_key: str | None = None


@dataclass
class Case:
    case_id: str
    action_request_id: str
    tenant_id: str
    state: str
    mode: str  # observe | hold
    protected_action: str
    path_class: str
    subject: dict[str, Any]
    jsm_ticket_ref: dict[str, Any]
    current_decision_id: str | None = None
    current_decision_output: str | None = None
    action_ceiling: list[str] = field(default_factory=list)
    unverified: list[str] = field(default_factory=list)
    degraded: list[str] = field(default_factory=list)
    context_snapshot_id: str | None = None
    calibration_config_id: str | None = None
    jsm_status_key: str | None = None  # SoR evidence only — not a Case enum
    hold_expired: bool = False
    transitions: list[Transition] = field(default_factory=list)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    meta: dict[str, Any] = field(default_factory=dict)

    def transition(
        self,
        to_state: str,
        *,
        actor_type: str,
        actor_id: str,
        reason: str,
        ledger_entry_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> Transition:
        if to_state not in STATES:
            raise ValueError(f"unknown state {to_state}")
        allowed = ALLOWED.get(self.state, frozenset())
        if to_state not in allowed:
            raise ValueError(
                f"illegal transition {self.state} → {to_state} "
                f"(allowed: {sorted(allowed)})"
            )
        if self.state == "VERIFIED" and to_state.startswith("ACTION_"):
            raise ValueError("FORBIDDEN: VERIFIED → ACTION_* skip")
        if self.hold_expired and to_state == "ACTION_PENDING":
            raise ValueError("hold_expired forbids ACTION_PENDING; must DENY")
        if self.mode == "observe" and to_state.startswith("ACTION_"):
            raise ValueError("mode=observe forbids ACTION_* (use BREAK_GLASS path only)")

        tr = Transition(
            from_state=self.state,
            to_state=to_state,
            at=_now(),
            actor_type=actor_type,
            actor_id=actor_id,
            reason=reason,
            ledger_entry_id=ledger_entry_id,
            idempotency_key=idempotency_key or new_id(),
        )
        self.state = to_state
        self.updated_at = tr.at
        self.transitions.append(tr)
        return tr

    def to_public(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "action_request_id": self.action_request_id,
            "tenant_id": self.tenant_id,
            "state": self.state,
            "mode": self.mode,
            "path_class": self.path_class,
            "protected_action": self.protected_action,
            "decision_output": self.current_decision_output,
            "action_ceiling": list(self.action_ceiling),
            "jsm_ticket_ref": self.jsm_ticket_ref,
            "jsm_status_key": self.jsm_status_key,
            "ledger_receipt_id": None,
            "real_gate": False,
        }


def new_case(
    tenant_id: str,
    *,
    mode: str = "observe",
    path_class: str = "jsm_primary",
    subject: dict[str, Any] | None = None,
    jsm_ticket_ref: dict[str, Any] | None = None,
    protected_action: str = "mfa_recovery",
) -> Case:
    case_id = new_id()
    return Case(
        case_id=case_id,
        action_request_id=case_id,
        tenant_id=tenant_id,
        state="RECEIVED",
        mode=mode,
        protected_action=protected_action,
        path_class=path_class,
        subject=subject or {},
        jsm_ticket_ref=jsm_ticket_ref or {},
    )

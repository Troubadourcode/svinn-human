"""Runnable Case API observe stub — stdlib only.

Platform states come from ``case_api.case_sm``. There is no ``sandbox``
import, no Entra/JSM client, and no MFA reset executor.

``real_gate`` is false. ``POST .../release`` records release intent and,
on the hold demo path, moves HOLD_PENDING → ACTION_PENDING. It does not
submit, succeed, or fail an action.
"""

from __future__ import annotations

import json
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from case_api import __version__
from case_api.case_sm import new_case
from case_api.ledger import Ledger
from case_api.store import CaseStore

HOST = os.environ.get("CASE_API_HOST", "127.0.0.1")
PORT = int(os.environ.get("CASE_API_PORT", "8787"))

_store = CaseStore()
_ledger = Ledger()
_idem: dict[tuple[str, ...], tuple[int, dict[str, Any]]] = {}
_lock = threading.Lock()

_PROTECTED = frozenset({"mfa_reset", "mfa_recovery"})
_MODES = frozenset({"observe", "hold"})


def _json(handler: BaseHTTPRequestHandler, code: int, body: Any) -> None:
    data = json.dumps(body, default=str).encode()
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _read(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    n = int(handler.headers.get("Content-Length") or 0)
    if not n:
        return {}
    raw = handler.rfile.read(n).decode() or "{}"
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("json object required")
    return parsed


def _public(case) -> dict[str, Any]:
    pub = _store.get_public(case.action_request_id) or case.to_public()
    receipts = _ledger.for_action(case.action_request_id)
    last = receipts[-1].receipt_id if receipts else None
    pub["ledger_receipt_id"] = last
    pub["real_gate"] = False
    return pub


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:
        code = args[1] if len(args) > 1 else ""
        print(f"[case-api] {self.command} {self.path} {code}")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/healthz":
            return _json(
                self,
                200,
                {
                    "ok": True,
                    "service": "case-api",
                    "version": __version__,
                    "real_gate": False,
                    "mode": "observe",
                    "note": "lab/observe stub; no Entra/JSM executor; no MFA reset execution",
                },
            )
        m = re.fullmatch(r"/v1/tenants/([^/]+)/action-requests/([^/]+)/ledger", path)
        if m:
            tenant, cid = m.group(1), m.group(2)
            with _lock:
                case = _store.get(cid)
                if not case or case.tenant_id != tenant:
                    return _json(self, 404, {"error": "not_found", "real_gate": False})
                return _json(
                    self,
                    200,
                    {
                        "case_id": case.case_id,
                        "real_gate": False,
                        "ledger": _ledger.export(case.case_id),
                    },
                )
        m = re.fullmatch(r"/v1/tenants/([^/]+)/action-requests/([^/]+)", path)
        if m:
            tenant, cid = m.group(1), m.group(2)
            with _lock:
                case = _store.get(cid)
                if not case or case.tenant_id != tenant:
                    return _json(self, 404, {"error": "not_found", "real_gate": False})
                return _json(self, 200, _public(case))
        _json(self, 404, {"error": "not_found", "real_gate": False})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        idem = (self.headers.get("Idempotency-Key") or "").strip()
        try:
            body = _read(self)
        except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
            return _json(self, 400, {"error": "invalid_json", "real_gate": False})

        m = re.fullmatch(r"/v1/tenants/([^/]+)/action-requests", path)
        if m:
            tenant = m.group(1)
            if not idem:
                return _json(self, 422, {"error": "Idempotency-Key required", "real_gate": False})
            protected = body.get("protected_action")
            if protected not in _PROTECTED:
                return _json(
                    self,
                    422,
                    {"error": "protected_action required", "real_gate": False},
                )
            mode = body.get("mode", "hold")
            if mode not in _MODES:
                return _json(self, 422, {"error": "invalid_mode", "real_gate": False})
            key = ("create", tenant, idem)
            with _lock:
                cached = _idem.get(key)
                if cached is not None:
                    return _json(self, cached[0], cached[1])
                case = new_case(
                    tenant,
                    mode=mode,
                    path_class=body.get("path_class", "jsm_primary"),
                    subject=body.get("subject") or {},
                    jsm_ticket_ref=body.get("jsm_ticket_ref") or {},
                    protected_action=protected,
                )
                if body.get("action_request_id"):
                    case.action_request_id = str(body["action_request_id"])
                _store.put(case)
                created = _ledger.append(
                    tenant_id=tenant,
                    case_id=case.case_id,
                    action_request_id=case.action_request_id,
                    kind="case.created",
                    idempotency_key=f"create:{idem}",
                    seen={"path": "case-api", "real_gate": False},
                )
                # Hold demo path stops at HOLD_PENDING. No executor runs.
                if case.mode == "hold":
                    case.transition("VERIFIED", actor_type="system", actor_id="api", reason="create")
                    case.transition("ENRICHING", actor_type="system", actor_id="api", reason="create")
                    case.transition("ASSESSED", actor_type="system", actor_id="api", reason="create")
                    case.transition(
                        "HOLD_PENDING",
                        actor_type="system",
                        actor_id="api",
                        reason="stub_hold",
                    )
                    case.current_decision_output = "allow_reset"
                    case.action_ceiling = list(body.get("action_ceiling") or ["mfa_methods_reset"])
                out = _public(case)
                out["create_receipt_id"] = created.receipt_id
                out["executed"] = False
                _idem[key] = (201, out)
                return _json(self, 201, out)

        m = re.fullmatch(r"/v1/tenants/([^/]+)/action-requests/([^/]+)/release", path)
        if m:
            tenant, cid = m.group(1), m.group(2)
            if not idem:
                return _json(self, 422, {"error": "Idempotency-Key required", "real_gate": False})
            key = ("release", tenant, cid, idem)
            with _lock:
                cached = _idem.get(key)
                if cached is not None:
                    return _json(self, cached[0], cached[1])
                case = _store.get(cid)
                if not case or case.tenant_id != tenant:
                    return _json(self, 404, {"error": "not_found", "real_gate": False})
                if case.mode == "observe":
                    return _json(
                        self,
                        409,
                        {"error": "mode_observe", "state": case.state, "real_gate": False},
                    )
                if case.state != "HOLD_PENDING":
                    return _json(
                        self,
                        409,
                        {"error": "illegal_state", "state": case.state, "real_gate": False},
                    )
                if case.hold_expired:
                    try:
                        case.transition(
                            "DENIED",
                            actor_type="system",
                            actor_id="api",
                            reason="hold_expired",
                        )
                    except ValueError:
                        pass
                    return _json(
                        self,
                        409,
                        {"error": "hold_expired", "state": case.state, "real_gate": False},
                    )
                ceiling_use = body.get("action_ceiling_use") or ["mfa_methods_reset"]
                if (
                    "mfa_methods_reset" not in ceiling_use
                    and "mfa_methods_reset" not in case.action_ceiling
                ):
                    return _json(self, 409, {"error": "ceiling_required", "real_gate": False})
                try:
                    case.transition(
                        "ACTION_PENDING",
                        actor_type="human",
                        actor_id=body.get("approver_id") or "recovery_owner",
                        reason="case_release_intent",
                    )
                except ValueError as exc:
                    return _json(self, 409, {"error": str(exc), "real_gate": False})
                # Intent only. ACTION_PENDING is not submission or success.
                released = _ledger.append(
                    tenant_id=tenant,
                    case_id=case.case_id,
                    action_request_id=case.action_request_id,
                    kind="case.release",
                    idempotency_key=f"release:{idem}",
                    approved={"action_ceiling_use": ceiling_use},
                    intent_only=True,
                    executed=False,
                    real_gate=False,
                )
                out = _public(case)
                out["release_receipt_id"] = released.receipt_id
                out["intent_only"] = True
                out["executed"] = False
                _idem[key] = (200, out)
                return _json(self, 200, out)

        _json(self, 404, {"error": "not_found", "real_gate": False})


def main() -> None:
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Case API observe stub listening on http://{HOST}:{PORT}")
    print("real_gate=false; no Entra/JSM executor; no MFA reset execution")
    print("OpenAPI: packages/case-api/openapi/case-api-v0.yaml")
    httpd.serve_forever()


if __name__ == "__main__":
    main()

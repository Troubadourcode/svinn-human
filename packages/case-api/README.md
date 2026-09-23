# Case API (Platform-owned)

Lab/observe stub for the IRI Case API. **real_gate = NO.** This process does not arm the Action plane: no Entra client, no JSM client, no MFA reset execution, no Slack Action plane.

**Authoritative CaseStatus = Platform** (`ENUM-MAP-CTO.md`, `openapi/case-api-v0.yaml`, `src/case_api/case_sm.py`).

Verified against the handoff state machine and the OpenAPI already on `main`. The enum is:

`RECEIVED`, `REJECTED`, `VERIFIED`, `ENRICHING`, `ASSESSED`, `OBSERVE`, `CHALLENGE_PENDING`, `HOLD_PENDING`, `DENIED`, `ACTION_PENDING`, `ACTION_SUBMITTED`, `ACTION_SUCCEEDED`, `ACTION_FAILED`, `ACTION_UNKNOWN`, `RECONCILED`, `BREAK_GLASS`.

Do not reintroduce shorthand or aliases (`HOLD`, `CHALLENGE`, `RELEASED`, `EXECUTING`, `AUTHORIZED_PENDING_RELEASE`, `DECIDING`, `OPEN`, `ACTION_READY`, `CLOSED`).

| Namespace | Rule |
|---|---|
| Case API `state` | Platform states only (`HOLD_PENDING`, `CHALLENGE_PENDING`, `ACTION_*`, …) |
| `jsm_status_key` / `status_map` | SoR evidence only — separate namespace |
| `real_gate` | Always `false` on this stub |

- `hold_expired` → Case `DENIED` (no release / no `ACTION_PENDING`)
- JSM `authorized` still requires **Case release + ledger** before any future Entra execute. This package does not perform that execute.
- `mode=hold` (request default) walks `RECEIVED → VERIFIED → ENRICHING → ASSESSED → HOLD_PENDING` for a demo and stops. `POST .../release` records intent and moves that case to `ACTION_PENDING`. It does not continue to `ACTION_SUBMITTED` / `ACTION_SUCCEEDED`.
- `mode=observe` stays at `RECEIVED`. Release returns `409` (`mode_observe`).

## Run

Stdlib only (Python 3.10+). No install step and no `sandbox.runtime` dependency.

From the repo root:

```bash
PYTHONPATH=packages/case-api/src python -m case_api
```

Listens on `http://127.0.0.1:8787`. Override with `CASE_API_HOST` and `CASE_API_PORT`.

OpenAPI: `openapi/case-api-v0.yaml`.

## Smoke

```bash
curl -sS http://127.0.0.1:8787/healthz

curl -sS -D - -X POST \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: demo-create-1' \
  -d '{"protected_action":"mfa_reset","mode":"hold","subject":{"upn":"user@example.com"},"jsm_ticket_ref":{"key":"IRI-1"}}' \
  http://127.0.0.1:8787/v1/tenants/acme/action-requests

# use case_id from the create body
curl -sS http://127.0.0.1:8787/v1/tenants/acme/action-requests/CASE_ID
curl -sS http://127.0.0.1:8787/v1/tenants/acme/action-requests/CASE_ID/ledger

curl -sS -X POST \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: demo-release-1' \
  -d '{"approver_id":"recovery_owner","action_ceiling_use":["mfa_methods_reset"]}' \
  http://127.0.0.1:8787/v1/tenants/acme/action-requests/CASE_ID/release
```

Mutating `POST`s require `Idempotency-Key`. Replays of the same key on the same route return the stored success body. Create keys are scoped by tenant; release keys are scoped by tenant + case id.

## Layout

| Path | Role |
|---|---|
| `src/case_api/case_sm.py` | Platform transitions |
| `src/case_api/store.py` | In-memory cases |
| `src/case_api/ledger.py` | Append-only receipts (`real_gate: false`) |
| `src/case_api/server.py` | HTTP stub |
| `src/case_api/__main__.py` | `python -m case_api` |

Paths: `/healthz`, `/v1/tenants/{tenant_id}/action-requests`, `GET` case, `POST` release, `GET` ledger.

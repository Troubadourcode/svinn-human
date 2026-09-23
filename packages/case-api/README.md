# Case API (Platform-owned)

**Authoritative CaseStatus enum = Platform** (see `ENUM-MAP-CTO.md` and `openapi/case-api-v0.yaml`).  
Do not reintroduce CTO shorthand (`HOLD`, `CHALLENGE`, `RELEASED`, `EXECUTING`, `AUTHORIZED_PENDING_RELEASE`, `DECIDING`).

| Namespace | Rule |
|---|---|
| Case API `state` | Platform states only (`HOLD_PENDING`, `CHALLENGE_PENDING`, `ACTION_*`, …) |
| `jsm_status_key` / `status_map` | SoR evidence only — separate namespace |

- `hold_expired` → Case `DENIED` (no release / no ACTION_PENDING)
- JSM `authorized` still requires **Case release + ledger** before Entra execute
- Workspace runnable stub (pre-push): `/workspace/svinn-platform/packages/case-api/` on `:8787`

Paths align with Platform stub: `/v1/tenants/{tenant_id}/action-requests/...`

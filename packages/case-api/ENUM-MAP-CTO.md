# CaseStatus enum map — CTO scaffold → Platform (authoritative)

CTO path (reference): `/workspace/svinn-human-scaffold/packages/case-api/openapi/case-api-v0.yaml`

| CTO label | Platform Case state (wins) | Notes |
|-----------|----------------------------|-------|
| RECEIVED | RECEIVED | same |
| *(missing)* | VERIFIED | after ingest integrity |
| ENRICHING | ENRICHING | same |
| DECIDING | ASSESSED | Decision computed; not a Case enum skip |
| HOLD | HOLD_PENDING | Y1 allow_reset lands here |
| CHALLENGE | CHALLENGE_PENDING | |
| AUTHORIZED_PENDING_RELEASE | HOLD_PENDING | JSM authorized ≠ Case state; still HOLD until release |
| RELEASED | ACTION_PENDING | after Case POST release |
| EXECUTING | ACTION_SUBMITTED / ACTION_SUCCEEDED / ACTION_FAILED / ACTION_UNKNOWN | finer Platform states |
| RECONCILED | RECONCILED | same |
| DENIED | DENIED | hold_expired → DENIED |
| *(missing)* | OBSERVE | shadow mode |
| *(missing)* | REJECTED | bad ingest |
| *(missing)* | BREAK_GLASS | dual-control |

**Rule:** do not rename Platform states to CTO shorthand in monorepo. Keep OpenAPI aligned with `sandbox/runtime/case_sm.py`. Correlate JSM via `jsm_ticket_ref` + `jsm_status_key` (evidence only).

# CaseStatus enum map — CTO scaffold → Platform (authoritative)

Platform CaseStatus is the source of truth. Names below were verified against:

- `openapi/case-api-v0.yaml` (`CaseStatus` enum)
- `src/case_api/case_sm.py` (`STATES`, ported from the workspace handoff)

They match. A shorter alias list (`OPEN`, `ACTION_READY`, `CLOSED`) does **not** appear in either source and is not used.

CTO path (historical scaffold reference): `/workspace/svinn-human-scaffold/packages/case-api/openapi/case-api-v0.yaml`

| CTO label | Platform Case state (wins) | Notes |
|-----------|----------------------------|-------|
| RECEIVED | RECEIVED | same |
| *(missing)* | VERIFIED | after ingest integrity |
| ENRICHING | ENRICHING | same |
| DECIDING | ASSESSED | Decision computed; not a Case enum skip |
| HOLD | HOLD_PENDING | Y1 allow_reset lands here |
| CHALLENGE | CHALLENGE_PENDING | |
| AUTHORIZED_PENDING_RELEASE | HOLD_PENDING | JSM authorized ≠ Case state; still HOLD until release |
| RELEASED | ACTION_PENDING | after Case POST release (intent only in this stub) |
| EXECUTING | ACTION_SUBMITTED / ACTION_SUCCEEDED / ACTION_FAILED / ACTION_UNKNOWN | finer Platform states; observe stub does not enter these |
| RECONCILED | RECONCILED | same |
| DENIED | DENIED | hold_expired → DENIED |
| *(missing)* | OBSERVE | shadow mode |
| *(missing)* | REJECTED | bad ingest |
| *(missing)* | BREAK_GLASS | dual-control |

**Not CaseStatus** (do not invent or rename to these): `OPEN`, `HOLD`, `CHALLENGE`, `RELEASED`, `EXECUTING`, `AUTHORIZED_PENDING_RELEASE`, `ACTION_READY`, `CLOSED`, `DECIDING`.

**Rule:** do not rename Platform states to CTO shorthand in the monorepo. Keep OpenAPI aligned with `packages/case-api/src/case_api/case_sm.py`. Correlate JSM via `jsm_ticket_ref` + `jsm_status_key` (evidence only).

**real_gate:** NO. The in-repo server is a lab/observe stub. Release records intent. It does not call Entra or JSM and does not execute MFA reset.

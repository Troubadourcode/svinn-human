# IRI Architecture One-Pager
**Approach A:** async overlay + System-of-Record (SoR) gate  
**SoRs:** Microsoft Entra (identity / MFA) + Jira Service Management (recovery workflow)  
**Principle:** Observe/Verify first; Hold/Challenge before reset. Never silent auto-reset day one.

---

## Six planes (+ Governance light)

```
JSM events / Entra signals (+ Slack evidence later; Zoom/email next wave)
        │
        ▼
┌───────────────┐
│   EVIDENCE    │  Ingest ticket fields, attachments metadata, agent notes,
│               │  prior receipts. Integrity tags (source, time, hash).
└───────┬───────┘
        ▼
┌───────────────┐
│   CONTEXT     │  Enrich: user risk, recent sign-ins, prior resets,
│               │  tenure, device posture (as available). Sensors only.
└───────┬───────┘
        ▼
┌───────────────┐
│   DECISION    │  Runs decision order (below) via OPA/policy + scoring.
│               │  Outputs: deny | hold | challenge | allow(with ceiling)
└───────┬───────┘
        ▼
┌───────────────┐     ┌──────────────┐
│   CHALLENGE   │────▶│   (response  │  Bound channel; proof returns
│               │     │   → Evidence)│  as new evidence, not a side door.
└───────┬───────┘     └──────────────┘
        ▼
┌───────────────┐
│   ACTION      │  Tenant-scoped Entra write executor only.
│               │  MFA reset / revoke sessions / etc. within ceiling.
└───────┬───────┘
        ▼
┌───────────────┐
│   LEDGER      │  Append-only decision + action receipts.
└───────────────┘

GOVERNANCE (light): policy versions, calibration configs, break-glass roles,
two-person bindings, tenant credential registry. Not a seventh runtime plane.
```

**Platform owns:** event/action schema, queue, OPA policy wiring, decision/action ledger storage.  
**Integrations owns:** Entra + JSM connectors, scopes, tenant PoC.  
**Security owns:** KMS, secrets, CI/CD, credential separation.  
**Detection owns:** rules calibration, frozen test sets, red-team scenarios.

---

## Decision order (strict)

1. **Integrity** — Is evidence/context authentic and fresh enough?  
2. **Capability** — Does this tenant/actor/credential have the right to even consider this action?  
3. **Hard rules** — Absolute deny/hold (e.g. missing two-person, cross-tenant, agent self-elevate).  
4. **Scoring** — Risk / confidence model.  
5. **Calibration** — Thresholds per tenant/policy version.  
6. **Action ceiling** — Max impact allowed (reset MFA? also revoke sessions? never domain-wide).  
7. **Receipt** — Persist decision before or atomically with Action; no action without ledger id.

Natural language in tickets cannot skip steps 1–3 or raise the ceiling.

---

## Authority boundaries

| Role | Propose | Verify | Approve | Execute |
|---|---|---|---|---|
| End user | Request via JSM | Respond to challenges | — | — |
| Helpdesk agent | Open/update ticket; propose recovery | Collect evidence | Low-impact only if policy allows | **No** Entra write in Approach A default |
| SVINN Decision | — | Policy verify | Automated allow/hold/challenge within ceiling | — |
| Human approver (named) | — | — | High-impact (two-person) | — |
| Action executor (machine) | — | — | — | Entra writes only after Decision + receipt |
| Break-glass admin | — | — | Dual-control emergency | Time-boxed execute + mandatory review |

**Two-person rule:** for high-impact actions (MFA reset, session revoke-all, disable+reset combo), `proposer ≠ approver`, and executor is never the approver’s interactive session in Approach A (machine executor + human approve).

**Credential separation:** read sensor apps ≠ write executor apps; separate secrets, separate KMS keys where practical; Capability step fails closed on mismatch.

---

## Tenant isolation

- One Entra app registration (or managed identity set) **per customer tenant** for write; never shared.  
- JSM site / project binding stored in tenant registry (Governance).  
- Queue partitions / ledger rows keyed by `tenant_id`; OPA input always includes it.  
- No cross-tenant Context joins.  
- Integrations PoC must prove wrong-tenant execute is impossible by construction.

---

## Fail modes

| Component | Mode | Notes |
|---|---|---|
| Sensors / Context enrichers | **Fail-open + alert** | Missing signal ≠ allow reset; Decision still runs hard rules; alert SRE |
| Identity sync / SoR gate (can we see truthful Entra state?) | **Fail-closed** | Only with published SLO + dual-control break-glass |
| Decision / OPA | Fail-closed on error | Prefer hold over allow |
| Action executor | Fail-closed | No partial “best effort” MFA reset without receipt |
| Ledger write | Fail-closed for Action | Action blocked if receipt cannot be persisted |

---


---

## Channel evidence waves (founder lock 2026-09-23)

- **MVP SoRs:** Entra + JSM only for Action.  
- **Slack:** **evidence first** (Evidence plane ingest / correlation). **SK2/SK3** Slack act capabilities stay **gated** until Lead opens.  
- **Zoom / email:** **evidence-only**, Next wave — not Action, not day-0 sandbox dependency.  
- **Marketing:** claim **"built to plug in"** only until the channel is live; architecture does not pretend Slack/Zoom/email are shipping Action.

Platform sandbox / observe stub for Entra+JSM is **not** blocked by Slack/Zoom/email wave work.

## Approach A vs B (boundary)

- **A (now):** async overlay on JSM + gate before Entra mutation; humans remain in loop for high impact.  
- **B (later, design partner):** tighter inline control / richer automation — requires this threat model + eval sets green.

---

## Day-0 interfaces to freeze with peers

1. Evidence event schema (Platform + Integrations)  
2. Decision output enum + action ceiling vocabulary (Platform + CTO)  
3. Entra permission matrix — least privilege write set (Integrations + Security + CTO)  
4. Ledger receipt fields (Platform + Detection for eval replay)

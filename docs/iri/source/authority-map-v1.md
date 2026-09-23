# IRI Authority Map v1 (FROZEN)
**Source:** New Bot SVINN Lead defaults (2026-09-23), including founder-path locks  
**Scope:** Approach A — Decision layer before MFA reset / account recovery on Entra + JSM Cloud  
**Unit of work:** action request (not “suspicious message”)  
**Status:** FROZEN — Yossef may override  

---

## Actors (canonical)

| Actor | Role |
|---|---|
| End user | Beneficiary of recovery — never approver of their own reset |
| Helpdesk agent | Initiator in JSM — proposes recovery action request |
| Named approver / recovery owner | Customer-owned role (IAM / security / manager) — **≠ initiator ≠ beneficiary**. Svinn does **not** staff customer approvers; product supports **role mapping** |
| Svinn agent | Propose / decide / challenge orchestrate — **not** Global Admin; never Entra write in Y1 without human approve or completed challenge |
| Entra | IdP / SoR for auth methods + sessions |
| JSM Cloud | Ticket / approval SoR (Approach A default; if flipped to Data Center, Integrations revises binding only) |
| Break-glass operator | Separate TTL’d accounts; two-person for high privilege; quarterly review; not routine path |

---

## Authority matrix

| Action | Propose | Verify / Challenge | Approve | Execute (Entra write) |
|---|---|---|---|---|
| Open recovery ticket | Helpdesk or end user | — | — | — |
| Create action request (MFA reset) | Helpdesk (initiator) or Svinn propose | Svinn Decision + Challenge plane | — | — |
| Clear challenge | OOB to IdP/HR recovery owner or manager (bound channel) | Challenge plane records proof → Evidence | — | — |
| Allow MFA reset | — | Integrity→Capability→Hard rules→…→Receipt | Human approve **or** completed challenge (Y1: **no auto-execute**). MFA-reset enforcement **requires challenge** (or risk-tiered 2nd approver) | — |
| Execute MFA reset | — | — | Prior allow + receipt | Write executor principal only |
| Session revoke (containment) | Helpdesk or Svinn | Same decision order | **Separate** approval + read-back | Write executor; **not** coupled to every reset |
| Break-glass bypass | Break-glass role | Dual control / two-person high privilege | Dual control | TTL’d break-glass account; ledger + **quarterly review** |

### Hard separations
- **proposer ≠ approver ≠ beneficiary** for high-impact  
- **Read sensor principal ≠ write executor principal**  
- Svinn agent is **not** Global Admin  
- No auto-execute of MFA reset in Y1  
- Challenge channel: OOB to IdP/HR recovery owner or manager — never initiator, never beneficiary as sole approver  

---

## Verify / challenge bar (LOCKED)

- Out-of-band to **IdP/HR recovery owner or manager**  
- Challenge recipient **≠ initiator ≠ beneficiary**  
- MFA-reset enforcement requires **completed challenge**, or a **risk-tiered second approver** path  
- Ticket natural language cannot clear challenge or raise ceiling  

---

## Decision outputs (Action ceiling vocabulary)

| Output | Meaning |
|---|---|
| `deny` | Do not proceed; ledger receipt |
| `hold` | Wait for human / more evidence |
| `challenge` | OOB challenge required; response re-enters Evidence |
| `allow_reset` | MFA reset permitted after human approve **or** completed challenge (or risk-tiered 2nd approver) |
| `allow_revoke_sessions` | Separate ceiling; optional containment; own approval + read-back |
| `break_glass` | Explicit emergency path only |

---

## Fail modes (locked)

| Component | Mode |
|---|---|
| Sensors / Context | Fail-open + alert |
| Identity sync / SoR gate | Fail-closed **only** with SLO + break-glass |
| Decision error | Fail-closed → hold/deny |
| Action without ledger receipt | Fail-closed (block write) |

Numeric SLO / break-glass TTL (**LOCKED** by New Bot 2026-09-23): **break-glass account TTL 4h**; **identity-gate SLO 99.9% monthly**. Yossef may override.

---

## Tenancy & data (locked)

- PoC = **single-tenant per design partner** first  
- Public product names: **Entra + JSM only** (JSM **Cloud** default)  
- Tenant-bound write credentials; Capability check enforces tenant match  
- **Residency/retention:** regional SaaS default; **raw retention = 0**; store metadata / hash / pointers; DPIA with Security + Product  

---

## Shadow → enforce path

1. **Observe/shadow** — Decision runs; no gate on write yet; ledger + eval  
2. **Verify/Hold + challenge** — gate before reset dispatch  
3. Approach B later with design partner (out of this freeze)

---

## Lead confirms (2026-09-23, New Bot)

- **SSPR:** OUT of Approach A MVP. Helpdesk/ticket (JSM) path only. `path_class=self_service_sspr` may still appear for observe/deny/eval labeling.
- **JSM wait-on-status ownership:** Svinn = Decision hold/challenge; customer = workflow status names; Integrations = reference workflow.
- **Canon:** No separate decision-report §6. Working architecture = this authority map + Platform schemas under `/workspace/svinn-platform/`.
- **Origin/repo:** Still founder-open (blocks Platform runnable observe stub). Peers continue on contracts/field maps until home is chosen.

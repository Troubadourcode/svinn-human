# svinn-human

**Identity Recovery Interlock (IRI)** — Approach A async overlay + System-of-Record gate.

| SoR | Role |
|---|---|
| Microsoft Entra | Identity / MFA; write executor only after Case release + ledger |
| Jira Service Management | Recovery workflow (Cloud); ticket status = evidence, not Case enum |

## Planes

Evidence → Context → Decision → Challenge → Action → Ledger (+ Governance light)

## Repo map

| Path | Owner | Notes |
|---|---|---|
| `packages/case-api/` | **Platform** | Case API skeleton (Platform Case states ≠ `jsm.status_map`) |
| `contracts/` | Platform + Integrations | Correlation / enricher contracts |
| `docs/iri/` | CTO | Architecture / authority / channel waves |

## Channel waves (founder lock 2026-09-23)

- **Slack:** evidence first; **SK2/SK3** Slack act **gated**
- **Zoom / email:** evidence-only Next wave
- **Marketing:** “built to plug in” until live
- MVP Action plane = Entra + JSM only

## Hard rules (Y1)

- No auto-execute MFA reset (human approve or completed challenge)
- Read sensor principal ≠ write executor; only Action plane fetches executor KMS material
- Raw retention 0 (metadata / hash / pointers)
- `authorized` (JSM) still requires **Case release + ledger receipt** before Entra write

## License

Apache-2.0 — see `LICENSE`.

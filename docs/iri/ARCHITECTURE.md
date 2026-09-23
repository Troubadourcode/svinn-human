# IRI architecture (summary)

Six planes: **Evidence → Context → Decision → Challenge → Action → Ledger**.

Decision order: Integrity → Capability → Hard rules → Scoring → Calibration → Action ceiling → Receipt.

**Case API** statuses are Platform states (`RECEIVED` … `RECONCILED`). They are **not** JSM `status_map` keys. Correlate via `status_map` + ticket ref. See `contracts/`.

Sensors: fail-open + alert. Identity sync gate: fail-closed only with SLO + break-glass.

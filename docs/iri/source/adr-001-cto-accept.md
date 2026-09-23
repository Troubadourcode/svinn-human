# ADR-001 CTO acceptance — 2026-09-23

**Decision:** Microsoft Graph via READ sensor for single-tenant PoC observe.  
**Defer:** Event Hub until volume, sub-minute SLA, or Graph throttling forces it.  
**Unchanged:** raw retention 0; fail-open+alert on missing/lagged signals; JSM SoR gate unrelated.

Source: `/workspace/svinn-integrations/mvp/adrs/ADR-001-graph-vs-event-hub.md`

## Platform ACK (2026-09-23)
Context enricher consumes Graph READ sensor under fail-open+alert. No streaming assumption for MVP. See `/workspace/svinn-platform/contracts/context-enricher-graph-v0.md`.

## Workflow correlation
Case API statuses (RECEIVED…RECONCILED) are a separate namespace from `jsm.status_map` keys. Correlate via status_map + ticket ref. Doc: `/workspace/svinn-platform/contracts/jsm-case-correlation-v0.md`.

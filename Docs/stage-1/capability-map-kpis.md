# Capability Map and KPIs

## Capability map

| Area | Capabilities |
|---|---|
| Asset management | Equipment CRUD, criticality, service date, health status |
| Monitoring | Parameter configuration, thresholds, readings, reading history |
| Alerting | Breach detection, deduplication, prioritization, clearing |
| Maintenance | Alert conversion, work-order editing, parts, closure |
| Governance | Role-aware actions, structured errors, audit-friendly metadata |
| Platform | FastAPI API, PostgreSQL persistence, OpenAPI, React frontend |

## MVP KPIs

- 100% of configured threshold boundary cases produce the documented result.
- Zero duplicate work orders for a single alert.
- 100% of closed work orders contain required closure data.
- API contract tests pass with no open P0/P1 defects before release.
- Core frontend flows have passing typecheck, build, and automated tests.
- All non-2xx API responses use the documented problem envelope.

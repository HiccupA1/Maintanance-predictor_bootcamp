# Assumptions, Constraints, and Risks

## Assumptions

- The MVP serves one plant.
- One maintenance engineer is available, so explicit assignment is unnecessary.
- Readings may be numeric or non-numeric.
- Threshold breach boundaries are inclusive.
- A generic `N/A` parts line satisfies closure when no physical part is used.

## Constraints

- Authentication is intentionally deferred.
- Configuration comes from environment variables; secrets are not committed.
- PostgreSQL is the intended runtime database; tests can use in-memory SQLite.
- The existing FastAPI and React/Vite structure should be preserved.
- Alert priority bands and notification behavior remain configurable/open.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Development identity shim is mistaken for auth | High | Document prominently; replace with real authentication before production. |
| Threshold rules are misunderstood | Medium | Show inclusive semantics and “no limit” states in the UI. |
| Duplicate alerts create noise | High | Enforce one active alert per equipment/parameter pair. |
| Closure data is incomplete | Medium | Validate resolution notes, root cause, and parts lines before closure. |
| Dependency/security findings remain unresolved | Medium | Track frontend audit and build findings as release blockers or follow-up work. |

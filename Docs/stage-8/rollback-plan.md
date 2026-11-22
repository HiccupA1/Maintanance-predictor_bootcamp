# Rollback Plan

## Decide
1. Stop promotion if smoke tests (`smoke-tests.md`) or readiness gates fail.
2. Keep logs and correlation ids (`X-Correlation-Id`) for diagnosis.
3. Name the rollback owner and record the decision.

## Application
4. **API:** redeploy the previous image tag. Images are immutable, one per
   commit on `main`.
5. **Frontend:** promote the previous Vercel deployment.
6. Re-run smoke tests 1 to 6.

## Database
7. **Migrations are expand-only** (0002 and 0003 only add nullable or
   defaulted columns and new tables), so the previous API image runs against
   the newer schema. **Do not downgrade the schema** as part of an application
   rollback.
8. If a migration itself is faulty, prefer a reviewed forward fix. Use
   `alembic downgrade <revision>` only as a reviewed exception, after a
   backup, and never `downgrade base` on a live database.
9. **0004 (D17)** is the exception that may need a fast revert: if the API
   loses database access after it is applied, the migration's own role check
   should already have prevented that. If it did not,
   `alembic downgrade 0003_model_registry_risk_scores` restores the old
   policies (and reopens D17). Then fix the API's database role.

## ML models
10. **Stop model alerts immediately:** in Admin → Models, set the active
    version to `shadow`, or set `SCORING_ENABLED=false` and restart.
    Threshold alerts and readings are unaffected.
11. **Return to a previous version:** activate a version that is still in
    shadow. Retired versions cannot be reinstated, so re-register the artifact
    as a new version.
12. Close open MODEL alerts with an accurate `failure_confirmed` value.

## Close out
13. Record the incident, the root cause, and the follow-up owner and date.

# Rollback Plan

1. Stop promotion if smoke tests or readiness gates fail.
2. Route traffic to the last known-good application version.
3. Preserve logs and correlation IDs for diagnosis.
4. Do not automatically downgrade database migrations; use a reviewed compensating migration.
5. Restore the last known-good frontend and backend artifacts.
6. Re-run health, database readiness, and core workflow smoke tests.
7. Record the incident, decision, and follow-up owner.

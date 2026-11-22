# Release Smoke Tests

Run these against each environment after a deployment: staging first, then
production. Use a real user of each role; there is no dev identity shim
outside `APP_ENV=dev`.

## API and platform
1. `GET /v1/health` returns `200 {"status":"ok"}`.
2. `GET /v1/health/db` returns `200`, with `"database":"ok"`.
3. `GET /v1/equipment` without a token returns `401`.
4. In production, `GET /docs` and `GET /openapi.json` return `404`
   (docs are off by default).
5. **Data API closed (D17):**
   `curl -H "apikey: <publishable key>" -H "Authorization: Bearer <user token>" https://<ref>.supabase.co/rest/v1/equipment?select=*`
   returns no rows, or a permission error.
6. `alembic current` reports the expected head.

## Workflows (frontend)
7. Sign in as each role and check the landing page and navigation:
   - Operator: Readings only.
   - Plant Manager: Alerts.
   - Maintenance Engineer: Work Orders.
   - Admin: Work Orders, plus Admin and Models.
8. As **Operator**, record a reading and check that it appears in the history
   with your name as `entered_by`.
9. Record a reading that breaches a threshold. As **Plant Manager**, open the
   alert and convert it to a work order. A second conversion attempt must be
   refused.
10. As **Maintenance Engineer**, close the work order with resolution notes,
    root cause, "failure confirmed" and a failure mode. Check that the alert is
    resolved and the equipment's last service date is updated.

## ML (only if a model is registered)
11. As **Admin**, open Models: the version shows its stage, evaluation and
    drift.
12. On a machine with `asset_class` set and all six inputs mapped, record a
    reading. The risk panel updates within about 10 s. Non-admins see shadow
    scores as "no scores".

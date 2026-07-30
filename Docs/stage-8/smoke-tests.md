# Release Smoke Tests

1. `GET /health` returns 200.
2. `GET /health/db` confirms database readiness.
3. Open `/docs` and `/openapi.json`.
4. Load the frontend application.
5. Select each development persona and verify role-aware navigation.
6. Create or inspect equipment.
7. Record a reading and verify history.
8. Trigger a threshold breach and inspect the alert.
9. Convert the alert into one work order.
10. Close the work order with valid closure data.
11. Verify alert resolution and service-date update.

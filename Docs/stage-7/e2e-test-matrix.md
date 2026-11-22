# End-to-End Test Matrix

Browser tests in `frontend/e2e/specs/`, run by Playwright against a **production frontend build**, the **real API** and **Postgres**. Sign-in uses Supabase-shaped sessions signed by a test key, and the API verifies them through its real JWKS path. Only the Supabase Auth HTTP endpoints are stubbed (`Docs/runbooks/e2e.md`).

**111 tests.** They run in CI (job `E2E (Playwright)`, part of the required **CI OK** check) with no retries. Before merge, the full suite passed twice in a row locally. Regenerate the test list with `npm run e2e -- --list`.

| Area | Tests | What is covered | Requirement |
|---|---|---|---|
| Role-based access | 28 | Every role × every page: landing page, nav visibility, allowed vs redirected routes | authorization-matrix.md |
| Authentication | 9 | Sign-in form, wrong credentials, sign-out, session persistence, off-site redirect protection | Security review; open-redirect fix |
| Equipment registry | 10 | Create, validate, duplicate id, edit, list, not-found, role limits | PRD FR1 |
| Parameters and thresholds | 7 | Create, validation rules, edit, role limits | PRD FR2 |
| Readings and threshold alerts | 11 | Inclusive bounds, priority by criticality, deduplication, recovery, non-numeric, correction, attribution | PRD FR3–FR6 |
| Alert triage and conversion | 6 | List, detail, linked conversion, duplicate refusal, role limits | PRD FR7 |
| Work orders and closure | 14 | Edit, filters, page size 200 (D4), closure validation, closure side effects, immutability | PRD FR8–FR10 |
| User administration | 4 | List, add, change role, delete | authorization-matrix.md |
| Failure-risk scoring | 8 | Not configured, shadow hidden vs admin-visible, Models page, activation, MODEL alert raised and resolved, return to shadow | ADR-0006/0007; ml-models.md |
| Resilience | 5 | Load failure with retry, profile failure without redirect loop, API health indicator, unknown route | System test strategy |
| Accessibility | 8 | axe-core WCAG 2.1 A/AA, no serious or critical violations on each main page | System test strategy |
| Workflow benchmark | 1 | Breach to closed work order across three roles, with every user action recorded | workflow-comparison.md |

## Catalogue

### Role-based access (`rbac.spec.ts`)

- Admin lands on /work-orders and sees their name and role
- Admin can open /readings
- Admin can open /work-orders
- Admin can open /equipment
- Admin can open /alerts
- Admin can open /admin/users
- Admin can open /admin/models
- PlantManager lands on /alerts and sees their name and role
- PlantManager can open /readings
- PlantManager can open /work-orders
- PlantManager can open /equipment
- PlantManager can open /alerts
- PlantManager cannot open /admin/users
- PlantManager cannot open /admin/models
- Operator lands on /readings and sees their name and role
- Operator can open /readings
- Operator cannot open /work-orders
- Operator cannot open /equipment
- Operator cannot open /alerts
- Operator cannot open /admin/users
- Operator cannot open /admin/models
- MaintenanceEngineer lands on /work-orders and sees their name and role
- MaintenanceEngineer can open /readings
- MaintenanceEngineer can open /work-orders
- MaintenanceEngineer can open /equipment
- MaintenanceEngineer can open /alerts
- MaintenanceEngineer cannot open /admin/users
- MaintenanceEngineer cannot open /admin/models

### Authentication (`auth.spec.ts`)

- an anonymous visitor is sent to sign in, keeping the requested page
- signing in with the form lands an Operator on Readings
- signing in returns the user to the page they asked for
- wrong credentials show an error and stay on the sign-in page
- post-login redirect refuses an off-site target (/\evil.example)
- post-login redirect refuses an off-site target (//evil.example)
- post-login redirect refuses an off-site target (https://evil.example)
- signing out clears the session and protects pages again
- the session survives a page reload

### Equipment registry (`equipment.spec.ts`)

- a Plant Manager can view equipment but not create it
- as Admin: creates equipment and opens its detail page
- as Admin: requires every field
- as Admin: rejects criticality 0
- as Admin: rejects criticality 6
- as Admin: rejects criticality 2.5
- as Admin: reports a duplicate equipment id
- as Admin: edits equipment
- as Admin: lists equipment with a link to its detail page
- as Admin: shows a not-found state for an unknown id

### Parameters and thresholds (`parameters.spec.ts`)

- an Admin sees parameters but cannot add them
- as Plant Manager: adds a parameter with thresholds
- as Plant Manager: requires at least one threshold
- as Plant Manager: rejects a minimum above the maximum
- as Plant Manager: requires a name and unit
- as Plant Manager: edits an existing threshold
- as Plant Manager: cannot edit the equipment record itself

### Readings and threshold alerts (`readings.spec.ts`)

- a Plant Manager can review readings but the capture form is disabled
- as Operator: records an in-range reading under the verified name, with no alert
- as Operator: a reading exactly at the maximum raises an alert (inclusive)
- as Operator: a reading exactly at the minimum raises an alert (inclusive)
- as Operator: a breach on critical equipment is raised as CRITICAL
- as Operator: a breach on ordinary equipment is raised as HIGH
- as Operator: a repeat breach updates the open alert instead of adding one
- as Operator: an in-range reading after a breach resolves the alert
- as Operator: a non-numeric observation is stored and raises no alert
- as Operator: validates the capture form
- as Operator: corrects a recent reading with a reason

### Alert triage and conversion (`alerts.spec.ts`)

- a Maintenance Engineer sees alerts but cannot convert them
- as Plant Manager: lists a breach with its equipment and parameter
- as Plant Manager: opens alert detail with the conversion action
- as Plant Manager: converts an alert into one work order linked to it
- as Plant Manager: refuses a second work order for the same alert
- as Plant Manager: shows a not-found state for an unknown alert

### Work orders and closure (`work-orders.spec.ts`)

- as Maintenance Engineer: the detail page is titled by the work order
- as Maintenance Engineer: closing reveals the closure record fields
- as Maintenance Engineer: closure requires resolution notes
- as Maintenance Engineer: closure requires a root cause
- as Maintenance Engineer: closure requires saying whether it was a failure
- as Maintenance Engineer: a confirmed failure requires a failure mode
- as Maintenance Engineer: closing records the label, resolves the alert and updates the service date
- as Maintenance Engineer: a false alarm is closed without a failure mode
- as Maintenance Engineer: a closed work order cannot be edited
- as Plant Manager: edits an open work order
- as Plant Manager: filters the list by status
- as Plant Manager: filters the list by priority
- as Plant Manager: loads the maximum page size (D4 regression)
- as Plant Manager: shows a not-found state for an unknown work order

### User administration (`admin.spec.ts`)

- lists application users with their roles
- adds a user with a role
- changes a user's role
- deletes a user after confirmation

### Failure-risk scoring (`ml.spec.ts`)

- equipment without a model asset class is shown as not scored
- shadow scores are hidden from a Plant Manager
- an Admin sees the shadow score, labelled as shadow
- the Models page shows the shadow evaluation and drift
- an Admin activates the model from the Models page
- an active model raises a MODEL alert that users can see
- a normal reading on an active model resolves its MODEL alert
- an Admin returns the model to shadow

### Resilience (`resilience.spec.ts`)

- a failed list load shows an error with a working retry
- if the profile cannot be loaded the user sees why, not a redirect loop
- the header reports when the API is unreachable
- the header reports a healthy API
- an unknown route shows a not-found page

### Accessibility (`a11y.spec.ts`)

- sign-in page has no serious or critical accessibility violations
- readings page has no serious or critical accessibility violations
- work orders page has no serious or critical accessibility violations
- equipment page has no serious or critical accessibility violations
- alerts page has no serious or critical accessibility violations
- admin users page has no serious or critical accessibility violations
- models page has no serious or critical accessibility violations
- equipment detail page has no serious or critical accessibility violations

### Workflow benchmark (`workflow-benchmark.spec.ts`)

- workflow benchmark: breach to closed work order, recorded

## Not covered

- The real Supabase Auth service. It is covered by the staging smoke tests (`Docs/stage-8/smoke-tests.md`).
- Browsers other than Chromium, and mobile viewports.
- A manual accessibility audit. Automated axe checks find only part of the WCAG issues.

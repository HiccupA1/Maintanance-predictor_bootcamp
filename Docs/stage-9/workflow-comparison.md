# Workflow Comparison: Manual Process vs the App

**Generated:** 2026-11-22 by `python -m tools.workflow_benchmark.report`
from `tools/workflow_benchmark/baseline.json` (manual) and the recorded
Playwright run `reports/workflow-app.json` (app,
`frontend/e2e/specs/workflow-benchmark.spec.ts`). Do not edit by hand.

## Scenario (identical for both)
1. An Operator records a reading that breaches a threshold.
2. The Plant Manager raises a work order for it.
3. The Maintenance Engineer closes it with resolution notes, a root cause and
   the failure outcome.
4. The issue ends resolved, and the asset's last-service date is updated.

Both flows type the same free text. The manual process is described in
`Docs/stage-9/workflow-baseline-sop.md`. **That baseline is an assumption**
and should be validated with a maintenance team.

## Results

| Measure | Manual | App | Reduction |
|---|---|---|---|
| User steps | 59 | 20 | **66.1%** |
| Characters typed | 540 | 55 | 89.8% |

### Steps by role
| Role | Manual | App |
|---|---|---|
| Operator | 17 | 5 |
| PlantManager | 24 | 6 |
| MaintenanceEngineer | 18 | 9 |

### Estimated operator time (Keystroke-Level Model)
| Assumptions | Manual | App | Reduction |
|---|---|---|---|
| low (fast user, quick system) | 314 s (5.2 min) | 78 s (1.3 min) | **75.2%** |
| mid (KLM average typist) | 386 s (6.4 min) | 85 s (1.4 min) | **77.9%** |
| high (slow typist, slow system) | 620 s (10.3 min) | 106 s (1.8 min) | **82.8%** |

Across all three assumption sets, estimated operator time falls by
**75.2% to 82.8%**.

For reference, the scripted browser completed the app flow in
5.5 s. That is machine speed, not human time, and
is not used in any comparison.

## What the app does that the manual process makes people do
- Reading timestamped and attributed to the signed-in user
- Threshold checked (inclusive bounds)
- Alert raised with machine, parameter, value, limits and priority
- Work order linked to the alert and prefilled with the machine
- Duplicate work orders for the same alert prevented
- Closure timestamped and attributed to the signed-in engineer
- Source alert resolved
- Equipment's last-service date updated
- Failure label stored for model retraining

## Method
- **Step:** one user action, meaning opening an app or page, a click, a
  dropdown choice, typing into a field, a visual lookup, or a by-eye
  comparison. Both flows use the same vocabulary. The app flow is counted
  automatically while Playwright drives the real UI.
- **Time:** the Keystroke-Level Model (Card, Moran and Newell, 1980), using
  the published operator times (K, P, B, H, M) and the same per-action rules
  for both flows (`klm.py`).
- **Assumptions:** system response time, visual search and by-eye comparison
  are not KLM operators. They take labelled low, mid and high values, and the
  range above covers all of them.
- **Fairness:**
  - The manual process is entirely at a desktop computer, with no paper and
    no walking, and with no waiting for email replies.
  - Opening the app counts as a step for every role, the same as opening an
    email.
  - Both choices favour the manual process.

## Limitations
- This is a **modelled** estimate, not timed users. KLM predicts expert,
  error-free performance. Real users make errors, which typically affect the
  manual process more (retyping across sheets).
- The baseline is a documented assumption, not an observed client process.
- **Not counted:** notification latency (the app has no push notifications;
  someone must open it) and time spent waiting between people.

## Claim wording supported by this report
> In a Keystroke-Level Model task analysis of a breach-to-closure workflow,
> the app needed **66.1% fewer user steps** (59 → 20)
> and an estimated **75.2–82.8% less operator time** than a documented
> spreadsheet-and-email process.

## Appendix A: Manual actions
| # | Actor | Action | Type | Characters |
|---|---|---|---|---|
| 1 | Operator | Open the readings logbook spreadsheet | navigate |  |
| 2 | Operator | Find the machine's sheet and the next empty row | lookup |  |
| 3 | Operator | Type the date and time (2026-11-22 09:14) | type | 16 |
| 4 | Operator | Type the machine name (Cooling pump P-101) | type | 18 |
| 5 | Operator | Type the parameter (Temperature) | type | 11 |
| 6 | Operator | Type the reading (95) | type | 2 |
| 7 | Operator | Type own name (Olu Operator) | type | 12 |
| 8 | Operator | Open the threshold reference sheet | navigate |  |
| 9 | Operator | Find the machine and parameter limits | lookup |  |
| 10 | Operator | Compare the reading against the limits | compare |  |
| 11 | Operator | Mark the logbook row as BREACH | type | 6 |
| 12 | Operator | Save the logbook | click |  |
| 13 | Operator | Open the email client and start a new message | navigate |  |
| 14 | Operator | Address it to the plant manager | type | 22 |
| 15 | Operator | Subject: Temperature breach P-101 | type | 32 |
| 16 | Operator | Body: machine, parameter, value, limit, time | type | 78 |
| 17 | Operator | Send the email | click |  |
| 18 | PlantManager | Open the email | navigate |  |
| 19 | PlantManager | Open the work-order register spreadsheet | navigate |  |
| 20 | PlantManager | Find the next work-order number | lookup |  |
| 21 | PlantManager | Type the work-order number | type | 6 |
| 22 | PlantManager | Open the asset register | navigate |  |
| 23 | PlantManager | Find the machine's location and criticality | lookup |  |
| 24 | PlantManager | Switch back to the work-order register | navigate |  |
| 25 | PlantManager | Type the machine name | type | 18 |
| 26 | PlantManager | Type the location (Hall 2) | type | 6 |
| 27 | PlantManager | Type the description (Inspect cooling loop) | type | 20 |
| 28 | PlantManager | Type the priority (HIGH) | type | 4 |
| 29 | PlantManager | Type the alert reference (reading, limit, time) | type | 30 |
| 30 | PlantManager | Type the assignee | type | 12 |
| 31 | PlantManager | Save the register | click |  |
| 32 | PlantManager | Start a new email | navigate |  |
| 33 | PlantManager | Address it to the engineer | type | 22 |
| 34 | PlantManager | Subject: Work order WO-0142 | type | 28 |
| 35 | PlantManager | Body: work-order number, machine, what to do | type | 60 |
| 36 | PlantManager | Send the email | click |  |
| 37 | MaintenanceEngineer | Open the email | navigate |  |
| 38 | MaintenanceEngineer | Open the work-order register | navigate |  |
| 39 | MaintenanceEngineer | Find the work-order row | lookup |  |
| 40 | MaintenanceEngineer | Type the status (CLOSED) | type | 6 |
| 41 | MaintenanceEngineer | Type the resolution notes (Replaced worn bearing) | type | 21 |
| 42 | MaintenanceEngineer | Type the root cause (Bearing wear) | type | 12 |
| 43 | MaintenanceEngineer | Type whether it was a real failure (Yes) | type | 3 |
| 44 | MaintenanceEngineer | Type the failure mode (Tool wear) | type | 9 |
| 45 | MaintenanceEngineer | Type the closure date and time | type | 16 |
| 46 | MaintenanceEngineer | Type own name as closer | type | 12 |
| 47 | MaintenanceEngineer | Save the register | click |  |
| 48 | MaintenanceEngineer | Open the asset register | navigate |  |
| 49 | MaintenanceEngineer | Find the machine's row | lookup |  |
| 50 | MaintenanceEngineer | Type the last-service date | type | 10 |
| 51 | MaintenanceEngineer | Save the asset register | click |  |
| 52 | MaintenanceEngineer | Reply to the plant manager | navigate |  |
| 53 | MaintenanceEngineer | Body: work order closed, root cause | type | 40 |
| 54 | MaintenanceEngineer | Send the email | click |  |
| 55 | PlantManager | Open the reply | navigate |  |
| 56 | PlantManager | Open the readings logbook | navigate |  |
| 57 | PlantManager | Find the BREACH row | lookup |  |
| 58 | PlantManager | Mark it RESOLVED | type | 8 |
| 59 | PlantManager | Save the logbook | click |  |

## Appendix B: App actions (recorded)
| # | Actor | Action | Type | Characters |
|---|---|---|---|---|
| 1 | Operator | Open the app (lands on Readings) | navigate |  |
| 2 | Operator | Choose the machine | select |  |
| 3 | Operator | Choose the parameter | select |  |
| 4 | Operator | Enter the reading | type | 2 |
| 5 | Operator | Save the reading | click |  |
| 6 | PlantManager | Open the app (lands on Alerts) | navigate |  |
| 7 | PlantManager | Open the alert | click |  |
| 8 | PlantManager | Convert to a work order | click |  |
| 9 | PlantManager | Describe the work | type | 20 |
| 10 | PlantManager | Set the priority | select |  |
| 11 | PlantManager | Create the work order | click |  |
| 12 | MaintenanceEngineer | Open the app (lands on Work Orders) | navigate |  |
| 13 | MaintenanceEngineer | Open the work order | click |  |
| 14 | MaintenanceEngineer | Edit the work order | click |  |
| 15 | MaintenanceEngineer | Set status to Closed | select |  |
| 16 | MaintenanceEngineer | Enter resolution notes | type | 21 |
| 17 | MaintenanceEngineer | Enter the root cause | type | 12 |
| 18 | MaintenanceEngineer | Confirm a real failure | select |  |
| 19 | MaintenanceEngineer | Choose the failure mode | select |  |
| 20 | MaintenanceEngineer | Save the closure | click |  |

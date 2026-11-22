# Workflow Baseline: the Manual Process (assumed)

**Status:** an assumption, written for the workflow comparison
(`workflow-comparison.md`). It is **to be validated** by a DigitalT3 lead or
a client maintenance team before any claim is made to that client. The
machine-readable version, which is what gets counted and priced, is
`tools/workflow_benchmark/baseline.json`.

## Why this baseline
Many plants without a CMMS (computerised maintenance management system) run
maintenance on shared spreadsheets and email. This baseline describes that
process for one incident. It is **deliberately favourable to the manual
process**:
- everything happens at a desktop computer, with no paper logbook and no
  walking to a terminal;
- every reply arrives instantly;
- nobody makes a mistake or has to retype anything.

## Tools people use
| Tool | Used for |
|---|---|
| Readings logbook (spreadsheet, one sheet per machine) | Recording readings and marking breaches |
| Threshold reference sheet | Looking up each parameter's limits |
| Email | Hand-offs between operator, plant manager and engineer |
| Work-order register (spreadsheet) | Raising, assigning and closing work orders |
| Asset register (spreadsheet) | Machine details and last-service dates |

## The process, for one breach
1. **Operator.** Opens the logbook, finds the machine's sheet, and types the
   time, machine, parameter, value and their own name. Opens the threshold
   sheet, finds the limits and compares the reading against them by eye. Marks
   the row as BREACH, saves, and emails the plant manager the details.
2. **Plant Manager.** Reads the email and opens the work-order register to
   take the next number. Looks up the machine's details in the asset register,
   then retypes the machine, location, description, priority, a reference to
   the reading, and the assignee. Saves, and emails the engineer.
3. **Maintenance Engineer.** Reads the email and finds the row in the
   work-order register. Types the status, resolution notes, root cause, the
   failure outcome and mode, the closure time and their name. Opens the asset
   register and updates the last-service date. Emails the plant manager.
4. **Plant Manager.** Reads the reply and marks the logbook row RESOLVED.

That is **59 discrete actions**, listed in Appendix A of
`workflow-comparison.md`.

## What the app replaces
- **Threshold check:** done automatically on save.
- **Alert:** created automatically, carrying the machine, parameter, value,
  limits and priority. There is no email to write, and no copying details
  between sheets.
- **Work order:** prefilled from the alert, linked to it, and protected
  against duplicates.
- **Closure:** resolves the alert and updates the service date
  automatically, and records the failure label used for model retraining.

## Validating this baseline
Walk through it with someone who runs a manual maintenance process, and
correct `baseline.json` to match what they really do. Then regenerate:

```bash
python -m tools.workflow_benchmark.report
```

For stronger evidence than a model, time 3 to 5 people doing both flows
against the same scenario, and report those times next to the KLM estimate.

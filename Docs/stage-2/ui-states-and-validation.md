# UI States and Validation

## Shared states

- Loading: show a progress indicator without losing context.
- Empty: explain why no records exist and provide the permitted next action.
- Error: show a human-readable message and correlation ID when available.
- Forbidden: explain the role required for the action.
- Success: confirm the persisted change and resulting state transition.

## Validation

- Equipment criticality: required integer 1–5.
- Parameter: name and unit required; at least one threshold required.
- Reading: value required; timestamp defaults to current time.
- Reading correction: own reading, within five minutes, with reason.
- Work-order update: reject empty updates and edits after closure.
- Work-order closure: require resolution notes, root cause, and at least one parts line.

Threshold equality is a breach. An absent minimum or maximum is displayed as “no limit.”

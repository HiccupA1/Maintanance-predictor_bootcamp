# Predictive Maintenance MVP — Expanded PRD

## Product goal

Provide a simple plant-floor workflow for registering equipment, recording manual health readings, detecting threshold breaches, triaging alerts, and managing maintenance work orders through closure.

## MVP scope

- Equipment registration and criticality management.
- Parameter and threshold configuration.
- Manual reading capture and correction within five minutes.
- Inclusive threshold evaluation and alert lifecycle management.
- Alert-to-work-order conversion.
- Work-order editing, spare-parts capture, and closure.
- Role-aware UI behavior for Admin, PlantManager, Operator, and MaintenanceEngineer.
- REST API with OpenAPI documentation and structured problem responses.

## Explicit non-goals

Automated sensor ingestion, machine-learning failure prediction, native mobile applications, multi-plant governance, and fully specified reporting/notification channels are outside the current MVP.

## Functional requirements

1. Admins can create and edit equipment with criticality from 1 through 5.
2. Plant Managers can configure active parameters with a name, unit, and minimum and/or maximum threshold.
3. Operators can record numeric or non-numeric readings.
4. Numeric readings are evaluated using inclusive boundaries: `value <= minimum` or `value >= maximum`.
5. The system creates one active alert per equipment/parameter breach stream and updates it on repeat breaches.
6. In-range readings clear an active alert.
7. Plant Managers can convert an alert into one work order only.
8. Plant Managers can edit open work orders.
9. Maintenance Engineers close work orders with resolution notes, root cause, and at least one parts line.
10. Closure resolves the source alert and updates the equipment service date.

## Non-functional requirements

The application should provide clear validation, accessible core flows, traceable error responses, structured logging, correlation IDs, and safe configuration through environment variables. Authentication is not enforced in this development stage; the identity shim must not be treated as secure authorization.

# Personas and Role Responsibilities

| Persona | Role | Primary responsibilities |
|---|---|---|
| Admin | `Admin` | Register and edit equipment; maintain criticality. |
| Priya Nair | `PlantManager` | Configure thresholds, triage alerts, create and edit open work orders. |
| Plant operator | `Operator` | Record readings and correct their own readings within five minutes. |
| Alex Rivera | `MaintenanceEngineer` | Perform maintenance, record parts, and close work orders. |
| Reliability lead | Governance role | Review threshold and maintenance patterns; represented through existing MVP capabilities. |

## Authorization principle

The frontend hides or disables unavailable actions, while the backend remains the authoritative enforcement point. The current development identity shim accepts `X-User-Role` and `X-User-Name`; it is not authentication and must not be used as a production security mechanism.

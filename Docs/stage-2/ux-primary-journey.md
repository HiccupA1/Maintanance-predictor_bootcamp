# Primary UX Journey

1. Admin registers equipment and assigns criticality.
2. Plant Manager configures a parameter and one or both thresholds.
3. Operator records a reading from the equipment context.
4. The system evaluates the reading:
   - In range: store it and clear any active alert.
   - Out of range: create or update one active alert and mark equipment at risk.
5. Plant Manager reviews the alert and converts it to a work order.
6. Maintenance Engineer records parts, resolution notes, root cause, and closes the work order.
7. The system resolves the source alert and updates the last service date.

Every screen must show the active equipment/parameter context, provide clear validation, and expose only role-appropriate actions.

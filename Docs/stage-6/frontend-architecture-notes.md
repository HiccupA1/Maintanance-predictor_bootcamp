# Frontend Architecture Notes

The frontend is a React/Vite application with route composition in `src/routes`, feature pages under `src/features`, shared UI controls under `src/components`, API modules under `src/api`, and hooks for server access. `App.tsx` supplies the browser router and delegates screen composition to `AppRoutes`.

Feature boundaries mirror equipment, readings, alerts, and work orders. Role gates improve usability but backend authorization remains authoritative.

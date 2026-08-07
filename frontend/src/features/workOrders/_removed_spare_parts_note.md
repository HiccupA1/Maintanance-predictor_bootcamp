# Removed: Spare parts checklist UI

This repository previously contained a `SparePartsChecklist.tsx` component for a legacy work-order schema that supported spare parts/part lines.

The live Supabase `public.work_orders` schema does **not** support spare-part line items, and the component was removed during schema reconciliation.

If you are seeing references to `SparePartsChecklist.tsx` in generated reports/logs, they are from historical diffs or tooling output, not from the current codebase.

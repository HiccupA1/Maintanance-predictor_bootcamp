# API Test Matrix

| Area | Positive | Negative / boundary |
|---|---|---|
| Health | `/health`, `/health/db` return 200 | Database unavailable returns readiness failure |
| Equipment | Create, fetch, update | Missing fields; criticality below 1 or above 5 |
| Parameters | Create with one/both thresholds | No thresholds; inactive behavior |
| Readings | Numeric and non-numeric values | Correction after five minutes; missing reason |
| Alerts | Create, update, clear | Duplicate active alert |
| Work orders | Convert, list, fetch, update, close | Unknown alert; duplicate conversion; closed update |
| Pagination | Supported page sizes including 200 | Zero, negative, and 201 |
| Errors | Problem envelope and correlation ID | No generic untraceable failures |

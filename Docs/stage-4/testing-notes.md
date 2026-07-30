# Backend Testing Notes

The repository includes health and work-order tests using an in-memory SQLite setup. Existing QA evidence records successful health checks, work-order create/update/fetch scenarios, structured errors, and most contract cases.

The documented QA retest found a valid `page_size=200` request returning HTTP 500 while `page_size=201` correctly returned HTTP 422. This remains a release-blocking investigation until reproduced, root-caused, fixed, and regression-tested.

# Backend Test Strategy

Test layers include schema/unit tests, service and repository integration tests, API contract tests, migration checks, and smoke tests. Coverage must include happy paths, invalid input, boundary values, duplicate creation, state transitions, role restrictions, database failures, and structured error responses.

Release gating requires no open P0/P1 defects and successful API contract execution against the supported database configuration.

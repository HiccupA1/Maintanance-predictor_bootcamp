# Security Review (WP6)

**Date:** 2026-11-20
**Scope:** FastAPI backend, Postgres/Supabase schema, ML model artifacts,
React frontend, CI/CD and the container image, as of `release/wp6`.
**Method:** a threat model of the trust boundaries, a walk through the
OWASP API Security Top 10 (2023), automated scanning (bandit, pip-audit,
npm audit, Trivy) and a review of the code. Every control listed is backed by
a test or a CI gate.

## Architecture and trust boundaries

```
Browser (React, Vercel) --(Supabase Auth: email/password)--> Supabase Auth
   |  Bearer JWT (RS256/ES256)
   v
FastAPI API (container) --(postgres role, BYPASSRLS)--> Supabase Postgres
   |                                                   (RLS on, no policies)
   +-- model store (joblib artifacts, SHA-256 pinned in model_versions)
```

| Boundary | Threat | Control | Evidence |
|---|---|---|---|
| Browser → API | Forged or expired token | JWKS signature check, RS256/ES256 only, `exp` enforced, optional `aud`. HS256 and `alg=none` are rejected | `tests/test_auth_jwt.py` (11) |
| Browser → API | Privilege escalation | Roles come only from `user_profiles`, never from JWT claims. Every route is guarded by one central policy | `app/core/rbac.py`, `tests/test_authorization.py` (128+) |
| Browser → Supabase Data API | Bypassing the API with the public key | RLS on and no policies; `anon` and `authenticated` have no privileges (D17) | `tests/sql/assert_no_data_api_access.sql` (CI) |
| API → database | Lock-out from a misconfigured role | Migration 0004 aborts unless the API role bypasses RLS | local and CI test |
| Model store → API | Malicious artifact (joblib can execute code) | Loaded only from `MODEL_STORE_DIR`, after SHA-256 verification against the registry, with path-escape protection | `tests/test_scoring.py` |
| Config → API | Dev shortcuts left on in production | `APP_ENV` defaults to production; the identity shim is refused outside dev; docs are off in production; JWKS must be https outside dev/test | `tests/test_me.py`, `tests/test_security_hardening.py` |
| Supply chain | Vulnerable dependencies | pip-audit (any finding), npm audit (prod ≥ high, all = critical), Trivy on the image (CRITICAL/HIGH with fixes), Dependabot | CI `security` and `docker` jobs |

## OWASP API Security Top 10 (2023)

| # | Risk | Status | Notes |
|---|---|---|---|
| API1 | Broken object-level authorization | **Accepted (single tenant)** | There is one plant and every user of a role may see all of its records, so there is no per-object ownership to enforce. If multi-site arrives, add a site or tenant key and object-level checks |
| API2 | Broken authentication | **Mitigated** | See above. Error details no longer echo the JWKS URL or internal causes |
| API3 | Broken object-property-level authorization | **Mitigated** | Request schemas are explicit. `closed_by` and `entered_by` are set server-side from the verified user; failure labels can only be set at closure |
| API4 | Unrestricted resource consumption | **Partially mitigated** | Pagination caps work orders at 200. Input lengths are bounded. The DB pool fails fast. **Gaps:** no rate limiting; `/alerts` and readings history are unpaginated. See R-1 and R-2 |
| API5 | Broken function-level authorization | **Mitigated** | Every route is in the policy table, and a test fails if any route lacks an entry |
| API6 | Unrestricted access to sensitive business flows | **Mitigated** | One work order per alert (unique index). Model promotion is Admin-only, verifies the artifact first, and records who made the change |
| API7 | Server-side request forgery | **Mitigated** | The only outbound fetches are to a configured JWKS URL (https only in production) and a constant dataset URL, verified by checksum |
| API8 | Security misconfiguration | **Mitigated** | Generic 500s; `nosniff`, `no-referrer` and `no-store` headers; explicit CORS origins; non-root container; docs off in production |
| API9 | Improper inventory management | **Mitigated** | One versioned `/v1` surface. The OpenAPI schema is the route inventory, checked against the policy table in CI |
| API10 | Unsafe consumption of APIs | **Mitigated** | Only the Supabase JWKS is consumed. It is parsed defensively and cached |

## Findings fixed during this review

| ID | Finding | Fix |
|---|---|---|
| S-1 | bandit B310: the JWKS fetch accepted `file://` and `http://` | Scheme allow-list: https only outside dev/test |
| S-2 | 401 details revealed the JWKS URL, key ids and exception text | Generic client messages; details go to server logs |
| S-3 | Interactive docs and the OpenAPI schema were public in production | Off by default in production (`API_DOCS_ENABLED` overrides) |
| S-4 | No baseline security headers | Added to every response |
| S-5 | Free-text inputs were unbounded | `max_length` on every free-text field |

These add to the fixes in earlier work packages:
- **D7, D14:** auth guard and identity shim.
- **D12, D13:** dependency vulnerabilities.
- **D16:** personal data in the repository.
- **D17:** Data API exposure.
- **Open redirect after login** (`safeNextPath`).

## Scan results (this build)

| Tool | Result |
|---|---|
| bandit 1.9.4 (`app ml tools scripts`, medium+) | 0 findings (two justified `nosec B310` annotations) |
| pip-audit | 0 known vulnerabilities |
| npm audit | 0 critical. Remaining findings are risk-accepted in `risk-register.md` (RA-1, RA-2) |
| Trivy (image, CRITICAL/HIGH with fixes) | CI job `Docker image`. See its log for this build |

## Residual risks (accepted, tracked)

| ID | Risk | Rating | Mitigation and owner |
|---|---|---|---|
| R-1 | No API rate limiting | Medium | Enforce at the platform edge (API gateway or ingress rate limits) when hosting is chosen (ADR-0008). Supabase Auth already rate-limits sign-in |
| R-2 | `GET /alerts` and readings history are unpaginated | Medium (grows with data) | Add pagination before history reaches thousands of rows per list (performance report) |
| R-3 | The email address is still in git history (D16) | Low–medium (privacy) | Rewriting history before client handover is the owner's decision |
| R-4 | There is no audit-log table. Stage changes and closures record who and when on the row only | Low | Add an append-only audit table if the client requires full history |
| R-5 | React Router 6 advisories (RA-2) and picomatch (RA-1) | Low | Review dates are in `risk-register.md`; D15 tracks the v7 migration |
| R-6 | The model store is the container filesystem, not Supabase Storage | Low | Mount a persistent volume. The Storage adapter (ADR-0007) is planned |

## Before go-live (owner actions)

1. Store secrets (`DATABASE_URL`, `SUPABASE_*`) only in the platform's secret
   store. The image contains no `.env` (`.dockerignore`).
2. Set `CORS_ORIGINS` to the production frontend origin only.
3. Apply migrations 0001 (stamp) to 0004 on staging, then production. Check
   that `/rest/v1/equipment` with a user's token returns no rows.
4. Configure edge rate limiting (R-1).
5. Enable branch protection requiring **CI OK** (`Docs/runbooks/ci.md`).

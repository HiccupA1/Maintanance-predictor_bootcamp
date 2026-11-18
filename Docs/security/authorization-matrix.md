# API Authorization Matrix

The API enforces this matrix on every request. The policy lives in one place,
`app/core/rbac.py` (`POLICY`). `tests/test_authorization.py` checks every route
against it:

- **No credentials:** 401.
- **Role outside the policy:** 403.
- **Role inside the policy:** passes authorization.
- **Completeness:** the test fails if a route is added without an entry, so a
  new route cannot ship without someone deciding who may call it.

Roles come only from `user_profiles.role`, which only Admins can change.
Roles in JWT claims are never trusted. The frontend's role checks
(`frontend/src/utils/rbac.ts`) only hide controls the user can't use; the API
is what enforces access.

**Key:** ✅ allowed · — 403

| Permission | Routes | Admin | Plant Manager | Operator | Maint. Engineer | Source |
|---|---|:-:|:-:|:-:|:-:|---|
| `equipment:read` | `GET /equipment`, `GET /equipment/{id}` | ✅ | ✅ | ✅ | ✅ | Operators select equipment when recording readings |
| `equipment:write` | `POST /equipment`, `PUT /equipment/{id}` | ✅ | — | — | — | PRD FR1 |
| `equipment:delete` | `DELETE /equipment/{id}` | ✅ | — | — | — | Existing guard |
| `parameter:read` | `GET /equipment/{id}/parameters` | ✅ | ✅ | ✅ | ✅ | As equipment:read |
| `parameter:write` | `POST /equipment/{id}/parameters`, `PUT /parameters/{id}` | — | ✅ | — | — | PRD FR2 |
| `reading:read` | `GET /equipment/{id}/parameters/{pid}/readings` | ✅ | ✅ | ✅ | ✅ | All personas review readings |
| `reading:write` | `POST /readings`, `PUT /readings/{id}`, `DELETE /readings/{id}` | — | — | ✅ | — | PRD FR3 |
| `alert:read` | `GET /alerts`, `GET /alerts/{id}` | ✅ | ✅ | — | ✅ | Frontend `operationalRoles` |
| `alert:delete` | `DELETE /alerts/{id}` | — | ✅ | — | — | Existing guard |
| `work_order:read` | `GET /work-orders`, `GET /work-orders/{id}` | ✅ | ✅ | — | ✅ | Frontend `operationalRoles` |
| `work_order:create` | `POST /work-orders` | — | ✅ | — | — | PRD FR7 |
| `work_order:update` | `PUT /work-orders/{id}` | — | ✅ | — | ✅ | PRD FR8 (edit) and FR9 (close) |
| `work_order:delete` | `DELETE /work-orders/{id}` | — | ✅ | — | ✅ | Existing guard |
| `user:admin` | `/admin/users` (list, create, update, delete, role change) | ✅ | — | — | — | Admin-only |

All paths are under `/v1`.

## Public and identity routes

| Route | Access |
|---|---|
| `GET /v1/health`, `GET /v1/health/db` | Public (liveness and readiness probes). |
| `GET /v1/me` | Needs a valid Supabase token, which returns the caller's own profile. Without a token it returns 401, unless the dev identity shim is on. |

## Direct database access (Supabase Data API)

The API is the **only** way to reach data. The browser uses Supabase for
sign-in only. From migration `0004_close_data_api_access` (D17):

- Every application table has RLS enabled and **no policies**.
- The `anon` and `authenticated` roles have no privileges on any of them.

So a signed-in user holding the public publishable key cannot read or write
anything through `/rest/v1`. CI enforces this with
`tests/sql/assert_no_data_api_access.sql`.

**Rule for new tables:** enable RLS and add no policies. If a feature
genuinely needs browser-direct access (for example Supabase Realtime), it
needs a security review and an entry in this document first.

## Development identity shim

`ENABLE_DEV_IDENTITY_SHIM` lets `GET /v1/me` accept `X-User-Role` and
`X-User-Name` headers, so you can work on the UI locally without Supabase.

- It is off by default.
- The API refuses to start if the shim is on and `APP_ENV` is not `dev`.
  `APP_ENV` defaults to `production`.
- It applies to `/me` only. Every route in the matrix ignores it.

## Other rules

- **Reading author:** `entered_by` and `modified_by` come from the verified
  profile (display name, then email, then user id). A client-sent
  `X-User-Name` header is ignored.
- **Unknown roles:** a profile whose role is not one of the four above is
  denied (403) on every route in the matrix.

## Open questions for the client

1. **Admin and work orders.** Admins can view work orders and alerts, but
   per the PRD they cannot create, edit or delete them. The frontend still
   lets Admins open the work-order edit page, where saving now returns 403.
   Confirm whether Admins should get `work_order:update`. If not, the
   frontend route should be restricted to match.
2. **Admin and parameters.** PRD FR2 gives parameter configuration to Plant
   Managers only, so Admins can create equipment but not its thresholds.
   Confirm this is intended.
3. **Alert and work-order deletion.** These guards predate this matrix and
   are not in the PRD. Confirm the roles, or remove the operations in favour
   of status changes, which keep the audit trail.

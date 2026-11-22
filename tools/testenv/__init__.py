"""Shared test-environment tooling for load tests and browser E2E tests.

Tokens are signed with a locally generated key and verified by the API's real
JWKS code path (``SUPABASE_JWKS_URL=file://...`` under ``APP_ENV=test``).
No authentication code is bypassed.
"""

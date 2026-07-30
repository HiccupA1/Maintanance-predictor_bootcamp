# ADR-0002 — Development Identity Shim

- **Status:** Temporary / development only
- **Decision:** Expose `GET /v1/me` with optional role/name headers during staged development.
- **Context:** Frontend role-gating needs deterministic personas before production identity integration exists.
- **Consequences:** Local demos are simple, but the shim provides no authentication or secure authorization and must be replaced before production.

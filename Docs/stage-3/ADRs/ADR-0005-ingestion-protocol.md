# ADR-0005 — Ingestion Protocol and Device Authentication

- **Status:** Proposed (CR-001)
- **Decision:**
  - The platform exposes one ingestion interface, `POST /v1/ingest/telemetry`. It is HTTPS,
    takes JSON batches of 1–500 points, and authenticates the device with an `X-Device-Key`
    header.
  - Plant-side protocols (MQTT, OPC-UA, Modbus, historian exports) are bridged **at the
    edge**. A gateway (for example Telegraf, Node-RED, Kepware or an EMQX rule) buffers
    locally and posts batches to this API.
  - The cloud platform does not run a protocol broker.

## Context

- The client's plant protocols are not yet known (PRD addendum, open question 2). Industrial
  sites commonly run OPC-UA or Modbus on the OT network, with MQTT for IIoT devices. Plant
  networks are usually segmented and allow outbound HTTPS only.
- Devices or gateways must not hold user credentials or Supabase service keys.

## Device authentication

- An Admin creates a device bound to one equipment record. A random 256-bit key is shown
  **once**, and only its SHA-256 hash is stored. Key comparison is constant-time.
- Rotating a key invalidates it immediately. Disabling a device rejects all of its requests.
  Both events are audit-logged (FR12).
- A key authorises writes only for parameters of its bound equipment. Keys cannot read data.
- Rate limiting is applied per device. Exceeding it returns `429` with `Retry-After`, and the
  gateway buffers.

## Payload contract

- Each point carries `parameter_id` (or `parameter_name`, unique per equipment), a numeric
  `value`, `ts` (RFC 3339, UTC), and an `ingest_id` that is unique per device.
- `ingest_id` makes retries safe. Gateways can retry on any network failure without creating
  duplicates (FR14).
- Points with a `ts` more than 5 minutes in the future, or older than the retention window,
  are rejected per point. The rest of the batch is still accepted, and per-point results are
  returned.

## Alternatives considered

| Option | Why not chosen now |
|---|---|
| Cloud MQTT broker (EMQX, HiveMQ, AWS IoT Core) | Adds a broker to operate and secure. Plants usually still need an edge bridge for OPC-UA or Modbus anyway. Reconsider if devices connect directly over cellular, or if fleet size grows past roughly 10k devices. |
| Direct OPC-UA from cloud to plant | Needs inbound connectivity into the OT network, which most plant security policies forbid. |
| mTLS client certificates | Stronger, but needs a PKI and certificate lifecycle tooling the client has not specified. API keys plus TLS are the agreed baseline, with mTLS as an upgrade. |
| Supabase user JWTs for devices | Devices are not users. Expiry and refresh complicate headless clients, and role semantics do not fit. |

## Consequences

- **Positive:**
  - The interface is protocol-agnostic, easy to test, and works through plant firewalls.
  - The edge simulator exercises exactly the production path.
- **Negative:**
  - Edge gateway configuration is the client's or their integrator's responsibility, and is
    out of scope in CR-001.
  - API keys are bearer secrets, so their safety depends on gateway hardening and rotation
    discipline.

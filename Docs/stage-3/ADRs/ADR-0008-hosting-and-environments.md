# ADR-0008 — Hosting, Environments and Delivery

- **Status:** Proposed (CR-001). The cloud provider is pending client confirmation.
- **Decision:**
  - **Frontend:** stays on Vercel (existing `vercel.json`).
  - **Data, auth and storage:** stay on Supabase (Postgres, Auth, Storage, Queues).
  - **API and worker:** built as **one Docker image** with two entrypoints:
    `uvicorn app.main:app` and `python -m app.worker`.
    - The image is published to GitHub Container Registry on every merge to `main`.
    - It is deployed as two services on a **managed container platform in the client's
      cloud**: Azure Container Apps if the client is on Azure, or AWS ECS Fargate if on AWS.
    - Render is acceptable as an interim staging host.
  - **Environments:** `dev` (local, `docker compose`), `staging`, and `prod`. Each has its
    own Supabase project and secrets.
    - The identity shim (ADR-0002) and `/docs` UI exposure are controlled by `ENV`. The shim
      is enabled only in `dev`.
  - **Delivery:**
    - `main` is protected: changes arrive by pull request, and CI must pass.
    - CI covers lint, format, unit tests on SQLite, migration and integration tests against
      a Postgres service container, `pip-audit` and `npm audit` at high/critical, and the
      frontend typecheck, lint and tests.
    - Merges to `main` deploy to staging. Production deploys come from tagged releases, with
      Alembic migrations applied as a gated release step.

## Context

- The repository has hosting configuration only for the frontend. The backend has no
  deployment definition.
- The worker must run continuously, not as a request-scoped function. That rules out
  serverless platforms with short execution limits for the worker.
- The client's cloud provider is not yet known.

## Alternatives considered

| Option | Why not chosen |
|---|---|
| Kubernetes (AKS, EKS) | Operational overhead is unjustified for two services. Managed container apps give autoscaling and revisions without cluster operations. |
| Serverless functions (Vercel, Lambda) for the API | Workable for the API, but not for the long-running worker. Splitting runtimes increases complexity. |
| VM with systemd | Manual patching and scaling, and no immutable deploys. |

## Consequences

- **Positive:**
  - Portable images that run the same locally, in CI and in each cloud.
  - The worker scales independently of the API.
  - Rollback means redeploying the previous image tag.
- **Negative:**
  - Three platforms to manage (Vercel, Supabase, the container host).
  - Network latency between the container host and Supabase must be minimised by using the
    same region.

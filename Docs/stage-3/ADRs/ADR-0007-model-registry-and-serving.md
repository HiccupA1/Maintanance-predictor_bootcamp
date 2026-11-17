# ADR-0007 — Model Registry and Serving

- **Status:** Proposed (CR-001)
- **Decision:**
  - **Training:** pipelines live in `ml/` with their own optional dependency extra. Runs are
    tracked with MLflow using a local or file artifact store. Each run produces a model
    artifact, `metrics.json` and a model card.
  - **Registry:** a promoted artifact is uploaded to a private Supabase Storage bucket
    (`models/`). It is registered in a `model_versions` table with: version, asset_class,
    kind (`failure_risk` or `anomaly`), stage (`shadow`, `active` or `retired`), feature
    list, operating threshold, metrics, artifact SHA-256, training data checksum,
    `created_by`, and the stage history.
  - **Serving:** models run **in-process in the worker** (ADR-0004), not behind a separate
    inference service.
    - The worker loads every `shadow` and `active` version at start-up, verifies the
      checksum, and polls `model_versions` every 60 s to hot-reload on stage changes.
    - Feature construction is imported from the same `ml/features/` module used in training,
      so there is no train/serve skew.

## Context

- Inference is cheap: a tree ensemble over fewer than 20 features takes microseconds per row.
  At ≈ 300 points/s and one score per batch, a separate model server adds network hops and
  ops burden for no gain.
- The client must be able to see which model produced every score, and roll back without a
  deploy (FR19–FR21).

## Alternatives considered

| Option | Why not chosen now |
|---|---|
| Hosted MLflow tracking server and registry | Another service to secure and run. File-backed tracking is enough for a small team. Upgrade when several data scientists collaborate. |
| Cloud ML platforms (SageMaker, Azure ML, Vertex) | Strong, but they lock in a cloud before the client has chosen one (ADR-0008). They are the natural upgrade once the hosting cloud is fixed. |
| Separate inference microservice (BentoML, FastAPI) | Justified for GPU models or many consumers. Neither applies here. |
| Artifacts baked into the Docker image | Rollback would need a redeploy, and stage changes could not happen at runtime. |

## Consequences

- **Positive:**
  - Every score is traceable to a version and checksum.
  - Rollback is a database update.
  - There are no extra services.
- **Negative:**
  - The worker image carries the ML runtime dependencies (scikit-learn, numpy).
  - Artifacts are pickled (joblib), so loading is restricted to checksum-verified files from
    the private bucket, and the bucket is writable only by the promotion script's service
    role.

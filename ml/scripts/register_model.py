"""Register a trained model version in the registry, in the shadow stage.

    python -m ml.scripts.register_model ml/artifacts/ai4i-v1

1. Copies ``model.joblib`` into ``MODEL_STORE_DIR`` as ``<version>.joblib``.
2. Records the version, asset class, threshold, feature list, metrics and
   the artifact's SHA-256 in ``model_versions``, with stage ``shadow``.

New versions always start in shadow: they are scored and stored but raise no
alerts. Promotion to active is a separate, audited Admin action
(``POST /v1/models/{id}/stage``) after shadow evaluation (WP5).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import joblib
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.ml import ModelVersion
from app.services.model_registry import sha256_file


def register(artifact_dir: Path) -> ModelVersion:
    bundle = joblib.load(artifact_dir / "model.joblib")
    metrics_path = artifact_dir / "metrics.json"
    metrics = (
        json.loads(metrics_path.read_text()) if metrics_path.exists() else None
    )
    version = bundle["version"]

    store = Path(get_settings().model_store_dir)
    store.mkdir(parents=True, exist_ok=True)
    target = store / f"{version}.joblib"
    shutil.copyfile(artifact_dir / "model.joblib", target)

    db = SessionLocal()
    try:
        if db.execute(
            select(ModelVersion).where(ModelVersion.version == version)
        ).scalar_one_or_none():
            raise SystemExit(f"version {version} is already registered")
        row = ModelVersion(
            version=version,
            kind=bundle.get("kind", "failure_risk"),
            asset_class=bundle["asset_class"],
            stage="shadow",
            threshold=float(bundle["threshold"]),
            features=list(bundle["features"]),
            metrics=(
                {
                    "test": metrics.get("test"),
                    "operating_points": metrics.get("operating_points"),
                    "selected_model": metrics.get("selected_model"),
                    "dataset_sha256": metrics.get("dataset", {}).get("sha256"),
                    "reference": metrics.get("reference"),
                    "comparison": metrics.get("comparison"),
                }
                if metrics
                else None
            ),
            artifact_uri=target.name,
            artifact_sha256=sha256_file(target),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("artifact_dir", type=Path)
    row = register(parser.parse_args().artifact_dir)
    print(
        f"registered {row.version} ({row.asset_class}) as {row.stage}: {row.id}"
    )


if __name__ == "__main__":
    sys.exit(main())

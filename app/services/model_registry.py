"""Load registered model artifacts safely (ADR-0007).

Artifacts are joblib files, and loading a joblib file can execute code.
Every artifact is therefore checked against the SHA-256 recorded in
``model_versions`` before it is deserialised, and only files inside the
configured store directory are read.

Storage is currently a directory (``MODEL_STORE_DIR``). The Supabase
Storage adapter (ADR-0007) replaces ``_resolve`` without changing callers.
"""

from __future__ import annotations

import hashlib
import logging
import threading
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.models.ml import ModelVersion

logger = logging.getLogger(__name__)

# Cache keyed by (version id, sha256): a re-registered artifact never serves
# a stale model, and stage changes need no reload.
_CACHE: dict[tuple[str, str], dict[str, Any]] = {}
_LOCK = threading.Lock()


class ArtifactError(RuntimeError):
    """The artifact is missing, outside the store, or fails verification."""


def _resolve(uri: str) -> Path:
    store = Path(get_settings().model_store_dir).resolve()
    path = (store / uri).resolve()
    if store not in path.parents:
        raise ArtifactError(f"artifact path escapes the model store: {uri}")
    if not path.is_file():
        raise ArtifactError(f"artifact not found: {uri}")
    return path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(version: ModelVersion) -> dict[str, Any]:
    """Return the artifact bundle (model, features, threshold, ...)."""
    key = (str(version.id), version.artifact_sha256)
    with _LOCK:
        if key in _CACHE:
            return _CACHE[key]
        path = _resolve(version.artifact_uri)
        actual = sha256_file(path)
        if actual != version.artifact_sha256:
            raise ArtifactError(
                f"checksum mismatch for {version.version}: refusing to load"
            )
        import joblib  # deferred: ml extra

        bundle = joblib.load(path)
        if bundle.get("features") != list(version.features):
            raise ArtifactError(
                f"{version.version}: artifact features differ from registry"
            )
        _CACHE[key] = bundle
        logger.info("loaded model %s (%s)", version.version, version.stage)
        return bundle


def clear_cache() -> None:
    with _LOCK:
        _CACHE.clear()

"""Seed a disposable database for load or E2E tests.

    DATABASE_URL=... MODEL_STORE_DIR=... python -m tools.testenv.seed OUT_DIR [--machines N] [--e2e]

- Writes ``jwks.json``, ``tokens.json`` and ``sessions.json`` to OUT_DIR.
  Start the API with ``SUPABASE_JWKS_URL=file:///OUT_DIR/jwks.json`` and
  ``APP_ENV=test``.
- Creates one user profile per role.
- Registers ``ml/artifacts/ai4i-v1`` in **shadow**. Train it first with
  ``python -m ml.pipelines.train_ai4i --version ai4i-v1``.
- ``--machines N``: creates N mapped machines and writes ``targets.json``
  (for the load test).

Run it only against a disposable database.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import select

from app.core.model_inputs import FEATURE_KEYS
from app.db.session import SessionLocal
from app.models.equipment import Equipment, Parameter
from app.models.ml import ModelVersion
from app.models.user_profile import UserProfile
from tools.testenv import keys

MODEL_ARTIFACT = Path("ml/artifacts/ai4i-v1")


def seed_users(db) -> None:
    for role in keys.ROLES:
        sub = keys.subject(role)
        if not db.execute(
            select(UserProfile).where(UserProfile.supabase_user_id == sub)
        ).scalar_one_or_none():
            db.add(
                UserProfile(
                    supabase_user_id=sub,
                    email=keys.email(role),
                    display_name=keys.display_name(role),
                    role=role,
                )
            )
    db.commit()


def seed_machines(db, count: int, prefix: str = "LT") -> list[dict]:
    targets = []
    for i in range(count):
        business_id = f"{prefix}-{i:03d}"
        eq = db.execute(
            select(Equipment).where(Equipment.equipment_id == business_id)
        ).scalar_one_or_none()
        if eq is None:
            eq = Equipment(
                equipment_id=business_id,
                name=f"Load mill {i}",
                location="Load plant",
                type="Mill",
                criticality=1 + i % 5,
                asset_class="ai4i_milling",
            )
            db.add(eq)
            db.flush()
            for key_name in FEATURE_KEYS:
                db.add(
                    Parameter(
                        equipment_id=eq.id,
                        name=key_name,
                        unit="-",
                        max_threshold=1e9,
                        feature_key=key_name,
                    )
                )
            db.flush()
        params = dict(
            db.execute(
                select(Parameter.feature_key, Parameter.id).where(
                    Parameter.equipment_id == eq.id
                )
            ).all()
        )
        targets.append({"equipment_id": business_id, "parameters": params})
    db.commit()
    return targets


def register_model(db) -> None:
    if db.execute(
        select(ModelVersion).where(ModelVersion.version == "ai4i-v1")
    ).scalar_one_or_none():
        return
    if not (MODEL_ARTIFACT / "model.joblib").exists():
        raise SystemExit(
            "ml/artifacts/ai4i-v1 not found: run "
            "`python -m ml.pipelines.train_ai4i --version ai4i-v1` first"
        )
    from ml.scripts.register_model import register

    register(MODEL_ARTIFACT)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out", type=Path)
    parser.add_argument("--machines", type=int, default=0)
    parser.add_argument("--e2e", action="store_true", help="E2E profile")
    args = parser.parse_args()

    key = keys.write_keys(args.out)
    keys.write_credentials(key, args.out)
    db = SessionLocal()
    try:
        seed_users(db)
        if args.machines:
            targets = seed_machines(db, args.machines)
            (args.out / "targets.json").write_text(json.dumps(targets))
    finally:
        db.close()
    db = SessionLocal()
    try:
        register_model(db)
    finally:
        db.close()
    print(f"SUPABASE_JWKS_URL={(args.out / 'jwks.json').resolve().as_uri()}")


if __name__ == "__main__":
    main()

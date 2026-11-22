"""Prepare a load-test environment: signing key, JWKS, tokens and seed data.

    DATABASE_URL=... MODEL_STORE_DIR=... python -m tools.loadtest.setup OUT_DIR

Writes to OUT_DIR:
- ``jwks.json``: the public key. Start the API with
  ``SUPABASE_JWKS_URL=file:///OUT_DIR/jwks.json``, so tokens are verified by
  the real JWT code path and no auth code is bypassed.
- ``tokens.json``: one 8-hour token per role.
- ``targets.json``: the seeded equipment and parameter ids.

It seeds 50 machines, each with the 6 mapped model parameters, registers
``ml/artifacts/ai4i-v1`` in shadow (so every reading POST also runs the
model), and creates one user profile per role. **Run it against a disposable
database only.**
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from pathlib import Path

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import select

from app.core.model_inputs import FEATURE_KEYS
from app.db.session import SessionLocal
from app.models.equipment import Equipment, Parameter
from app.models.ml import ModelVersion
from app.models.user_profile import UserProfile

ROLES = ("Admin", "PlantManager", "Operator", "MaintenanceEngineer")
KID = "loadtest-key"
MACHINES = 50


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    (out / "jwks.json").write_text(
        json.dumps(
            {"keys": [{**jwk, "kid": KID, "alg": "RS256", "use": "sig"}]}
        )
    )

    db = SessionLocal()
    tokens = {}
    now = int(time.time())
    for role in ROLES:
        sub = str(uuid.uuid5(uuid.NAMESPACE_URL, f"loadtest/{role}"))
        if not db.execute(
            select(UserProfile).where(UserProfile.supabase_user_id == sub)
        ).scalar_one_or_none():
            db.add(
                UserProfile(
                    supabase_user_id=sub,
                    email=f"{role.lower()}@loadtest.invalid",
                    display_name=f"Load {role}",
                    role=role,
                )
            )
        tokens[role] = jwt.encode(
            {
                "sub": sub,
                "aud": "authenticated",
                "iat": now,
                "exp": now + 8 * 3600,
            },
            key,
            algorithm="RS256",
            headers={"kid": KID},
        )

    targets = []
    for i in range(MACHINES):
        business_id = f"LT-{i:03d}"
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

    if not db.execute(
        select(ModelVersion).where(ModelVersion.version == "ai4i-v1")
    ).scalar_one_or_none():
        db.close()
        from ml.scripts.register_model import register

        register(Path("ml/artifacts/ai4i-v1"))
    else:
        db.close()

    (out / "tokens.json").write_text(json.dumps(tokens))
    (out / "targets.json").write_text(json.dumps(targets))
    print(f"SUPABASE_JWKS_URL={(out / 'jwks.json').resolve().as_uri()}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))

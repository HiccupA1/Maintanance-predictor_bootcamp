"""Prepare a load-test environment (kept for compatibility).

    DATABASE_URL=... MODEL_STORE_DIR=... python -m tools.loadtest.setup OUT_DIR

Equivalent to ``python -m tools.testenv.seed OUT_DIR --machines 50``. It writes
the signing key's JWKS, tokens for each role and ``targets.json``, seeds 50
mapped machines and one user per role, and registers ``ai4i-v1`` in shadow.
Run it only against a disposable database.
"""

from __future__ import annotations

import sys

from tools.testenv import seed

if __name__ == "__main__":
    sys.argv = [sys.argv[0], sys.argv[1], "--machines", "50"]
    seed.main()

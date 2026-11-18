"""Pinned settings for reproducible training runs."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "ml" / "data" / "raw"
ARTIFACTS_DIR = ROOT / "ml" / "artifacts"

SEED = 42
# Stratified split fractions (train / validation / test).
VAL_FRACTION = 0.2
TEST_FRACTION = 0.2

# Operating point: the threshold is chosen on validation as the most precise
# threshold that still catches at least this share of failures. The value is
# a placeholder until the client agrees one (CR-001 / ADR-0006).
RECALL_FLOOR = 0.90

# Relative cost of errors for the cost-weighted metric: a missed failure
# (unplanned downtime) is assumed to cost 10x a false alarm (an inspection).
COST_FALSE_NEGATIVE = 10.0
COST_FALSE_POSITIVE = 1.0

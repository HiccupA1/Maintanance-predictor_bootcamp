"""Feature construction shared by training and online scoring.

The scoring worker (WP4) maps an asset's latest sensor values onto
``RAW_INPUTS`` (per asset class) and calls :func:`build_features`. Training
calls the same function, so the two cannot drift apart.
"""

from __future__ import annotations

import math

import pandas as pd

# Canonical raw inputs (snake_case), and the AI4I source column for each.
RAW_INPUTS = {
    "product_type": "Type",
    "air_temp_k": "Air temperature [K]",
    "process_temp_k": "Process temperature [K]",
    "rotational_speed_rpm": "Rotational speed [rpm]",
    "torque_nm": "Torque [Nm]",
    "tool_wear_min": "Tool wear [min]",
}

PRODUCT_TYPES = ("L", "M", "H")

FEATURES = [
    "air_temp_k",
    "process_temp_k",
    "rotational_speed_rpm",
    "torque_nm",
    "tool_wear_min",
    # Engineered, physically motivated features.
    "temp_diff_k",  # heat dissipation headroom
    "power_w",  # mechanical power = torque * angular speed
    "strain_nm_min",  # tool wear x torque (overstrain proxy)
    "type_L",
    "type_M",
    "type_H",
]

# Columns that must never be model inputs: identifiers and label components.
FORBIDDEN_INPUTS = {
    "UDI",
    "Product ID",
    "Machine failure",
    "TWF",
    "HDF",
    "PWF",
    "OSF",
    "RNF",
}


def from_ai4i(df: pd.DataFrame) -> pd.DataFrame:
    """Rename AI4I columns to the canonical raw input names."""
    return df[list(RAW_INPUTS.values())].rename(
        columns={v: k for k, v in RAW_INPUTS.items()}
    )


def build_features(raw: pd.DataFrame) -> pd.DataFrame:
    """Return the model feature matrix, columns in ``FEATURES`` order.

    ``raw`` must contain the ``RAW_INPUTS`` keys. Missing values raise rather
    than being imputed: equipment without a complete feature set is "not
    scorable" (ADR-0006), not scored on guesses.
    """
    missing = set(RAW_INPUTS) - set(raw.columns)
    if missing:
        raise ValueError(f"missing raw inputs: {sorted(missing)}")
    if raw[list(RAW_INPUTS)].isna().any().any():
        raise ValueError("raw inputs contain nulls; asset is not scorable")
    unknown = set(raw["product_type"]) - set(PRODUCT_TYPES)
    if unknown:
        raise ValueError(f"unknown product_type values: {sorted(unknown)}")

    out = pd.DataFrame(index=raw.index)
    for name in (
        "air_temp_k",
        "process_temp_k",
        "rotational_speed_rpm",
        "torque_nm",
        "tool_wear_min",
    ):
        out[name] = raw[name].astype("float64")
    out["temp_diff_k"] = out["process_temp_k"] - out["air_temp_k"]
    out["power_w"] = (
        out["torque_nm"] * out["rotational_speed_rpm"] * (2 * math.pi / 60)
    )
    out["strain_nm_min"] = out["tool_wear_min"] * out["torque_nm"]
    for product_type in PRODUCT_TYPES:
        out[f"type_{product_type}"] = (
            raw["product_type"] == product_type
        ).astype("float64")
    return out[FEATURES]

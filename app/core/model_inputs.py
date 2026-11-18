"""Model raw inputs that equipment parameters can be mapped to.

Mirrors ``ml.features.ai4i.RAW_INPUTS`` (a test asserts they are equal). It is
kept separate so the API can validate configuration without the ml extra.
"""

FEATURE_KEYS = (
    "product_type",
    "air_temp_k",
    "process_temp_k",
    "rotational_speed_rpm",
    "torque_nm",
    "tool_wear_min",
)
CATEGORICAL_KEYS = frozenset({"product_type"})

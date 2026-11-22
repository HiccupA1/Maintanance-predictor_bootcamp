"""Fill a running local API with a realistic plant, through the real API.

    python -m tools.demo.seed_data DEMO_DIR [--api http://127.0.0.1:8000]

Everything goes through HTTP as the right role, so every rule the app
enforces (thresholds, alerts, one work order per alert, closure side effects,
background risk scoring) is applied exactly as it would be for a user.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import httpx

MACHINES = [
    # id, name, location, type, criticality, asset_class
    ("P-101", "Cooling pump P-101", "Hall 1", "Pump", 4, None),
    ("C-201", "Air compressor C-201", "Hall 1", "Compressor", 3, None),
    ("B-301", "Boiler feed pump B-301", "Boiler house", "Pump", 5, None),
    ("CNC-01", "CNC mill CNC-01", "Machining", "Mill", 4, "ai4i_milling"),
    ("CNC-02", "CNC mill CNC-02", "Machining", "Mill", 3, "ai4i_milling"),
]
THRESHOLDS = {
    "P-101": [("Temperature", "°C", 10, 80), ("Vibration", "mm/s", None, 7.1)],
    "C-201": [
        ("Discharge pressure", "bar", 6, 10),
        ("Oil temperature", "°C", None, 95),
    ],
    "B-301": [
        ("Bearing temperature", "°C", None, 85),
        ("Flow", "m³/h", 20, None),
    ],
}
ML_INPUTS = (
    "product_type",
    "air_temp_k",
    "process_temp_k",
    "rotational_speed_rpm",
    "torque_nm",
    "tool_wear_min",
)
HEALTHY = {
    "product_type": "M",
    "air_temp_k": "298.5",
    "process_temp_k": "309.0",
    "rotational_speed_rpm": "1510",
    "torque_nm": "39",
    "tool_wear_min": "40",
}
WORN = {
    "product_type": "L",
    "air_temp_k": "302.1",
    "process_temp_k": "310.5",
    "rotational_speed_rpm": "1310",
    "torque_nm": "64",
    "tool_wear_min": "228",
}


class Client:
    def __init__(self, api: str, tokens: dict[str, str]):
        self.http = httpx.Client(base_url=f"{api}/v1", timeout=30)
        self.tokens = tokens

    def __call__(self, role: str, method: str, url: str, body=None):
        r = self.http.request(
            method,
            url,
            json=body,
            headers={"Authorization": f"Bearer {self.tokens[role]}"},
        )
        if r.status_code >= 400:
            raise RuntimeError(
                f"{role} {method} {url}: {r.status_code} {r.text}"
            )
        return r.json() if r.content else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("demo_dir", type=Path)
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    api = Client(
        args.api, json.loads((args.demo_dir / "tokens.json").read_text())
    )

    params: dict[str, dict[str, str]] = {}
    pks: dict[str, str] = {}
    for mid, name, loc, typ, crit, asset_class in MACHINES:
        eq = api(
            "Admin",
            "POST",
            "/equipment",
            {
                "equipment_id": mid,
                "name": name,
                "location": loc,
                "type": typ,
                "criticality": crit,
                "asset_class": asset_class,
            },
        )
        pks[mid] = eq["id"]
        params[mid] = {}
        if asset_class:
            for key in ML_INPUTS:
                p = api(
                    "PlantManager",
                    "POST",
                    f"/equipment/{mid}/parameters",
                    {
                        "name": key.replace("_", " ").capitalize(),
                        "unit": "-",
                        "max_threshold": 1e9,
                        "feature_key": key,
                    },
                )
                params[mid][key] = p["id"]
        for pname, unit, lo, hi in THRESHOLDS.get(mid, []):
            p = api(
                "PlantManager",
                "POST",
                f"/equipment/{mid}/parameters",
                {
                    "name": pname,
                    "unit": unit,
                    "min_threshold": lo,
                    "max_threshold": hi,
                    "suggested_action": f"Inspect {pname.lower()} sensor and process.",
                },
            )
            params[mid][pname] = p["id"]

    def reading(mid: str, key: str, value: str) -> None:
        api(
            "Operator",
            "POST",
            "/readings",
            {
                "equipment_id": mid,
                "parameter_id": params[mid][key],
                "value": value,
            },
        )

    # Normal operation, then breaches.
    for mid, key, values in [
        ("P-101", "Temperature", ["62", "64", "71", "86"]),  # ends in a breach
        ("P-101", "Vibration", ["3.2", "3.5", "4.1"]),
        ("C-201", "Discharge pressure", ["8.1", "8.4", "10.6"]),  # breach
        ("C-201", "Oil temperature", ["78", "81"]),
        (
            "B-301",
            "Bearing temperature",
            ["70", "91", "93"],
        ),  # breach, then repeat
        ("B-301", "Flow", ["34", "31"]),
    ]:
        for v in values:
            reading(mid, key, v)

    alerts = {
        a["equipment_id"]: a for a in api("PlantManager", "GET", "/alerts")
    }

    # P-101: raised and closed as a confirmed failure.
    wo = api(
        "PlantManager",
        "POST",
        "/work-orders",
        {
            "title": "Temperature breach on Cooling pump P-101",
            "description": "Check the cooling loop and pump bearings.",
            "priority": "CRITICAL",
            "alert_id": alerts[pks["P-101"]]["id"],
        },
    )
    api(
        "MaintenanceEngineer",
        "PUT",
        f"/work-orders/{wo['id']}",
        {
            "status": "CLOSED",
            "resolution_notes": "Replaced worn bearing and flushed the cooling loop.",
            "root_cause": "Bearing wear causing friction heat",
            "failure_confirmed": True,
            "failure_mode": "OTHER",
        },
    )
    # C-201: raised, still open.
    api(
        "PlantManager",
        "POST",
        "/work-orders",
        {
            "title": "Discharge pressure breach on Air compressor C-201",
            "description": "Inspect the relief valve and pressure switch.",
            "priority": "HIGH",
            "alert_id": alerts[pks["C-201"]]["id"],
        },
    )
    # B-301 stays as an open alert, waiting for the Plant Manager.

    # Risk model: activate it, then score a healthy and a worn mill.
    models = api("Admin", "GET", "/models")
    model = next(m for m in models if m["version"] == "ai4i-v1")
    if model["stage"] != "active":
        api(
            "Admin",
            "POST",
            f"/models/{model['id']}/stage",
            {"stage": "active"},
        )
    for key in ML_INPUTS:
        reading("CNC-02", key, HEALTHY[key])
    for key in ML_INPUTS:
        reading("CNC-01", key, HEALTHY[key])
    time.sleep(1)
    for key in ML_INPUTS:
        reading("CNC-01", key, WORN[key])
    time.sleep(2)  # background scoring

    print("Demo data loaded:")
    print(
        f"  {len(MACHINES)} machines, alerts: {len(api('PlantManager', 'GET', '/alerts'))}"
    )
    risk = api("Admin", "GET", "/equipment/CNC-01/risk")
    if risk["latest"]:
        print(
            f"  CNC-01 failure risk {risk['latest']['score']:.0%} (flagged={risk['latest']['flagged']})"
        )


if __name__ == "__main__":
    main()

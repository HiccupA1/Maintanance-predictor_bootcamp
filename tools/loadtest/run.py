"""Closed-loop HTTP load test against a running API.

    python -m tools.loadtest.run --base http://127.0.0.1:8000 \
        --dir OUT_DIR --users 25 --duration 60 [--out report.json]

Each virtual user repeatedly picks a weighted scenario, sends one request and
waits a short think time (0.2–0.8 s). The mix reflects manual operation:
mostly dashboard reads, plus operators recording readings. Every reading
POST also triggers threshold evaluation and risk scoring.

Reports throughput, error rate, and p50/p95/p99 latency per scenario.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import statistics
import time
from collections import defaultdict
from pathlib import Path

import httpx

# name, weight, role
SCENARIOS = [
    ("GET /equipment", 25, "PlantManager"),
    ("GET /equipment/{id}/risk", 15, "MaintenanceEngineer"),
    ("GET /alerts", 15, "PlantManager"),
    ("GET /work-orders", 10, "MaintenanceEngineer"),
    ("GET readings history", 10, "Operator"),
    ("POST /readings (+scoring)", 25, "Operator"),
]

READING_VALUES = {
    "product_type": lambda: random.choice("LMH"),
    "air_temp_k": lambda: f"{random.gauss(300, 2):.1f}",
    "process_temp_k": lambda: f"{random.gauss(310, 1.5):.1f}",
    "rotational_speed_rpm": lambda: str(int(random.gauss(1540, 180))),
    "torque_nm": lambda: f"{random.gauss(40, 10):.1f}",
    "tool_wear_min": lambda: str(random.randint(0, 240)),
}


def _percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, round(q / 100 * (len(ordered) - 1))))
    return ordered[k]


async def _user(client, tokens, targets, deadline, samples, errors) -> None:
    names = [s[0] for s in SCENARIOS]
    weights = [s[1] for s in SCENARIOS]
    roles = {s[0]: s[2] for s in SCENARIOS}
    while time.monotonic() < deadline:
        name = random.choices(names, weights)[0]
        headers = {"Authorization": f"Bearer {tokens[roles[name]]}"}
        target = random.choice(targets)
        eq = target["equipment_id"]
        if name == "GET /equipment":
            req = client.get("/v1/equipment", headers=headers)
        elif name == "GET /equipment/{id}/risk":
            req = client.get(f"/v1/equipment/{eq}/risk", headers=headers)
        elif name == "GET /alerts":
            req = client.get("/v1/alerts", headers=headers)
        elif name == "GET /work-orders":
            req = client.get("/v1/work-orders?page_size=50", headers=headers)
        elif name == "GET readings history":
            pid = target["parameters"]["torque_nm"]
            req = client.get(
                f"/v1/equipment/{eq}/parameters/{pid}/readings",
                headers=headers,
            )
        else:
            key = random.choice(list(READING_VALUES))
            req = client.post(
                "/v1/readings",
                headers=headers,
                json={
                    "equipment_id": eq,
                    "parameter_id": target["parameters"][key],
                    "value": READING_VALUES[key](),
                },
            )
        start = time.perf_counter()
        try:
            resp = await req
            ok = resp.status_code < 400
        except httpx.HTTPError:
            ok = False
        elapsed_ms = (time.perf_counter() - start) * 1000
        samples[name].append(elapsed_ms)
        if not ok:
            errors[name] += 1
        await asyncio.sleep(random.uniform(0.2, 0.8))


async def run(base: str, directory: Path, users: int, duration: int) -> dict:
    tokens = json.loads((directory / "tokens.json").read_text())
    targets = json.loads((directory / "targets.json").read_text())
    samples: dict[str, list[float]] = defaultdict(list)
    errors: dict[str, int] = defaultdict(int)
    limits = httpx.Limits(
        max_connections=users, max_keepalive_connections=users
    )
    async with httpx.AsyncClient(
        base_url=base, timeout=30, limits=limits
    ) as client:
        # Warm-up: JWKS fetch, model load, connection pool.
        for role in tokens:
            await client.get(
                "/v1/me", headers={"Authorization": f"Bearer {tokens[role]}"}
            )
        started = time.monotonic()
        deadline = started + duration
        await asyncio.gather(
            *[
                _user(client, tokens, targets, deadline, samples, errors)
                for _ in range(users)
            ]
        )
        wall = time.monotonic() - started

    per = {}
    for name, values in samples.items():
        per[name] = {
            "requests": len(values),
            "errors": errors[name],
            "p50_ms": round(statistics.median(values), 1),
            "p95_ms": round(_percentile(values, 95), 1),
            "p99_ms": round(_percentile(values, 99), 1),
        }
    every = [v for values in samples.values() for v in values]
    total_errors = sum(errors.values())
    return {
        "users": users,
        "duration_s": round(wall, 1),
        "requests": len(every),
        "throughput_rps": round(len(every) / wall, 1),
        "error_rate": round(total_errors / max(len(every), 1), 5),
        "p50_ms": round(statistics.median(every), 1),
        "p95_ms": round(_percentile(every, 95), 1),
        "p99_ms": round(_percentile(every, 99), 1),
        "scenarios": per,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--dir", type=Path, required=True)
    parser.add_argument("--users", type=int, default=25)
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = asyncio.run(run(args.base, args.dir, args.users, args.duration))
    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        args.out.write_text(text)


if __name__ == "__main__":
    main()

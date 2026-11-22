"""Keystroke-Level Model (KLM) task-time estimates.

Card, S. K., Moran, T. P. and Newell, A. (1980). The keystroke-level model
for user performance time with interactive systems. Communications of the
ACM 23(7), 396-410. Operator times as published there:

    K  keystroke                  0.28 s (average non-secretarial typist;
                                  0.20 s good typist, 0.50 s poor typist)
    P  point with a mouse         1.10 s
    B  mouse button press/release 0.10 s (a click is BB = 0.20 s)
    H  home hands mouse<->keyboard 0.40 s
    M  mental preparation         1.35 s

Each action type is a fixed sequence of operators, applied identically to
both flows. Three action types depend on things KLM does not model, so they
carry explicit, labelled assumptions with a low/mid/high range:

    R  system response when opening an app or file   (1 / 2 / 5 s)
    S  visual search for a row or value in a sheet   (3 / 5 / 15 s)
    C  comparing a value against limits by eye       (2 / 3 / 6 s)
"""

from __future__ import annotations

from dataclasses import dataclass

P, B, H, M = 1.10, 0.10, 0.40, 1.35
CLICK = P + 2 * B  # point and click


@dataclass(frozen=True)
class Scenario:
    """Typing speed and the three non-KLM assumptions."""

    name: str
    k: float
    response: float
    search: float
    compare: float


SCENARIOS = {
    "low": Scenario("low (fast user, quick system)", 0.20, 1.0, 3.0, 2.0),
    "mid": Scenario("mid (KLM average typist)", 0.28, 2.0, 5.0, 3.0),
    "high": Scenario("high (slow typist, slow system)", 0.50, 5.0, 15.0, 6.0),
}


def action_seconds(action: dict, s: Scenario) -> float:
    """KLM time for one action (see the module docstring)."""
    kind = action["type"]
    if kind == "click":  # decide, point, click
        return M + CLICK
    if kind == "select":  # decide, open the dropdown, choose an option
        return M + 2 * CLICK
    if kind == "type":  # decide, focus the field, home, type, home back
        return M + CLICK + 2 * H + action["chars"] * s.k
    if kind == "navigate":  # decide, click to open, wait for it
        return M + CLICK + s.response
    if kind == "lookup":  # decide, search visually
        return M + s.search
    if kind == "compare":  # decide, compare
        return M + s.compare
    raise ValueError(f"unknown action type: {kind!r}")


def flow_seconds(actions: list[dict], s: Scenario) -> float:
    return sum(action_seconds(a, s) for a in actions)


def summarise(actions: list[dict]) -> dict:
    """Step count plus KLM time under each scenario."""
    by_type: dict[str, int] = {}
    by_actor: dict[str, int] = {}
    for a in actions:
        by_type[a["type"]] = by_type.get(a["type"], 0) + 1
        by_actor[a["actor"]] = by_actor.get(a["actor"], 0) + 1
    return {
        "steps": len(actions),
        "keystrokes": sum(a.get("chars", 0) for a in actions),
        "by_type": by_type,
        "by_actor": by_actor,
        "seconds": {
            k: round(flow_seconds(actions, s), 1) for k, s in SCENARIOS.items()
        },
    }


def reduction(before: float, after: float) -> float:
    """Percentage reduction from ``before`` to ``after``."""
    return round(100 * (before - after) / before, 1)

"""Workflow benchmark: KLM pricing rules, baseline integrity, report build."""

from __future__ import annotations

import json

import pytest

from tools.workflow_benchmark import klm, report

MID = klm.SCENARIOS["mid"]
ACTION_TYPES = {"navigate", "click", "select", "type", "lookup", "compare"}


def test_klm_operator_times_match_card_moran_newell() -> None:
    assert (klm.P, klm.B, klm.H, klm.M) == (1.10, 0.10, 0.40, 1.35)
    assert MID.k == 0.28  # average non-secretarial typist


@pytest.mark.parametrize(
    ("action", "seconds"),
    [
        ({"type": "click"}, 1.35 + 1.1 + 0.2),
        ({"type": "select"}, 1.35 + 2 * 1.3),
        ({"type": "type", "chars": 10}, 1.35 + 1.3 + 0.8 + 10 * 0.28),
        ({"type": "navigate"}, 1.35 + 1.3 + 2.0),
        ({"type": "lookup"}, 1.35 + 5.0),
        ({"type": "compare"}, 1.35 + 3.0),
    ],
)
def test_action_pricing(action, seconds) -> None:
    assert klm.action_seconds(action, MID) == pytest.approx(seconds)


def test_unknown_action_type_is_rejected() -> None:
    with pytest.raises(ValueError):
        klm.action_seconds({"type": "teleport"}, MID)


def test_scenarios_are_ordered_low_to_high() -> None:
    lo, mid, hi = (klm.SCENARIOS[k] for k in ("low", "mid", "high"))
    for field in ("k", "response", "search", "compare"):
        assert getattr(lo, field) <= getattr(mid, field) <= getattr(hi, field)


def test_reduction() -> None:
    assert klm.reduction(60, 20) == 66.7
    assert klm.reduction(100, 100) == 0.0


def test_baseline_is_well_formed() -> None:
    baseline = json.loads(report.BASELINE.read_text())
    assert baseline["actions"], "baseline has no actions"
    for a in baseline["actions"]:
        assert a["type"] in ACTION_TYPES, a
        assert a["actor"] in report.ACTORS, a
        assert a["description"]
        assert (a["type"] == "type") == ("chars" in a), a


def test_report_builds_from_a_recorded_app_flow(tmp_path) -> None:
    app = {
        "automated_wall_time_s": 12.3,
        "actions": [
            {"actor": "Operator", "type": "navigate", "description": "Open"},
            {
                "actor": "Operator",
                "type": "type",
                "chars": 2,
                "description": "Value",
            },
            {
                "actor": "PlantManager",
                "type": "click",
                "description": "Create",
            },
        ],
        "automated": ["Threshold checked"],
    }
    path = tmp_path / "app.json"
    path.write_text(json.dumps(app))
    md, result = report.build(path)
    assert result["app_steps"] == 3
    assert result["manual_steps"] == len(
        json.loads(report.BASELINE.read_text())["actions"]
    )
    assert 0 < result["step_reduction_pct"] < 100
    assert "Keystroke-Level Model" in md and "Threshold checked" in md

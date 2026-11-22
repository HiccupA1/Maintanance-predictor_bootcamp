"""Build Docs/stage-9/workflow-comparison.md from the two recorded flows.

    # 1. Record the app flow (runs the Playwright scenario):
    #    cd frontend && npm run e2e -- workflow-benchmark
    # 2. Generate the report:
    python -m tools.workflow_benchmark.report [--app reports/workflow-app.json]

The manual flow is tools/workflow_benchmark/baseline.json. Both are priced
by the same KLM rules (tools/workflow_benchmark/klm.py).
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from tools.workflow_benchmark.klm import SCENARIOS, reduction, summarise

ROOT = Path(__file__).resolve().parents[2]
BASELINE = Path(__file__).with_name("baseline.json")
DEFAULT_APP = ROOT / "reports" / "workflow-app.json"
OUT = ROOT / "Docs" / "stage-9" / "workflow-comparison.md"

ACTORS = ("Operator", "PlantManager", "MaintenanceEngineer")


def _actions_table(actions: list[dict]) -> str:
    rows = [
        "| # | Actor | Action | Type | Characters |",
        "|---|---|---|---|---|",
    ]
    for i, a in enumerate(actions, 1):
        rows.append(
            f"| {i} | {a['actor']} | {a['description']} | {a['type']} | {a.get('chars', '')} |"
        )
    return "\n".join(rows)


def build(app_path: Path) -> tuple[str, dict]:
    manual = json.loads(BASELINE.read_text())
    app = json.loads(app_path.read_text())
    m, a = summarise(manual["actions"]), summarise(app["actions"])

    step_cut = reduction(m["steps"], a["steps"])
    key_cut = reduction(m["keystrokes"], a["keystrokes"])
    time_cut = {
        k: reduction(m["seconds"][k], a["seconds"][k]) for k in SCENARIOS
    }
    lo, hi = min(time_cut.values()), max(time_cut.values())
    result = {
        "manual_steps": m["steps"],
        "app_steps": a["steps"],
        "step_reduction_pct": step_cut,
        "keystroke_reduction_pct": key_cut,
        "time_reduction_pct": time_cut,
        "manual_seconds": m["seconds"],
        "app_seconds": a["seconds"],
    }

    actor_rows = "\n".join(
        f"| {actor} | {m['by_actor'].get(actor, 0)} | {a['by_actor'].get(actor, 0)} |"
        for actor in ACTORS
    )
    time_rows = "\n".join(
        f"| {s.name} | {m['seconds'][k]:.0f} s ({m['seconds'][k] / 60:.1f} min) | "
        f"{a['seconds'][k]:.0f} s ({a['seconds'][k] / 60:.1f} min) | **{time_cut[k]}%** |"
        for k, s in SCENARIOS.items()
    )
    automated = "\n".join(f"- {x}" for x in app["automated"])

    md = f"""# Workflow Comparison: Manual Process vs the App

**Generated:** {date.today().isoformat()} by `python -m tools.workflow_benchmark.report`
from `tools/workflow_benchmark/baseline.json` (manual) and the recorded
Playwright run `reports/workflow-app.json` (app,
`frontend/e2e/specs/workflow-benchmark.spec.ts`). Do not edit by hand.

## Scenario (identical for both)
1. An Operator records a reading that breaches a threshold.
2. The Plant Manager raises a work order for it.
3. The Maintenance Engineer closes it with resolution notes, a root cause and
   the failure outcome.
4. The issue ends resolved, and the asset's last-service date is updated.

Both flows type the same free text. The manual process is described in
`Docs/stage-9/workflow-baseline-sop.md`. **That baseline is an assumption**
and should be validated with a maintenance team.

## Results

| Measure | Manual | App | Reduction |
|---|---|---|---|
| User steps | {m['steps']} | {a['steps']} | **{step_cut}%** |
| Characters typed | {m['keystrokes']} | {a['keystrokes']} | {key_cut}% |

### Steps by role
| Role | Manual | App |
|---|---|---|
{actor_rows}

### Estimated operator time (Keystroke-Level Model)
| Assumptions | Manual | App | Reduction |
|---|---|---|---|
{time_rows}

Across all three assumption sets, estimated operator time falls by
**{lo}% to {hi}%**.

For reference, the scripted browser completed the app flow in
{app['automated_wall_time_s']} s. That is machine speed, not human time, and
is not used in any comparison.

## What the app does that the manual process makes people do
{automated}

## Method
- **Step:** one user action, meaning opening an app or page, a click, a
  dropdown choice, typing into a field, a visual lookup, or a by-eye
  comparison. Both flows use the same vocabulary. The app flow is counted
  automatically while Playwright drives the real UI.
- **Time:** the Keystroke-Level Model (Card, Moran and Newell, 1980), using
  the published operator times (K, P, B, H, M) and the same per-action rules
  for both flows (`klm.py`).
- **Assumptions:** system response time, visual search and by-eye comparison
  are not KLM operators. They take labelled low, mid and high values, and the
  range above covers all of them.
- **Fairness:**
  - The manual process is entirely at a desktop computer, with no paper and
    no walking, and with no waiting for email replies.
  - Opening the app counts as a step for every role, the same as opening an
    email.
  - Both choices favour the manual process.

## Limitations
- This is a **modelled** estimate, not timed users. KLM predicts expert,
  error-free performance. Real users make errors, which typically affect the
  manual process more (retyping across sheets).
- The baseline is a documented assumption, not an observed client process.
- **Not counted:** notification latency (the app has no push notifications;
  someone must open it) and time spent waiting between people.

## Claim wording supported by this report
> In a Keystroke-Level Model task analysis of a breach-to-closure workflow,
> the app needed **{step_cut}% fewer user steps** ({m['steps']} → {a['steps']})
> and an estimated **{lo}–{hi}% less operator time** than a documented
> spreadsheet-and-email process.

## Appendix A: Manual actions
{_actions_table(manual['actions'])}

## Appendix B: App actions (recorded)
{_actions_table(app['actions'])}
"""
    return md, result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--app", type=Path, default=DEFAULT_APP)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    md, result = build(args.app)
    args.out.write_text(md, encoding="utf-8")
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "workflow-comparison.json").write_text(
        json.dumps(result, indent=2)
    )
    print(json.dumps(result, indent=2))
    print(f"\nWrote {args.out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

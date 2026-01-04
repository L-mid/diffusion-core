"""
## Controls and ensures this repo's run layout.

Why: ensure layout meets expectations for A): humans, B): machine parsers.


### importable:
    create_run_dir: creates run layout, fails on existing run_dir check, returns RunPaths dataclass.

*Tested by: tests/config/test_run_layout.py*
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunPaths:
    """Minimum viable layout expectations."""

    run_dir: Path
    meta_dir: Path
    logs_dir: Path
    ckpts_dir: Path
    artifacts_dir: Path
    metrics_jsonl: Path
    ckpt_last_dir: Path


def create_run_dir(run_root: Path, experiment_name: str, *, run_id: str) -> RunPaths:
    """
    Creates the expected layout for a single run.

    Layout expections:
      - meta/
      - logs/metrics.jsonl
      - ckpts/last/
      - artifacts/
    """
    safe = "".join(c if (c.isalnum() or c in "-_") else "-" for c in experiment_name).strip("-")
    rid = f"{run_id}_{safe or 'run'}"

    run_dir = run_root / rid
    meta_dir = run_dir / "meta"
    logs_dir = run_dir / "logs"
    ckpts_dir = run_dir / "ckpts"
    artifacts_dir = run_dir / "artifacts"
    ckpt_last_dir = ckpts_dir / "last"
    metrics_jsonl = logs_dir / "metrics.jsonl"

    # Check: fail if run_dir already exists (no silent reuse/merging issues).
    run_dir.mkdir(parents=True, exist_ok=False)  # might want to add a more specific error message
    meta_dir.mkdir(parents=True, exist_ok=False)
    logs_dir.mkdir(parents=True, exist_ok=False)
    ckpts_dir.mkdir(parents=True, exist_ok=False)
    artifacts_dir.mkdir(parents=True, exist_ok=False)
    ckpt_last_dir.mkdir(parents=True, exist_ok=False)

    # Create empty metrics file, as part of layout expectations.
    metrics_jsonl.write_text("", encoding="utf-8")

    # to cli:
    return RunPaths(
        run_dir=run_dir,
        meta_dir=meta_dir,
        logs_dir=logs_dir,
        ckpts_dir=ckpts_dir,
        artifacts_dir=artifacts_dir,
        metrics_jsonl=metrics_jsonl,
        ckpt_last_dir=ckpt_last_dir,
    )

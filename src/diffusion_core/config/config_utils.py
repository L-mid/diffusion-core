"""
## Default config classes & helpers for this repo. Uses pydantic.

Why: ensures config is strict, config instances are immutable, and overrides are not mutations.


Importables
    ### models
    RunConfig: strict + copy-on-override. Immutable via frozen=True (may change)
    AppConfig: the runtime config updated to any overrides (real runtime cfg)

    ### helpers
    load_config:        loads yaml, validates with model_validate(`cfg`) on AppConfig dict
    with_run_root:      **copies** and updates cfg dict with overrides in AppConfig
    write_resolved_yaml: writes the true, final resolved yaml into out_path (in run dir)


*Tested by: tests/config/test_config_utils.py*
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict


class RunConfig(BaseModel):
    """
    Run-specific config.

    Strict: unknown keys are errors.

    Defaults:
        experiment_name = "smoke"
        run_root = "runs"
        cfg = YAML merged with defaults, then validated

    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    experiment_name: str = "smoke"
    run_root: str = "runs"


class AppConfig(BaseModel):
    """
    Applied config.

    Strict: unknown keys are errors.

    Defaults:
        seed = 0            (please note: this is the **default seed** unless filled)
        run = RunConfig()   (previously untouched cfg)
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    seed: int = 0
    run: RunConfig = RunConfig()


def load_config(path: Path) -> AppConfig:
    """Load YAML and validate strictly (unknown keys hard-fail)."""
    raw: Any
    with path.open("r", encoding="utf-8") as f:
        raw = (
            yaml.safe_load(f) or {}
        )  # upon empty or `null`, return plain {} (avoids `None` passing in)
    return AppConfig.model_validate(raw)


def with_run_root(cfg: AppConfig, run_root: Path) -> AppConfig:
    """Return a new config with run.run_root overridden (no mutation)."""
    return cfg.model_copy(update={"run": cfg.run.model_copy(update={"run_root": str(run_root)})})


def write_resolved_yaml(cfg: AppConfig, out_path: Path) -> None:
    """Write resolved config snapshot (this is what actually ran)."""
    payload = cfg.model_dump(mode="python")
    out_path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")

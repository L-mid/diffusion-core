"""
## Sub CLI run logic entrypoint mechanics.

Why: separate tests (speed + tracebacks) & bloat from the main CLI entrypoint.

Logic flow at play:
  load validated config -> override run_root
  -> create run_dir layout -> write config.resolved.yaml
  Return: run_dir   (for use from CLI)


*Tested by: tests/config/test_config_runner.py*
"""

from __future__ import annotations

from pathlib import Path

from diffusion_core.config.config_utils import load_config, with_run_root, write_resolved_yaml
from diffusion_core.config.run_layout import create_run_dir


def run_once(*, config_path: Path, run_root: Path, run_id: str = "smoke") -> Path:
    """
    Sub entrypoint CLI running logic:
      load validated config -> override run_root
      -> create run_dir layout -> write config.resolved.yaml
    Returns: run_dir
    """
    cfg = load_config(config_path)  # loads cfg
    cfg = with_run_root(cfg, run_root)  # resolves to correct root

    paths = create_run_dir(
        run_root, cfg.run.experiment_name, run_id=run_id
    )  # creates layout to expectactions
    write_resolved_yaml(
        cfg, paths.run_dir / "config.resolved.yaml"
    )  # attached final run's yaml **ATFER** all cfg manipulations
    return paths.run_dir

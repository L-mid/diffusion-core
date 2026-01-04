"""
## Unit tests for yaml config loader, root resolver, writer, and pydanic's validation.

Tests:
    In general: provided cfg loads and can be manipulated without error.
    1) unknown top keys fail validation.
    2) unknown nested keys fail validation.
    3) config overrides to a new dir sucessfully
    4) final resolved yaml written and roundtrip sucessful

*This tests: src/diffusion_core/config/config_utils.py*
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from diffusion_core.config.config_utils import load_config, with_run_root, write_resolved_yaml


def test_unknown_top_key_fails(tmp_path: Path) -> None:
    """Loads config, and ensures validation fails on unknown **top** key."""
    p = tmp_path / "bad.yaml"
    p.write_text("seed: 0\nrun:\n  experiment_name: smoke\nBAD_KEY: 123\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_config(p)


def test_unknown_nested_key_fails(tmp_path: Path) -> None:
    """Loads config, and ensures validation fails on unknown **nested** key."""
    p = tmp_path / "bad.yaml"
    p.write_text("seed: 0\nrun:\n  experiment_name: smoke\n  BAD_NESTED: true\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_config(p)


def test_with_run_root_returns_new_cfg(tmp_path: Path) -> None:
    """
    with_run_root **copies** config to new dir.
    """
    p = tmp_path / "ok.yaml"
    p.write_text("seed: 1\nrun:\n  experiment_name: smoke\n", encoding="utf-8")
    cfg0 = load_config(p)
    cfg1 = with_run_root(cfg0, tmp_path / "runs")

    assert cfg0.run.run_root == "runs"  # default
    assert cfg1.run.run_root.endswith("runs")
    assert cfg0 is not cfg1


def test_write_resolved_yaml_roundtrip(tmp_path: Path) -> None:
    """Resolved yaml roundtrips successfully."""
    p = tmp_path / "ok.yaml"
    p.write_text("seed: 7\nrun:\n  experiment_name: smoke\n", encoding="utf-8")
    cfg = load_config(p)

    out = tmp_path / "config.resolved.yaml"
    write_resolved_yaml(cfg, out)

    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert data["seed"] == 7
    assert data["run"]["experiment_name"] == "smoke"
    assert data["run"]["run_root"] == "runs"

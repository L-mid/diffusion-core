"""
## Ensures sub CLI logic flow behaves perfectly to expectations.

Tests:
    1) loads validated config -> override run_root
        -> create run_dir layout -> write config.resolved.yaml
    2) yaml output actually readable.

*This tests: tests/config/test_config_runner.py*
"""

from __future__ import annotations

from pathlib import Path

import yaml

from diffusion_core.config.runner import run_once


def test_runner_logic(tmp_path: Path) -> None:
    config_path = tmp_path / "smoke.yaml"
    config_path.write_text("seed: 7\nrun:\n  experiment_name: smoke\n", encoding="utf-8")

    run_root = tmp_path / "run_root"
    run_root.mkdir()

    run_dir = run_once(config_path=config_path, run_root=run_root, run_id="r0001")

    # expected layout exists
    assert (run_dir / "meta").is_dir()
    assert (run_dir / "logs" / "metrics.jsonl").is_file()
    assert (run_dir / "ckpts" / "last").is_dir()
    assert (run_dir / "artifacts").is_dir()

    # config is resolved
    resolved = run_dir / "config.resolved.yaml"
    assert resolved.is_file()

    # roundtrip works
    data = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    assert data["seed"] == 7
    assert data["run"]["experiment_name"] == "smoke"
    assert Path(data["run"]["run_root"]).resolve() == run_root.resolve()

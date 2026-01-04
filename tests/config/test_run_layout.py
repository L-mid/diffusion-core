"""
## Unit tests for this repo's expected run layout.

Tests:
    create_run_dir:
    1) layout resolves as expected.
    2) Failure if run_dir already exists when attempted.


*This tests: src/diffusion_core/config/run_layout.py*
"""

from __future__ import annotations

from pathlib import Path

import pytest

from diffusion_core.config.run_layout import create_run_dir


def test_creates_expected_layout(tmp_path: Path) -> None:
    """Tests expectations for a run's layout remain intact."""
    run_root = tmp_path / "runs"
    run_root.mkdir()

    paths = create_run_dir(run_root, "smoke", run_id="r0001")

    assert paths.run_dir.is_dir()
    assert (paths.run_dir / "meta").is_dir()
    assert (paths.run_dir / "logs").is_dir()
    assert (paths.run_dir / "logs" / "metrics.jsonl").is_file()
    assert (paths.run_dir / "ckpts").is_dir()
    assert (paths.run_dir / "ckpts" / "last").is_dir()
    assert (paths.run_dir / "artifacts").is_dir()


def test_fails_if_run_dir_already_exists(tmp_path: Path) -> None:
    """Fails if run_dir already exists on a new run attempt."""
    run_root = tmp_path / "runs"
    run_root.mkdir()

    _ = create_run_dir(run_root, "smoke", run_id="r0001")
    with pytest.raises(FileExistsError):
        _ = create_run_dir(run_root, "smoke", run_id="r0001")

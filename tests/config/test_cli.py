"""
Integration test for CLI.

Tests:
    1) CLI runs and returns output matched to basic expectaions.


*This tests: src/diffusion_core/cli.py*
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def _extract_run_dir(out: str) -> Path:
    """Ensure run_dir is recoverable."""
    m = re.search(r"^RUN_DIR:\s*(.+)\s*$", out, flags=re.MULTILINE)
    if not m:
        raise AssertionError(f"Missing RUN_DIR line.\n\nOUT:\n{out}")
    return Path(m.group(1)).expanduser().resolve()


def test_cli_integration(tmp_path: Path) -> None:
    """
    Creates run_dir, then expands run_dir in a check for expectations.
    """

    # Minimal config file (kept inside tmp.)
    cfg = tmp_path / "smoke.yaml"
    cfg.write_text("seed: 0\nrun:\n  experiment_name: smoke\n", encoding="utf-8")

    run_root = tmp_path / "runs"
    run_root.mkdir()

    cmd = [
        sys.executable,
        "-m",
        "diffusion_core.cli",
        "smoke",
        "--config",
        str(cfg),
        "--run-root",
        str(run_root),
        "--run-id",
        "r0001",  # stable run_id for test (and avoids randomness in assertions)
    ]

    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=30,
        check=False,
    )

    assert p.returncode == 0, f"CLI smoke failed\n\nOUT:\n{p.stdout}"

    run_dir = _extract_run_dir(p.stdout)

    # expected outputs
    assert (run_dir / "config.resolved.yaml").is_file()
    assert (run_dir / "meta").is_dir()
    assert (run_dir / "logs" / "metrics.jsonl").is_file()
    assert (run_dir / "ckpts" / "last").is_dir()
    assert (run_dir / "artifacts").is_dir()

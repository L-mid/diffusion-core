from __future__ import annotations

from pathlib import Path

import pytest


def find_repo_root(start: Path) -> Path:
    """Resolves the repo root using `pyproject.toml`."""
    start = start.resolve()
    for p in (start, *start.parents):
        if (p / "pyproject.toml").exists():
            return p
    raise RuntimeError(f"Could not find repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT

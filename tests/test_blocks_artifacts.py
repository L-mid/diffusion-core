"""
Unit tests for blocking artifacts.

Tests two cases:
    1) Artifacts too large don't go through.
    2) Correctly size artifacts do.

    
Test file: tests/test_blocks_artifacts.py

"""


from pathlib import Path

import tools.blocks_artifacts as ba


def _make_sparse_file(path: Path, size_bytes: int) -> None:
    # sparse file: fast and doesn't actually write 20MB of data
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.seek(size_bytes - 1)
        f.write(b"\0")


def test_allows_small_good_file(tmp_path: Path):
    p = tmp_path / "good.dat"
    p.write_bytes(b"hello")  # tiny, allowed ext, not in forbidden dirs

    violations = ba.scan_paths([str(p)], max_bytes=ba.DEFAULT_MAX_BYTES)
    assert violations == []


def test_rejects_over_20mb_file(tmp_path: Path):
    p = tmp_path / "big.dat"
    _make_sparse_file(p, ba.DEFAULT_MAX_BYTES + 1)

    violations = ba.scan_paths([str(p)], max_bytes=ba.DEFAULT_MAX_BYTES)
    assert len(violations) == 1
    assert violations[0].path == str(p)
    assert "file too large" in violations[0].reason.lower()

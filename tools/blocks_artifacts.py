#!/usr/bin/env python3
"""
Artifact Blocker (STRICT)

Fails the check if any forbidden artifacts are present in:
- staged changes (default; for local pre-commit)
- entire repo working tree (for CI)

Why: .gitignore can be bypassed with `git add -f`, and doesn't protect history by itself.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple


FORBIDDEN_DIR_NAMES = {
    "runs",
    "run",
    "checkpoints",
    "checkpoint",
    "ckpts",
    "ckpt",
    "data",
    "dataset",
    "datasets",
    "caches",
    "cache",
    ".cache",
    "wandb",
    "lightning_logs",
}

FORBIDDEN_EXTS = {
    # checkpoints / weights
    ".pt",
    ".pth",
    ".ckpt",
    ".safetensors",
    ".onnx",
    # binary blobs
    ".npz",
    ".npy",
    ".pkl",
    ".pickle",
    ".joblib",
    # archives
    ".zip",
    ".tar",
    ".tgz",
    ".gz",
    ".7z",
    ".rar",
}

DEFAULT_MAX_BYTES = 20 * 1024 * 1024  # 20 MB (extra safety net)


@dataclass(frozen=True)
class Violation:
    path: str
    reason: str


def _run_git(args: List[str]) -> str:
    try:
        out = subprocess.check_output(["git", *args], stderr=subprocess.STDOUT)
        return out.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError as e:
        msg = e.output.decode("utf-8", errors="replace")
        raise RuntimeError(f"git command failed: git {' '.join(args)}\n{msg}") from e


def _list_staged_files() -> List[str]:
    # Include A(dd), C(opy), M(odify), R(ename), T(type), U(unmerged), X(unknown), B(broken)
    out = _run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMRTUXB"])
    files = [line.strip() for line in out.splitlines() if line.strip()]
    return files


def _list_repo_files() -> List[str]:
    # Use git ls-files to avoid scanning ignored/untracked junk,
    # but still catch tracked forbidden files.
    out = _run_git(["ls-files"])
    files = [line.strip() for line in out.splitlines() if line.strip()]
    return files


def _is_under_forbidden_dir(path: Path) -> Tuple[bool, str]:
    parts = [p for p in path.parts if p not in (".", "")]
    for p in parts:
        if p in FORBIDDEN_DIR_NAMES:
            return True, f"forbidden directory segment '{p}/'"
    return False, ""


def _is_forbidden_ext(path: Path) -> Tuple[bool, str]:
    suf = path.suffix.lower()
    if suf in FORBIDDEN_EXTS:
        return True, f"forbidden extension '{suf}'"
    return False, ""


def _is_too_large(path: Path, max_bytes: int) -> Tuple[bool, str]:
    try:
        size = path.stat().st_size
    except FileNotFoundError:
        # Renames/deletes can appear in staged lists; ignore missing.
        return False, ""
    if size > max_bytes:
        return True, f"file too large ({size} bytes > {max_bytes} bytes)"
    return False, ""


def _check_paths(paths: Iterable[str], max_bytes: int) -> List[Violation]:
    violations: List[Violation] = []
    for p in paths:
        # Normalize to forward slashes for output readability
        rel = Path(p)
        if rel.parts and rel.parts[0] == ".git":
            continue

        bad_dir, dir_reason = _is_under_forbidden_dir(rel)
        if bad_dir:
            violations.append(Violation(p, dir_reason))
            continue

        bad_ext, ext_reason = _is_forbidden_ext(rel)
        if bad_ext:
            violations.append(Violation(p, ext_reason))
            continue

        # Size check only if the file exists in working tree
        bad_size, size_reason = _is_too_large(rel, max_bytes=max_bytes)
        if bad_size:
            violations.append(Violation(p, size_reason))
            continue

    return violations


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--mode",
        choices=["staged", "repo"],
        default="staged",
        help="staged=check staged changes (pre-commit), repo=check entire tracked repo (CI).",
    )
    ap.add_argument(
        "--max-bytes",
        type=int,
        default=DEFAULT_MAX_BYTES,
        help="Fail if any file exceeds this size (extra safety net).",
    )
    args = ap.parse_args()

    try:
        files = _list_staged_files() if args.mode == "staged" else _list_repo_files()
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 2

    violations = _check_paths(files, max_bytes=args.max_bytes)
    if not violations:
        print(f"[blocks_artifacts] OK ({args.mode}): no forbidden artifacts detected.")
        return 0

    print("\n[blocks_artifacts] FAIL: forbidden artifacts detected:\n", file=sys.stderr)
    for v in violations:
        print(f"  - {v.path}  ({v.reason})", file=sys.stderr)

    print(
        "\nMove artifacts to GitHub Releases/external storage and reference them with SHA256.\n"
        "See docs/the_artifacts_policy.md.\n",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

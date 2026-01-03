"""
Unit test for the precommiting guard.

Tests:
    1) commit fails if not in a git repository
    2) commit is blocked if on the main branch
    3) commit is blocked if on a detached HEAD.
    4) commit is blocked if on a stale ref/deleted branch (passes otherwise)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parents[1] / "tools" / "precommit_guard.py").resolve()


def run(cmd: list[str], cwd: Path, check: bool = False) -> tuple[int, str]:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"  # never prompt in tests
    p = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if check and p.returncode != 0:
        raise AssertionError(f"Command failed: {cmd}\n{p.stdout}")
    return p.returncode, (p.stdout or "").strip()


def git(cwd: Path, *args: str, check: bool = True) -> tuple[int, str]:
    return run(["git", *args], cwd=cwd, check=check)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def commit(repo: Path, msg: str, fname: str = "file.txt", content: str = "x\n") -> None:
    write_text(repo / fname, content)
    git(repo, "add", fname)
    git(repo, "commit", "-m", msg)


def setup_repo_with_origin(tmp_path: Path) -> tuple[Path, Path]:
    """
    Create:
      - a working repo with user configured
      - a local bare "origin" remote
      - main branch pushed to origin
    """
    repo = tmp_path / "repo"
    remote = tmp_path / "origin.git"
    repo.mkdir()

    git(repo, "init")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test User")

    commit(repo, "initial")
    git(repo, "branch", "-M", "main")

    # bare origin
    run(["git", "init", "--bare", str(remote)], cwd=tmp_path, check=True)

    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "main")

    return repo, remote


def run_guard(cwd: Path) -> tuple[int, str]:
    return run([sys.executable, str(SCRIPT)], cwd=cwd)


def test_not_a_git_repo(tmp_path: Path) -> None:
    nogit = tmp_path / "nogit"
    nogit.mkdir()
    rc, out = run_guard(nogit)
    assert rc == 1
    assert "not a git repo" in out


def test_blocks_commit_on_main(tmp_path: Path) -> None:
    repo, _ = setup_repo_with_origin(tmp_path)
    git(repo, "checkout", "main")
    rc, out = run_guard(repo)
    assert rc == 1
    assert "refusing commit on 'main'" in out


def test_blocks_detached_head(tmp_path: Path) -> None:
    repo, _ = setup_repo_with_origin(tmp_path)

    # detach at current HEAD commit
    _, head = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", head)

    rc, out = run_guard(repo)
    assert rc == 1
    assert "detached HEAD" in out


def test_blocks_stale_branch_and_passes_when_fresh(tmp_path: Path) -> None:
    repo, _ = setup_repo_with_origin(tmp_path)

    # create feature branch at current main
    git(repo, "checkout", "-b", "chore/feat")

    # advance main and push to origin (feature branch becomes stale/behind)
    git(repo, "checkout", "main")
    commit(repo, "advance main", fname="main.txt", content="main advance\n")
    git(repo, "push", "origin", "main")

    # back to feature branch (stale now)
    git(repo, "checkout", "chore/feat")
    rc, out = run_guard(repo)
    assert rc == 1
    assert "stale ref" in out or "not based on latest origin/main" in out

    # make it fresh: fast-forward feature to origin/main (no divergence)
    git(repo, "merge", "origin/main")

    rc, out = run_guard(repo)
    assert rc == 0, out

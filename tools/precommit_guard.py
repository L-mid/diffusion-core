"""
Precommit guard.

Why: Prevents main commits (disallowed) and stale ref pushes in PR's.

Fails the check if:
- Commiting to main
- Commiting via detached HEAD
- Commit is not based on latest origin/main (stale ref)

Tested by: tests/test_precommit_guard.py
"""

#!/usr/bin/env python3
from __future__ import annotations

import subprocess


def sh(*cmd: str) -> tuple[int, str]:
    """Runs git in subprocess."""
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout.strip()


def main() -> int:
    """Must be on a real branch (not detached HEAD)."""
    rc, branch = sh("git", "rev-parse", "--abbrev-ref", "HEAD")
    if rc != 0:
        print("[precommit_guard.py]: not a git repo (or git not available).")
        return 1

    if branch == "HEAD":
        print("[precommit_guard.py]: detached HEAD. Create a branch before committing.")
        print("   Fix: git switch -c chore/<topic>")
        return 1

    if branch in {"main", "master"}:
        print(
            f"[precommit_guard.py]: refusing commit on '{branch}'. Commits must go via a PR branch."
        )
        print("   Fix: git switch -c chore/<topic>")
        return 1

    # Must be based on latest origin/main (stale ref guard).
    # This intentionally fetches to avoid “it passed locally but CI fails”.
    rc, out = sh("git", "fetch", "origin", "main", "--quiet")
    if rc != 0:
        print("[precommit_guard.py]: failed to fetch origin/main; cannot verify branch freshness.")
        print(out)
        return 1

    rc, _ = sh("git", "show-ref", "--verify", "--quiet", "refs/remotes/origin/main")
    if rc != 0:
        print("[precommit_guard.py]: origin/main not found after fetch.")
        return 1

    # Ensure origin/main is an ancestor of HEAD.
    rc, _ = sh("git", "merge-base", "--is-ancestor", "origin/main", "HEAD")
    if rc != 0:
        print("[precommit_guard.py]: your branch is not based on latest origin/main (stale ref).")
        print("   Fix: git rebase origin/main  (or merge origin/main) then re-commit.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

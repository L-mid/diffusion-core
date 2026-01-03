import subprocess
import sys
from pathlib import Path


def test_repo_import_and_docstring_checker_runs():
    """
    Imports and resolves repo route and returns without error.
    """
    # 1) prove the repo/package is importable
    import diffusion_core  # rename if your package name differs

    assert diffusion_core is not None

    # 2) prove the checker script runs without error (help exits 0)
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "tools" / "enforce_docstrings.py"

    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        f"Non-zero exit code: {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}\n"
    )

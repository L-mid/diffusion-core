"""
## Provenance, manifest, and enviroment logging, validation, and writing.

Why: Functions here log and manage runtime information on a run before starting.

Process:    # todo: reorganize this later to inclide the importable
    Logs provanence/runtime information.
    Logged information can be cross checked with validate_provenance_file so expectations met.
    Outputs:
        - meta/pip_freeze.txt
        - meta/manifest.json
        - meta/provenance.json

*Tested by: tests/configs/test_config_runner.py*    # todo: not ideal, will rearrage
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class ManifestEntry:
    """Passed into manifest_obj to json."""

    relpath: str
    bytes: int
    sha256: str


class ProvenanceModel(BaseModel):
    """
    Schema for provenance.json.
    Verifing required keys.
    Integrety checks done in validate_provenance_file() instead.
    """

    schema_version: str = Field(default="v1")

    created_utc: str
    git: dict[str, Any]
    cli: dict[str, Any]
    config: dict[str, Any]
    env: dict[str, Any]
    torch: dict[str, Any]
    rng: dict[str, Any]
    manifest: dict[str, Any]
    fid_stats: dict[str, Any] | None


def _sha256_file(path: Path) -> str:
    """Logs sha256."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    """A runner used to collect messages from the terminal to log fields."""
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    p = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return p.returncode, (p.stdout or "").strip()


def _git_repo_root() -> Path:
    """Logs repo root. Returns RuntimeError if 'not in a repo' (if the command fails)."""
    rc, out = _run(["git", "rev-parse", "--show-toplevel"], cwd=Path.cwd())
    if rc != 0 or not out:
        raise RuntimeError(
            "Provenance requires git metadata, but this does not look like a git repo.\n"
            f"git output:\n{out}"
        )
    return Path(out).resolve()


def _git_sha(repo_root: Path) -> str:
    """Logs git sha."""
    rc, out = _run(["git", "rev-parse", "HEAD"], cwd=repo_root)
    if rc != 0 or not out:
        raise RuntimeError(f"Failed to get git SHA.\n{out}")
    return out.strip()


def _git_dirty(repo_root: Path) -> bool:
    """git diff --quiet exits 1 when dirty, 0 when clean."""
    rc, _ = _run(["git", "diff", "--quiet"], cwd=repo_root)
    return rc != 0


def _git_submodules(repo_root: Path) -> list[dict[str, str]]:
    """Git submodules sha search, logs any found. (useful for using this repo as a submodule)"""
    rc, out = _run(["git", "submodule", "status", "--recursive"], cwd=repo_root)
    if rc != 0 or not out:
        return []
    subs: list[dict[str, str]] = []
    for line in out.splitlines():
        # Format:  <status><sha> <path> (optional stuff...)
        # status is one of ' ', '-', '+', 'U'
        status = line[0]
        rest = line[1:].strip()
        parts = rest.split()
        if len(parts) >= 2:
            sha = parts[0]
            path = parts[1]
            subs.append({"path": path, "sha": sha, "status": status})
    return subs


def _read_python_version_pin(repo_root: Path) -> str | None:
    """
    If present, record the project's pinned Python version.
    """
    p = repo_root / ".python-version"
    if not p.is_file():
        return None
    v = p.read_text(encoding="utf-8").strip()
    return v or None


def _uv_version(repo_root: Path) -> str | None:
    """
    Record uv version if uv in available.
    """
    rc, out = _run(["uv", "--version"], cwd=repo_root)
    if rc == 0 and out:
        return out
    return None


def _capture_freeze_text(repo_root: Path) -> tuple[str, str]:
    """
    Default is uv. Fallback to pip if uv isn't available,
    but records which command produced the snapshot.
    """
    rc, out = _run(["uv", "pip", "freeze"], cwd=repo_root)
    if rc == 0 and out:
        return "uv pip freeze", out

    rc, out = _run([sys.executable, "-m", "pip", "freeze"], cwd=repo_root)
    if rc == 0 and out is not None:
        return f"{sys.executable} -m pip freeze", out

    raise RuntimeError("Failed to capture dependency snapshot via uv or pip.")


def _torch_snapshot() -> dict[str, Any]:
    """
    Log torch version and basic cuda information.
    Does not **enforce** torch, does not **enforce** gpu fields to be filled if unavaliable.
    (For CI speed/testing purposes)
    """
    try:
        import torch  # type: ignore
    except Exception as e:
        return {"installed": False, "error": repr(e)}

    snap: dict[str, Any] = {
        "installed": True,
        "version": getattr(torch, "__version__", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_version": getattr(torch.version, "cuda", None),  # todo
    }

    if torch.cuda.is_available():
        # not enforced
        try:
            snap["gpu_name_0"] = torch.cuda.get_device_name(0)
            snap["gpu_capability_0"] = ".".join(map(str, torch.cuda.get_device_capability(0)))
        except Exception:
            # still marking cuda_available True.
            pass

    return snap


def _iter_manifest_files(run_dir: Path) -> Iterable[Path]:
    """
    Organizes the current manifest logs.
      - config.resolved.yaml
      - logs/metrics.jsonl
      - artifacts/**/*
      - meta/pip_freeze.txt
    Excludes ckpts by default (huge). (Should expand this later).
    """
    root_files = [run_dir / "config.resolved.yaml", run_dir / "logs" / "metrics.jsonl"]
    for p in root_files:
        if p.exists() and p.is_file():
            yield p

    artifacts = run_dir / "artifacts"
    if artifacts.exists():
        for p in artifacts.rglob("*"):
            if p.is_file():
                yield p

    meta_freeze = run_dir / "meta" / "pip_freeze.txt"
    if meta_freeze.exists() and meta_freeze.is_file():
        yield meta_freeze


def write_provenance_bundle(
    *,
    run_dir: Path,
    seed: int,
    argv: Sequence[str],
    fid_stats_path: Path | None = None,
) -> Path:
    """
    Writes:
      meta/pip_freeze.txt
      meta/manifest.json
      meta/provenance.json

    Returns: path to provenance.json
    """
    run_dir = run_dir.resolve()
    meta_dir = (run_dir / "meta").resolve()
    meta_dir.mkdir(parents=True, exist_ok=True)

    repo_root = _git_repo_root()
    lock_path = repo_root / "uv.lock"
    if not lock_path.is_file():
        raise RuntimeError("Missing uv.lock at repo root.Fix:\n  uv lock\n  git add uv.lock\n")

    # --- pip freeze snapshot ---
    freeze_cmd, freeze_text = _capture_freeze_text(repo_root)
    pip_freeze_path = meta_dir / "pip_freeze.txt"
    pip_freeze_path.write_text(freeze_text + "\n", encoding="utf-8")

    # --- manifest ---
    manifest_path = meta_dir / "manifest.json"
    entries: list[ManifestEntry] = []
    for p in _iter_manifest_files(run_dir):
        rel = p.relative_to(run_dir).as_posix()
        entries.append(ManifestEntry(relpath=rel, bytes=p.stat().st_size, sha256=_sha256_file(p)))

    manifest_obj = {
        "run_dir": str(run_dir),
        "generated_utc": datetime.now(tz=UTC).isoformat(),
        "entries": [e.__dict__ for e in entries],
    }
    manifest_path.write_text(
        json.dumps(manifest_obj, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # --- provenance stamp ---
    resolved_cfg = run_dir / "config.resolved.yaml"
    if not resolved_cfg.is_file():
        # fails if no resolved config to log
        raise RuntimeError("Missing config.resolved.yaml. runner must write it before provenance.")

    # FULL DICT (edit here to make changes):
    prov = {
        "schema_version": "v1",
        "created_utc": datetime.now(tz=UTC).isoformat(),
        "git": {
            "sha": _git_sha(repo_root),
            "dirty": _git_dirty(repo_root),
            "submodules": _git_submodules(repo_root),
        },
        "cli": {
            "argv": list(argv),
            "cwd": str(Path.cwd().resolve()),
            # 'recommended' command:
            "recommended": f"{Path(sys.executable).resolve()} -m diffusion_core.cli "
            + " ".join(str(a) for a in list(argv)[1:]),
        },
        "config": {
            "resolved_path": str(resolved_cfg.resolve()),
            "resolved_sha256": _sha256_file(resolved_cfg),
        },
        "env": {
            "python": sys.version.split()[0],
            "python_full": sys.version,
            "python_executable": str(Path(sys.executable).resolve()),
            "python_version_pin": _read_python_version_pin(repo_root),
            "platform": platform.platform(),
            "uv_version": _uv_version(repo_root),
            "pip_freeze": {
                "command": freeze_cmd,
                "path": str(pip_freeze_path.resolve()),
                "sha256": _sha256_file(pip_freeze_path),
            },
            "uv_lock": {
                "path": str(lock_path.resolve()),
                "sha256": _sha256_file(lock_path),
            },
        },
        "torch": _torch_snapshot(),
        "rng": {"seed": int(seed)},
        "manifest": {
            "path": str(manifest_path.resolve()),
            "sha256": _sha256_file(manifest_path),
        },
        "fid_stats": (
            None
            if fid_stats_path is None
            else {"path": str(fid_stats_path.resolve()), "sha256": _sha256_file(fid_stats_path)}
        ),
    }

    prov_path = meta_dir / "provenance.json"
    # Validated before writing:
    validaed = ProvenanceModel.model_validate(prov)
    prov_path.write_text(
        json.dumps(validaed.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return prov_path


def validate_provenance_file(path: Path) -> dict[str, Any]:
    """
    The validation process here:
      - required fields exist + non-empty
      - referenced files exist
      - sha256 fields match the referenced files

    These cross checks are the entire validation check for provanance expectations.

    Returns parsed json dict on success, raises AssertionError on failure.
    """
    path = path.resolve()
    assert path.is_file(), f"Missing provenance file: {path}"
    # Schema validation:
    validated = ProvenanceModel.model_validate_json(path.read_text(encoding="utf-8"))
    data = validated.model_dump(mode="json")

    def req_str(d: dict[str, Any], key: str) -> str:
        """Asserts key `"X"` exists and is not empty."""
        assert key in d, f"Missing key: {key}"
        v = d[key]
        assert isinstance(v, str) and v.strip(), f"Expected non-empty string at {key}"
        return v

    def req_dict(d: dict[str, Any], key: str) -> dict[str, Any]:
        """Asserts dict `"X"` exists."""
        assert key in d and isinstance(d[key], dict), f"Expected dict at {key}"
        return d[key]

    # top-level
    req_str(data, "created_utc")

    git = req_dict(data, "git")
    req_str(git, "sha")

    cli = req_dict(data, "cli")
    assert isinstance(cli.get("argv"), list) and len(cli["argv"]) >= 1, "cli.argv missing/empty"

    cfg = req_dict(data, "config")
    cfg_path = Path(req_str(cfg, "resolved_path"))
    cfg_sha = req_str(cfg, "resolved_sha256")
    assert cfg_path.is_file(), f"resolved config missing: {cfg_path}"
    assert _sha256_file(cfg_path) == cfg_sha, "resolved config sha256 mismatch"

    env = req_dict(data, "env")

    lock = req_dict(env, "uv_lock")
    lock_path = Path(req_str(lock, "path"))
    lock_sha = req_str(lock, "sha256")
    assert lock_path.is_file(), f"uv.lock missing: {lock_path}"
    assert _sha256_file(lock_path) == lock_sha, "uv.lock sha256 mismatch"

    freeze = req_dict(env, "pip_freeze")
    freeze_path = Path(req_str(freeze, "path"))
    freeze_sha = req_str(freeze, "sha256")
    assert freeze_path.is_file(), f"pip freeze file missing: {freeze_path}"
    assert _sha256_file(freeze_path) == freeze_sha, "pip freeze sha256 mismatch"

    mani = req_dict(data, "manifest")
    mani_path = Path(req_str(mani, "path"))
    mani_sha = req_str(mani, "sha256")
    assert mani_path.is_file(), f"manifest missing: {mani_path}"
    assert _sha256_file(mani_path) == mani_sha, "manifest sha256 mismatch"

    rng = req_dict(data, "rng")
    assert isinstance(rng.get("seed"), int), "rng.seed missing/not int"

    # torch block must exist; content can vary if not installed
    torch = req_dict(data, "torch")
    assert isinstance(torch.get("installed"), bool), "torch.installed missing/not bool"

    return data

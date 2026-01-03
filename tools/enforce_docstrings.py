#!/usr/bin/env python3
"""
Enforces docstrings.

Why: aid comprehensibility and cooperation in puplicly used spaces.


Fails (exit 1) if:
- Public surface symbols lack docstrings
- Core modules lack module header docstrings
- ingore method is used without an inline reason

Public API:
- Exports from src/diffusion_core/__init__.py via __all__
- Anything under src/diffusion_core/api/

Core modules: see CORE_MODULES below. (may have updated)


TEMPORARY: manual calls
    # Check staged changes (default):
    python tools/enforce_docstrings.py --staged

    # Check a branch vs main (in CI later)
    python tools/enforce_docstrings.py --range origin/main...HEAD

    Check everything (sanity sweep)
    python tools/enforce_docstrings.py --all

Tested by: test/test_enforces_docstrings.py

"""

from __future__ import annotations

import argparse
import ast
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

TopLevelDef: TypeAlias = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
DocstringNode: TypeAlias = ast.Module | TopLevelDef

ROOT = Path(__file__).resolve().parents[1]


# Configuration
def detect_pkg_dir() -> Path:
    """Scans src root for files."""
    src = ROOT / "src"
    if not src.exists():
        raise SystemExit("Expected a src/ directory at repo root.")
    candidates = []
    for p in src.iterdir():
        if p.is_dir() and (p / "__init__.py").exists():
            candidates.append(p)
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) == 0:
        raise SystemExit(
            "Could not auto-detect package dir under src/. Add src/diffusion_core/__init__.py."
        )
    raise SystemExit(
        f"Multiple packages under src/: {[c.name for c in candidates]}. Pass --pkg explicitly."
    )


def pkg_dir(pkg_name: str | None) -> Path:
    """
    Searches for src root for detect_pkg_dir()
    """
    if pkg_name:
        p = ROOT / "src" / pkg_name
        if not (p / "__init__.py").exists():
            raise SystemExit(f"--pkg={pkg_name} but src/{pkg_name}/__init__.py not found.")
        return p
    return detect_pkg_dir()


ESCAPE_TOKENS = ("noqa: DOC", "docstring-contract: ignore")


# These are REPO-RELATIVE paths.
CORE_MODULES = [
    "src/diffusion_core/config/load.py",
    "src/diffusion_core/runs/layout.py",
    "src/diffusion_core/executor.py",
    "src/diffusion_core/logging.py",
    "src/diffusion_core/eval/metrics.py",
    "src/diffusion_core/eval/metrics/__init__.py",  # might be irrelevent
    "src/diffusion_core/checkpointing.py",
    "src/diffusion_core/determinism.py",
]


# -----------------------------
# Git helpers
# -----------------------------
def run_git(args: list[str]) -> str:
    """Runs git as subprocess"""
    out = subprocess.check_output(["git", *args], cwd=ROOT)
    return out.decode("utf-8", errors="replace").strip()


def changed_files_from_range(diff_range: str) -> list[str]:
    """diff_range example: "origin/main...HEAD"""
    out = run_git(["diff", "--name-only", "--diff-filter=ACMR", diff_range])
    return [line.strip() for line in out.splitlines() if line.strip()]


def changed_files_staged() -> list[str]:
    """Checks staged files only."""
    out = run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    return [line.strip() for line in out.splitlines() if line.strip()]


# -----------------------------
# AST helpers
# -----------------------------
@dataclass
class Violation:
    path: Path
    lineno: int
    message: str


def parse_py(path: Path) -> ast.Module:
    """Parses python files."""
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as e:
        raise SystemExit(f"SyntaxError parsing {path}:{e.lineno}:{e.offset}: {e.msg}") from e

    # ast.parse returns a Module at runtime; make it explicit for the type-checker.
    if not isinstance(tree, ast.Module):
        raise SystemExit(f"Internal error: expected ast.Module from ast.parse for {path}.")
    return tree


def module_docstring_ok(mod: ast.Module) -> bool:
    """Return True if module has a docstring."""
    return bool(ast.get_docstring(mod))


def get_lines(path: Path) -> list[str]:
    """Gets lines using path.read_text"""
    return path.read_text(encoding="utf-8").splitlines()


def has_escape_with_reason(def_line: str) -> bool:
    """
    Accept:
      - # noqa: DOC <reason>
      - # docstring-contract: ignore <reason>
    Require a non-empty reason after the token.
    """
    lower = def_line.lower()
    for tok in ESCAPE_TOKENS:
        idx = lower.find(tok.lower())
        if idx == -1:
            continue
        # require something after token
        after = def_line[idx + len(tok) :].strip()
        return len(after) > 0
    return False


def is_public_name(name: str) -> bool:
    """Ignores all private functions."""
    return not name.startswith("_")


def top_level_defs(mod: ast.Module) -> list[TopLevelDef]:
    """Fetch top-level defs that can have docstrings."""
    out: list[TopLevelDef] = []
    for node in mod.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.append(node)
    return out


def extract_all_list(mod: ast.Module) -> list[str] | None:
    """
    Extract __all__ = ["a", "b"].
    Requires __all__ to be a literal list/tuple of string constants.
    Returns None if __all__ is not defined.
    """
    for node in mod.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "__all__":
                    val = node.value
                    if isinstance(val, (ast.List, ast.Tuple)):
                        items: list[str] = []
                        for elt in val.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                items.append(elt.value)
                            else:
                                raise SystemExit(
                                    "__all__ must be a literal list/tuple of strings "
                                    "(no computed expressions)."
                                )
                        return items
                    raise SystemExit("__all__ must be a literal list/tuple of strings.")
    return None


def import_map_from_init(mod: ast.Module) -> dict[str, tuple[str, str]]:
    """
    Map exported name -> (module_path, original_name)
    Supports:
      from .foo import Bar
      from .foo import Bar as Baz
    """
    mapping: dict[str, tuple[str, str]] = {}
    for node in mod.body:
        if isinstance(node, ast.ImportFrom) and node.level >= 1:
            base = node.module or ""
            # Convert relative import to dotted path relative to package
            for alias in node.names:
                exported = alias.asname or alias.name
                original = alias.name
                mapping[exported] = (base, original)
    return mapping


def resolve_module_file(pkg: Path, dotted: str) -> Path | None:
    """
    dotted like "api.metrics" => src/<pkg>/api/metrics.py or api/metrics/__init__.py
    """
    rel = Path(*dotted.split(".")) if dotted else Path()
    cand1 = pkg / (str(rel) + ".py") if str(rel) else None
    cand2 = pkg / rel / "__init__.py"
    if cand1 and cand1.exists():
        return cand1
    if cand2.exists():
        return cand2
    return None


def find_top_level_symbol(mod: ast.Module, name: str) -> TopLevelDef | None:
    """
    Finds nodes from the top level.
    """
    for node in top_level_defs(mod):
        if node.name == name:
            return node
    return None


# -----------------------------
# Checks
# -----------------------------
def check_api_file(path: Path) -> list[Violation]:
    """
    Checks Public API has doctrings
    (defined as under diffusion_core/__init__.py)
    """
    v: list[Violation] = []
    tree = parse_py(path)
    assert isinstance(tree, ast.Module)
    lines = get_lines(path)

    if not module_docstring_ok(tree):
        v.append(Violation(path, 1, "Missing module docstring (required for public API file)."))

    for node in top_level_defs(tree):
        name = node.name
        if not is_public_name(name):
            continue
        doc = ast.get_docstring(node)
        if doc:
            continue
        def_line = lines[node.lineno - 1] if 1 <= node.lineno <= len(lines) else ""
        if has_escape_with_reason(def_line):
            continue
        v.append(Violation(path, node.lineno, f"Public symbol '{name}' is missing a docstring."))

    return v


def check_core_module(path: Path) -> list[Violation]:
    """Checks for core infrastructure docstrings."""
    v: list[Violation] = []
    tree = parse_py(path)
    if not module_docstring_ok(tree):
        v.append(
            Violation(
                path,
                1,
                "Missing module header docstring (required for core infrastructure module).",
            )
        )
    return v


def check_init_exports(init_path: Path, pkg: Path) -> list[Violation]:
    """Does init actually export its files?"""
    v: list[Violation] = []
    tree = parse_py(init_path)
    if not module_docstring_ok(tree):
        v.append(
            Violation(
                init_path, 1, "Missing module docstring in package __init__.py (public file)."
            )
        )

    exported = extract_all_list(tree)
    if exported is None:
        v.append(Violation(init_path, 1, "__all__ is missing; public files must be explicit."))
        return v

    imports = import_map_from_init(tree)

    for name in exported:
        if name.startswith("_"):
            v.append(Violation(init_path, 1, f"__all__ contains private name '{name}'."))
            continue

        if name not in imports:
            v.append(
                Violation(
                    init_path,
                    1,
                    f"__all__ exports '{name}' but "
                    "it is not imported via a simple 'from .x import {name}' mapping.",
                )
            )
            continue

        mod_dotted, original = imports[name]
        mod_file = resolve_module_file(pkg, mod_dotted)
        if mod_file is None:
            v.append(
                Violation(
                    init_path, 1, f"Cannot resolve module '.{mod_dotted}' for exported '{name}'."
                )
            )
            continue

        mod_tree = parse_py(mod_file)
        sym = find_top_level_symbol(mod_tree, original)
        if sym is None:
            v.append(
                Violation(
                    mod_file, 1, f"Exported '{name}' maps to '{original}' but symbol not found."
                )
            )
            continue

        doc = ast.get_docstring(sym)
        if doc:
            continue

        lines = get_lines(mod_file)
        def_line = lines[sym.lineno - 1] if 1 <= sym.lineno <= len(lines) else ""
        if has_escape_with_reason(def_line):
            continue

        v.append(
            Violation(
                mod_file, sym.lineno, f"Exported public symbol '{name}' is missing a docstring."
            )
        )

    return v


def substitute_pkg(paths: Iterable[str], pkg_name: str) -> list[str]:
    """If names change."""
    return [p.replace("src/diffusion_core/", f"src/{pkg_name}/") for p in paths]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkg", default=None, help="Package directory name under src/, diffusion_core")
    g = ap.add_mutually_exclusive_group(required=False)
    g.add_argument("--staged", action="store_true", help="Check staged changes only (default).")
    g.add_argument(
        "--range", dest="diff_range", default=None, help="Git diff range, e.g. origin/main...HEAD"
    )
    g.add_argument("--all", action="store_true", help="Check all relevant files, not just changed.")
    args = ap.parse_args()

    pkg = pkg_dir(args.pkg)
    pkg_name = pkg.name

    # materialize configured paths
    core_paths = set(substitute_pkg(CORE_MODULES, pkg_name))
    api_dir = pkg / "api"
    init_path = pkg / "__init__.py"

    if args.all:
        changed = []
        # check all possible targets
        candidates: list[Path] = []
        if api_dir.exists():
            candidates.extend([p for p in api_dir.rglob("*.py") if p.is_file()])
        candidates.append(init_path)
        for rel in core_paths:
            p = ROOT / rel
            if p.exists():
                candidates.append(p)
        targets = sorted({p.resolve() for p in candidates})
    else:
        if args.diff_range:
            changed = changed_files_from_range(args.diff_range)
        else:
            changed = changed_files_staged()
        targets = [ROOT / p for p in changed if p.endswith(".py")]

    violations: list[Violation] = []

    # public API: api/ files
    for t in targets:
        try:
            rel = t.relative_to(ROOT).as_posix()
        except ValueError:
            continue

        if rel == init_path.relative_to(ROOT).as_posix():
            violations.extend(check_init_exports(init_path, pkg))
            continue

        if api_dir.exists() and api_dir in t.parents:
            violations.extend(check_api_file(t))
            continue

        if rel in core_paths:
            violations.extend(check_core_module(t))
            continue

    if violations:
        print("\nDocstring enforcement violations:\n")
        for vio in violations:
            rel = vio.path.relative_to(ROOT).as_posix()
            print(f"- {rel}:{vio.lineno}: {vio.message}")
        print(
            "\nFix: add required docstrings, or use an ignore method with a reason "
            "(# noqa: DOC <reason>) and list it in your PR. "
            "\n\nSee `docs/the_docstrings_policy.md` for more information.\n"
        )
        return 1

    print("Docstring contract: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

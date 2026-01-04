"""
CLI Orchestrator.

Tips:
- CLI does only argument parsing + call into a single top-level function per command.
- Sub behavior logic is in library code (`config/`), for ease of unit test + speed.

Call stack:     # todo: might remove this, add command(s) to use in cli proper
  cli.main()
    -> smoke.run_smoke(config_path, run_root, run_id)
      -> config.load_config()            (loading & validation)
      -> config.with_run_root()          (explicit override, no mutation)
      -> run_layout.create_run_dir()     (expected layout)
      -> config.write_resolved_yaml()    (config.resolved.yaml snapshot)


# calls

## from repo root:

python -m diffusion_core.cli smoke --config configs/smoke.yaml --run-root ./.smoke_runs


## A fully stable, repeatable path for CI (no randomness), include a fixed run id:
    python -m diffusion_core.cli smoke \
    --config configs/smoke.yaml \
    --run-root ./.smoke_runs \
    --run-id r0001


In the CLI contract this uses, the command must print:
    RUN_DIR: <path>
    Which must contain expectations.

"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from secrets import token_hex

from diffusion_core.config.runner import run_once


def _default_run_id() -> str:
    """Creates a unique enough run_id for CI/local. Avoids collisions on fast reruns."""
    ts = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    return f"{ts}_{token_hex(3)}"  # e.g., 20260104_081530_a1b2c3


def _cmd_smoke(args: argparse.Namespace) -> int:
    """Organizes run_dir for logging purposes."""
    run_dir = run_once(
        config_path=Path(args.config),
        run_root=Path(args.run_root),
        run_id=str(args.run_id),
    )
    # single line parsable by tests/tools.
    print(f"RUN_DIR: {run_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Builds the parser for organization."""
    p = argparse.ArgumentParser(prog="diffusion-core")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("smoke", help="Fast smoke run that only writes contract outputs.")
    s.add_argument("--config", required=True, help="Path to YAML config.")
    s.add_argument("--run-root", required=True, help="Root directory where runs are created.")
    s.add_argument(
        "--run-id", default=_default_run_id(), help="Run id prefix (defaults to unique UTC id)."
    )
    s.set_defaults(func=_cmd_smoke)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    return int(ns.func(ns))


if __name__ == "__main__":
    raise SystemExit(main())

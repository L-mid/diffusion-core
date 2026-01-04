# Smoke test (canonical)

This repo has a canonical "smoke" run that must stay fast and stable.

## Command

Run from repo root:

python -m diffusion_core.cli smoke --config configs/smoke.yaml --run-root ./.smoke_runs

## Runtime ceiling

- Must complete in **≤ 30 seconds** on CI (ubuntu-latest, CPU).
- If it exceeds this, it is considered a regression (smoke must stay cheap).

## Required outputs

The smoke run must print the run directory path:

RUN_DIR: <path>

That directory must contain (minimum contract):

- config.resolved.yaml
- meta/
- logs/ (and logs/metrics.jsonl)
- ckpts/ (and ckpts/last/)
- artifacts/

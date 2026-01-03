# Run Layout Contract (policy?)
# decide what this doc is for
## Purpose
Every run produces outputs in a **standard, auditable directory layout** so that:
- runs are easy to inspect (by humans),
- tests can validate correctness (by machines),
- tooling (export, resume, dashboards) has stable assumptions.

This document describes the **filesystem contract only** (what exists, where, and minimal required fields). The *contents* of provenance, determinism, and checkpoint format are specified in separate docs. 
## todo: which will be listed here, when done.

## Definitions
- **Run directory**: the root folder for a single execution of `train`/`eval`/etc.
- **run_id**: a unique identifier used as the run directory name (format is implementation-defined, but MUST be unique and stable).
- **Layout version**: a small integer written into provenance so changes are explicit.

## Required directory structure
A valid run directory MUST contain the following entries:
- <run_dir>/
- config.resolved.yaml
- meta/
- provenance.json
- logs/
- metrics.jsonl
- ckpts/
- last/
- artifacts/



Notes:
- `ckpts/last/` may be empty for runs that do not checkpoint yet, but the directory MUST exist.
- `artifacts/` may be empty; it is the only allowed place for human-facing outputs (plots, sample grids, small summaries).
- Additional files/dirs MAY exist, but MUST NOT rename or delete the required entries above.

## `config.resolved.yaml` (required)
- MUST be written at `<run_dir>/config.resolved.yaml`.
- MUST represent the *fully resolved* config actually used by the run (defaults applied, overrides merged).
- MUST be written **once per run** and MUST NOT change after training starts.

## `meta/provenance.json` (required)
MUST exist at `<run_dir>/meta/provenance.json` and MUST be valid JSON.

### Required top-level keys
- `layout_version` (int) — version of this layout contract.
- `run_id` (string)
- `created_at_utc` (string, ISO-8601 UTC, e.g. `2026-01-07T12:34:56Z`)
- `command` (object)
  - `argv` (array of strings) — exact CLI invocation tokens
  - `cwd` (string)
- `git` (object)
  - `repo_sha` (string) — current commit SHA
  - `is_dirty` (bool) — whether there were uncommitted changes
- `env` (object)
  - `python` (string) — e.g. `3.11.7`
  - `platform` (string) — e.g. `Windows-10-10.0.22631-SP0` or similar
  - `torch` (string) — torch version string

Optional keys may be added freely (more will be required by the later provenance spec), but the keys above MUST exist and be non-empty.

## `logs/metrics.jsonl` (required)
MUST exist at `<run_dir>/logs/metrics.jsonl`.

Format rules:
- UTF-8 text file.
- Each line MUST be a standalone JSON object (JSON Lines).
- Each event object MUST include:
  - `step` (int, >= 0)
  - `time` (float, seconds since run start OR unix seconds; choose one and keep consistent)

Other keys are allowed (metric payloads), but `step` and `time` are mandatory for all events.

## `ckpts/` (required)
- `ckpts/last/` MUST exist.
- This folder is reserved for “resume-from-here” checkpoint material.
- If your system also tracks “best”, it MUST be a sibling directory: `ckpts/best/` (optional for now).

No file naming is mandated yet (defined in checkpointing/resume contract), but tests may assert the directory exists.

## `artifacts/` (required)
- MUST exist at `<run_dir>/artifacts/`.
- Only human-facing outputs belong here (plots, sample grids, tiny summaries).
- Any tool that writes images/plots MUST write them under `artifacts/` (not `meta/`, not `logs/`, not top-level).

## Stability rules
- The required paths in this doc are **reserved** and MUST NOT be repurposed.
- Backward-compatible additions are allowed (new files/dirs), but removing or renaming required entries is a contract break and requires bumping `layout_version`.

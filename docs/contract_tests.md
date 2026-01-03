# Contract Tests 

# todo: the purpose of this doc will be to present minimum viable tests/clarify expectations on what's optionally tested, what's not.

## Purpose
These tests enforce the repo’s **non-negotiable contracts**:
- config strictness,
- run directory layout,
- provenance stamping,
- determinism expectations,
- checkpoint/resume continuity.

They are written so a contributor can implement them with **no guessing** about pass/fail.

---

## CT-01 — Strict config rejects unknown keys
**Goal:** Prevent silent typos/drift in YAML configs.

**Setup**
- Provide a minimal valid config file.
- Add an extra unknown key (e.g. `trainer: { unknowntyppo: 1 }` or a top-level `typo_key: 1`).

**Assertion**
- Loading/validating the config MUST fail with a non-zero exit (or raised validation error).
- The error message MUST include the unknown key path (e.g. `trainer.unknowntyppo`).
- No run directory is created as a side-effect of config validation failure.

---

## CT-02 — Smoke run creates run dir + resolved config snapshot
**Goal:** A “run” always produces auditable outputs at predictable paths.

**Setup**
- Execute the smallest possible run mode (e.g. `--steps 2`, tiny batch, CPU allowed).
- Provide a run root (e.g. `runs/`).

**Assertions (filesystem)**
A new run directory MUST be created and MUST contain, at minimum:

- `<run_dir>/config.resolved.yaml` exists and is non-empty
- `<run_dir>/meta/provenance.json` exists and is valid JSON
- `<run_dir>/logs/metrics.jsonl` exists (may be small, but must exist)
- `<run_dir>/ckpts/last/` directory exists
- `<run_dir>/artifacts/` directory exists

**Assertion (resolved config immutability)**
- `config.resolved.yaml` MUST NOT change after run start.
  - Test method: read hash after creation, run finishes, hash unchanged.

---

## CT-03 — Provenance stamp required fields
**Goal:** Runs are attributable to code + command + environment.

**Setup**
- Use the run directory created by CT-02.

**Assertions**
`meta/provenance.json` MUST contain these keys with non-empty values:

- `layout_version` (int)
- `run_id` (string)
- `created_at_utc` (ISO-8601 UTC string ending in `Z`)
- `command.argv` (array of strings, length >= 1)
- `command.cwd` (string)
- `git.repo_sha` (string length >= 7)
- `git.is_dirty` (bool)
- `env.python` (string)
- `env.platform` (string)
- `env.torch` (string)

---

## CT-04 — Determinism contract check (smoke-level)
**Goal:** With identical inputs + seeds, the run is repeatable within a defined tolerance.

**Setup**
Run the same smoke config twice with:
- same `seed`,
- same `config.resolved.yaml`,
- same `git.repo_sha`,
- same device class (CPU-to-CPU or same GPU type).

**Assertions**
- The final training step recorded in `logs/metrics.jsonl` MUST match.
- A stable “summary value” MUST match exactly OR within tolerance:
  - Preferred: a recorded scalar like `train/loss` at the final step.
  - Rule: `abs(a-b) <= 1e-6` (CPU) or `<= 1e-4` (GPU).
- If the project declares “strict determinism” for the chosen backend, then:
  - the final-step scalar MUST match exactly (`a == b`).

(If determinism is not supported for a given backend, the test MUST be skipped with a clear reason, not silently passed.)

---

## CT-05 — Checkpoint/resume continuity check
**Goal:** Resuming from `ckpts/last/` produces the same result as an uninterrupted run.

**Setup**
Perform two runs from the same config+seed:

1) **Reference run:** run for `N` steps uninterrupted.
2) **Resume run:**
   - run for `K` steps (K < N) and ensure a checkpoint is written into `ckpts/last/`
   - resume from that checkpoint and run to `N` total steps

**Assertions**
- Resume run MUST start from step `K` (not from 0).
- Both runs MUST end at step `N`.
- Compare a stable end-of-run scalar (same as CT-04):
  - `abs(a-b) <= 1e-6` (CPU) or `<= 1e-4` (GPU)
  - or exact equality if strict determinism is claimed
- `ckpts/last/` MUST exist in both runs, and the resume run MUST read from it (verify via logs or provenance flag).

---

## Scope notes
These tests enforce **contracts**, not model quality.
They do NOT assert FID improves, loss decreases, or that “best” checkpoints exist.

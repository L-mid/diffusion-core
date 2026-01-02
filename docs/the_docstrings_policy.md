# The Docstrings Policy 

### If you change **public API** or **core infrastructure modules**, you must check:
- **Public API**: objects must have docstrings.
- **Core infrastructure**: modules must have a module header docstring.
- Exceptions for the above are allowed only via an explicit gate, with an explicitly stated reason.

### In general: 
- Docstrings are optional. They are welcome and encouraged on all functions (*especially: module headers, high level orchestrators, and modularized work*).
- Suggested: 1-6 lines explaining what your function does.
- Explanatory comments (#) also encouraged.
- Excessively long docstrings for 'minor/helper/obvious' functions (*use your own judgement*) may be trimmed/edited. 
- Anyone can edit any docstrings in the repo they feel appropriate (subject to PR approval).
---

## Definitions

**Public API** means:

1) Anything exported from `src/diffusion_core/__init__.py` via `__all__`.
2) Anything under `src/diffusion_core/api/` (Here: every non-underscored top-level symbol is 'public').

If it’s not in those places, it is not 'public' (*even if you import it somewhere else*). 

### Core infrastructure modules 
These modules MUST start with a **module header docstring**:

- `src/diffusion_core/config/load.py`
- `src/diffusion_core/runs/layout.py`
- `src/diffusion_core/executor.py`
- `src/diffusion_core/logging.py`
- `src/diffusion_core/eval/metrics.py` (or `src/diffusion_core/eval/metrics/__init__.py`)
- `src/diffusion_core/checkpointing.py`
- `src/diffusion_core/determinism.py`

These files have doc strings enforced using:
- `tools/enforce_docstrings.py`

---

## 'Good docstrings' for public functions:

For every **public class/function**:

### MUST
- **One-line summary**: what does it do?
- **Inputs**: names + types + shapes where relevant (and units if meaningful).
- **Outputs**: type + shape where relevant.
- **Side effects**: file I/O, network, global state, logging, RNG usage.
- **Determinism** notes:
  - does it use randomness?
  - does it accept a generator/seed?
  - does it guarantee reproducibility at some level?
- **Raises** (if it can raise on user input).

### SHOULD (suggested)
- Complexity or performance notes if it can surprise users.
- A tiny usage example for APIs.

**Style**: Loose, plain prose is fine. You may use Google-style blocks as a default:
`Args:`, `Returns:`, `Raises:`, `Notes:`.

---

## Core infrastructure modules

Must start with a module header docstring that answers (if applicable):

- What contract does this module enforce?
- What are the key invariants?
- What files/dirs/formats does it own (run layout, config schema, etc.)?
- How was this file tested? (direct pointers to associated tests encouraged).
- Determinism expectations.
- What NOT to do here (guardrails).

---

## Ingoring docstring requirements:

You can skip docstring requirements in either of the above cases by adding either of these on the **def/class** line:

- `# noqa: DOC <reason>`
- `# enforce-docstrings: ignore <reason>`


Rules:
- A reason is **required**, on the same line.
- This practice is expected to be a temporary measure only.


### In your PR, please paste this at the bottom:
If you added `# noqa: DOC ...`/`# docstring-contract: ignore ...`, please list each one:

- Path: `src/diffusion_core/...` Line: ___  Reason: ___  Follow-up issue/link: ___

---

## Examples:

### Example 1: Bad 
Bad because: no inputs/outputs, no determinism, no side effects mentioned.

> “Does stuff for metrics.”

### Example 1: Good 
Good because: states inputs/outputs, shapes, side effects, determinism.

> “Compute FID from cached Inception stats and a batch of generated images.
> Inputs: images as float32 in [0,1], shape (N,3,H,W). Output: float FID.
> Side effects: reads stats file from disk. Determinism: deterministic given inputs.”

### Example 2: Bad 
Bad because: user knows nearly nothing, or whether it's experimental/reproducible.

> “Run training.”

### Example 2: Good 
Good because: defines what it does, what is expected on use.

> “Run a training loop for K steps writing a run directory under runs/.
> Side effects: creates files, writes metrics.jsonl, may write checkpoints.
> Determinism: reproducible on same machine when deterministic=true and AMP off.”

---

## Enforcement details:

The following docstrings checks are enforced on pre-commit and CI, using: `tools/enforce_docstrings.py`

Flagged blocks:
- Changing public API exports or files under `src/diffusion_core/api/` **and** a docstring is missing.  # is it also unedited?
- Changing a core contract module and it lacks a module header docstring.
- Using an ingore method without a reason on the same line.


### For issues with blocks:
Try an ingore method (*see 'Ingoring docstring requirements' above*). Mention in the **PR and as your ingore reason**: that your docstring is sufficient, but couldn't make the block dissapear.

### For questions/further issues:
Please contact the owner at <midjourney4321@gmail.com> or any name on this repo's `.github/CODEOWNERS` list.

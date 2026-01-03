# SSOT (Single Source of Truth)

This repo has a strict rule: **all documentation has exactly one place where ground truth  can be sourced**.
Other documentation in this repo is allowed to *describe* the truth, but must never become an independent second definition.


> "What is going on/how to do X?"

This page is the index for that question.

---

## SSOT index

### Schema keys SSOT 
**Groud truth lives in:** the **schema definitions** (dataclasses/pydantic models/typed config objects), not necessarily (or accurately) in docs. 

- What are 'schema keys':
  - YAML/JSON config field names
  - allowed enums/choices
  - required vs optional fields
  - default values (when defaults are part of the schema object)

**If docs list config keys/schema:** most docs are validated against the schema via an automated check (see '', below). 
Please keep in mind: this check is not guaranteed for all documentation.  

---

### CLI SSOT (flags, defaults, help text)
**Ground truth lives in:** the **CLI parser definitions** (argument parser/typer/click definitions), including:
- flag names
- default values
- required flags
- help text shown by `--help`

Documentation and docstrings may show examples, but **the parser itself is the source of ground truth**. 

---

### Run layout SSOT (what a run writes to disk)
**Truth lives in:** the **run-writer module behavior** (the code that creates run directories and files).

Docs can explain the structure, but **the run-writer implementation is authoritative**:
- what directories/files exist
- naming rules
- required vs optional outputs
- when files are written (start/end/periodic)
- atomicity guarantees (if any)

---

### Metrics SSOT (metric names, registration, namespaces)
**Truth lives in:** the **metrics registry** (the code registry / plugin registration that defines “what metrics exist”).

Docs may describe metrics and how to enable them, but:
- **metric names must come from the registry**
- **metric output keys must follow registry/namespace rules**
- **any documented metric must be resolvable from the registry**

---

## Hard rule (prevents docs vs code drift)

**Docs may describe SSOT, but must not define it independently without a verification step.**

Concretely:

- If a doc contains a *list* of config keys, metric names, CLI flags, or run-layout requirements,
  then there must exist an automated check that fails when the doc diverges from the SSOT.

Examples of acceptable verification steps:
- a docs-sync test/job that compares documented config keys vs schema keys
- a test that checks documented metric names exist in the metrics registry
- a test that runs `--help` and verifies documented CLI examples don’t drift
- a contract test that asserts the run-writer creates the required files/dirs described in docs

Until the verification exists, docs should **link to the SSOT location** rather than restating it as a definitive list.

NOTE: 
- Certain **experiemental/older/niche** features may not have up to date checks in place. They are typically marked with their non-checked status, but this is *NOT guaranteed*. 

- ***It is highly recomended to cross reference groud truth components to given documentation on such features, and run smokes to see the output/ know what to expect. Please be careful with using these features.***

---

## Fast lookup: "What is going on/how to do X?"

Typical mappings:

- “Is `foo:` a valid config key?” → **schema definitions**
- “What is the default for `--steps`?” → **CLI parser**
- “Should a run have `meta/` or `logs/`?” → **run-writer**
- “Is `fid` a valid metric name?” → **metrics registry**

If an answer isn't clear in ~10 seconds, this page is missing an entry or the SSOT is unclear.
Best practice is to update/add this page immediately when introducing a new change/feature.

---

## Change protocol (what to do when SSOT changes)

Whenever you change an SSOT:
1. Change the SSOT implementation (schema/CLI/run-writer/registry).
2. Update docs *to describe the new truth* (this file and any relevant contract docs).
3. Add or update the verification step so drift becomes a failing check.

SSOT changes are monitored. PRs containing changes to them:
- A): without modifying/adding suitible respecive documents, and/or
- B): containing many changes to multiple files in a single PR,

Are very likely to be rejected.

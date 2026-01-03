# Debugging suggestions

To constribute fixes/refactors, consider the below.

- This repo is designed so that: if CI would fail, pre-commit will fail locally. You may rely on `pre-commit run -a` to ensure you're ok with CI enforcements & a larger suite of light tests.


- After any bugfix, add the minimal regression test immediately where appropriate.      # more on the specific test suite later


## Enviroment (see Enviroment.md or what we call it later for this repos doc for Reproducibility/Env set up)


## Reproduce a failing test 

Run a single test by node id:
- `python -m pytest -q tests/<file>.py::test_name`

Run only fast suite (pre-commit uses this):
- `python -m pytest -q -m "not slow and not integration"`

Run all tests: 
- `pytest`

For tests of various marker level:
- `tbd`


# deleate this
## VS Code specifics: this testing configuration

1) Open the Testing panel (beaker icon).
2) Find the failing test.
3) Click the "Debug Test" button (or right-click → Debug Test).
4) Set breakpoints in the code under test and rerun.

Tip: You can also drop `breakpoint()` in the failing path and rerun the test.

## After fix, add a minimal regression test immediately

Suggested process:
1) Write a regression test that fails on the bug (or would have failed).
2) Fix the bug.
3) Re-run only that test node id.
4) Re-run `pre-commit run -a` before pushing.

Why: it prevents the same bug from returning in a later refactor. 

## Levels of fixes:
Suggested: in your PR, mention which of the following you did to test your implementation:
- 1): Unit tests: Run the entire suite for that unit.

- 2): Integration tests: Run the integration suite relevent to your change.

- 3): Full run tests/many changes: Run E2E smoke tests. 

- CUDA: (For components using CUDA/device logic): Run at your level of fix **with** cuda enabled.

Tip: if unsure, run the largest suite you feasibly can as a last check before pushing. 
(This is typically what a reviwer will do to sanity check your changes)
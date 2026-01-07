# Environment (local dev)

This repo uses a local virtual environment at `./.venv` and installs the project in editable mode. 

## Prerequisites

- Python >= 3.11
- Git

From the repo root, you should be able to run:
- `python --version`
- `git --version`

*Tip: `./.venv` is gitingored (only persists locally). Whenever cloning this repo, please always install again using the same instructions.*


For exact Notebook/kaggle repoducibility, secrects integration, or lfs/filepointing installation examples, see: # todo

---

## One-time setups 

Please note whether you're on Windows Powershell, or macOS/Linux/WSL/Git Bash: 

# todo: update to recent and test these installations properly
### macOS/Linux/WSL/Git Bash setup:
```bash
# confirmed to run, but on a weird windows using git bash way
py -3.11 -m venv .venv
source .venv/Scripts/activate

python -m pip install -U pip setuptools wheel
python -m pip install -e ".[dev]"

pre-commit install
python -m pytest

```

## update these to current
### Windows PowerShell setup:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"

pre-commit install
python -m pytest

```


### Usage:

#### MacOS/Linux/WSL/Git Bash:

```bash
source .venv/bin/activate

```

#### Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1

```


Quick verification install worked correctly:

```bash     
# bash used in this snippet.
# however powershell works for the below commands too!


# Run tests:
python -m pytest

# Run a CLI smoke command:
python -m diffusion_core.cli smoke --config configs/smoke.yaml --run-root ./.smoke_runs


# tooling checks:
ruff check .
ruff format .
pyright

# A local documentation preview of this repo (MkDocs based):
mkdocs serve

```



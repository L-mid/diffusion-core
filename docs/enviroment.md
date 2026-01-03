# PLACEHOLDER:

### will be covered in more detail, for now setup is:

##### do in bash

python -m venv .venv
# activate the venv
python -m pip install -U pip
python -m pip install -e ".[dev]"
pre-commit install
pre-commit run -a 
# uv implementation (merge with enviroment/quickstart later)

With uv, changing the environment mostly means changing the project’s declared dependencies (in pyproject.toml) and then letting uv update uv.lock + sync .venv to match.


## a few options:

### add something:
uv add numpy
uv lock
uv sync --locked
git add pyproject.toml uv.lock
git commit -m "deps: add numpy"

(can also do manually in the pyproject but not ideal)


## add a dev only tool (pytest plugin, formatter, etc):
Example: add pytest-xdist 

(under dependency groups):
uv add --group dev pytest-xdist
uv lock
uv sync --locked
git add pyproject.toml uv.lock
git commit -m "dev: add pytest-xdist"


## Add a new group (docs, ml, etc.)

[dependency-groups]
dev = [ ... ]
docs = ["mkdocs>=1.5", "mkdocs-material>=9"]
ml = ["torch==...", "torchvision==..."]

uv sync --group dev --group docs --locked
# or:
uv sync --all-groups --locked


## (If you don’t pass groups, uv installs the default set for the project; recommended to be explicit in CI.)


Bump constraints intentionally

Edit pyproject.toml (e.g., raise minimum versions), then:


uv lock
uv sync --locked
set dotenv-load

mod remote

[private]
default:
    @just --list --list-submodules

# Serve the API with reload
serve port="8001":
    uv run uvicorn sully.main:app --reload --port {{ port }}

# Fetch the due sources into the local database, e.g. `just fetch dgcl --force`
fetch *args:
    uv run sully fetch {{ args }}

# Render a fiche to PDF, e.g. `just fiche 35238 -c identite,carto`
fiche *args:
    uv run sully fiche {{ args }}

lint:
    uv run ruff check sully
    uv run ruff format --check sully

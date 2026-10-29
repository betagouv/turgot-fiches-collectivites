set dotenv-load

mod dokku
mod scalingo

[private]
default:
    @just --list --list-submodules

# Serve the API with reload
serve port="8001":
    uv run uvicorn fico.main:app --reload --port {{ port }}

# Fetch the due sources into the local database, e.g. `just fetch dgcl --force`
fetch *args:
    uv run fico fetch {{ args }}

# Render a fiche to PDF, e.g. `just fiche 35238 -c identite,financements.*`
fiche *args:
    uv run fico fiche {{ args }}

# Run the tests, e.g. `just test --update-references` to rewrite the expected outputs
test *args:
    uv run pytest {{ args }}

lint:
    uv run ruff check fico
    uv run ruff format --check fico

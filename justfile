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

# Bundle the components' script and styles for the project's version, set with `uv version`
assets:
    #!/usr/bin/env bash
    set -euo pipefail
    version=$(uv version --short)
    script=fico/assets/fico.$version.js
    style=fico/assets/fico.$version.css
    # Clients pin a committed version's integrity: rewriting it would break them.
    if git ls-files --error-unmatch "$script" "$style" &>/dev/null; then
        echo "La version $version est déjà commitée : passe à la suivante avec uv version." >&2
        exit 1
    fi
    npx --yes esbuild@0.25.0 fico/components/fiche.js --bundle --format=esm --outfile="$script"
    cp fico/components/fico.css "$style"
    for file in "$script" "$style"; do
        echo "$file sha384-$(openssl dgst -sha384 -binary "$file" | base64 -w0)"
    done

# Run the tests, e.g. `just test --update-references` to rewrite the expected outputs
test *args:
    uv run pytest {{ args }}

lint:
    uv run ruff check fico
    uv run ruff format --check fico

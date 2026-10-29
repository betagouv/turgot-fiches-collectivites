set dotenv-load

host := env("FICO_HOST", "")
app := env("FICO_APP", "fico")
database := app + "-db"
dokku := "ssh dokku@" + host

[private]
default:
    @just --list dokku

[private]
check-host:
    @test -n "{{ host }}" || (echo "Set FICO_HOST=server" && exit 1)

# Create the app and its database, and copy the API token from .env; safe to rerun
setup: check-host
    {{ dokku }} apps:exists {{ app }} 2>/dev/null || {{ dokku }} apps:create {{ app }}
    {{ dokku }} buildpacks:set {{ app }} https://github.com/heroku/heroku-buildpack-python
    {{ dokku }} postgres:exists {{ database }} 2>/dev/null || {{ dokku }} postgres:create {{ database }}
    {{ dokku }} postgres:linked {{ database }} {{ app }} 2>/dev/null || {{ dokku }} postgres:link {{ database }} {{ app }}
    @{{ dokku }} config:set --no-restart {{ app }} API_COLLECTIVITES_TOKEN="$API_COLLECTIVITES_TOKEN" > /dev/null

# Deploy the current commit; uncommitted changes stay behind
deploy: check-host
    git push dokku@{{ host }}:{{ app }} HEAD:master

# Serve the app over HTTPS with a Let's Encrypt certificate; needs a first deploy
https: check-host
    {{ dokku }} letsencrypt:enable {{ app }}

# Run `fico fetch` in a detached container, e.g. `just dokku fetch api-collectivites --force`
fetch *args: check-host
    {{ dokku }} run:detached {{ app }} python -m fico.cli fetch {{ args }}

# Follow the output of the fetch containers
logs: check-host
    {{ dokku }} run:logs {{ app }} -t

# List the running fetch containers
status: check-host
    {{ dokku }} run:list {{ app }}

# Replace the local database with the server's
pull: check-host
    mkdir -p tmp
    {{ dokku }} postgres:export {{ database }} > tmp/{{ database }}.dump
    pg_restore --clean --if-exists --no-owner --no-acl -d "$DATABASE_URL" tmp/{{ database }}.dump

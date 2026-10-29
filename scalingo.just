set dotenv-load

app := env("FICO_APP", "turgot-fico")
region := env("SCALINGO_REGION", "osc-secnum-fr1")
scalingo := "scalingo --region " + region + " --app " + app

[private]
default:
    @just --list scalingo

# Create the app and its database, and copy the API token from .env; safe to rerun
setup:
    scalingo --region {{ region }} apps | grep -qw {{ app }} || scalingo --region {{ region }} create {{ app }}
    {{ scalingo }} addons | grep -q postgresql || {{ scalingo }} addons-add postgresql postgresql-starter-512
    @{{ scalingo }} env-set API_COLLECTIVITES_TOKEN="$API_COLLECTIVITES_TOKEN" > /dev/null

# Deploy the current commit; uncommitted changes stay behind
deploy:
    git push git@ssh.{{ region }}.scalingo.com:{{ app }}.git HEAD:master

# Run `fico fetch` in a detached container, e.g. `just scalingo fetch api-collectivites --force`
fetch *args:
    {{ scalingo }} run --detached -- python -m fico.cli fetch {{ args }}

# Follow the app's output, the fetch containers included
logs:
    {{ scalingo }} logs --follow

# List the running containers
status:
    {{ scalingo }} ps

# Replace the local database with the server's latest backup
pull:
    mkdir -p tmp
    {{ scalingo }} --addon postgresql backups-download --output tmp/{{ app }}-db.tar.gz
    tar -xzOf tmp/{{ app }}-db.tar.gz | pg_restore --clean --if-exists --no-owner --no-acl -d "$DATABASE_URL"

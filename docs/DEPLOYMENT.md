# Persistent local hosting

This is a self-hosting preview, not a hosted service. Six-language work and public HTTPS acceptance remain. Use Python 3.12 on Linux or Docker. The bounded PDF checker requires POSIX resource limits.

```sh
python3 scripts/setup.py
docker compose up --build -d
```

Setup creates a private `.env` with a random `APPROVAL_OWNER_KEY` and refuses to overwrite existing configuration. Read that file locally to unlock the workspace. Do not share or commit it. The Compose service binds only `127.0.0.1:8093`; open http://127.0.0.1:8093. Invitations using localhost only work on that computer.

The service runs Waitress as UID 10001, with a read-only container filesystem, writable `/data` named volume, temporary `/tmp`, no extra capabilities and no-new-privileges. Database contents survive container replacement. Never run `docker compose down -v` unless intentionally deleting all files and review records.

For access from other computers, separately configure a trusted HTTPS reverse proxy, request limits and host firewall. Generate invitations using that final HTTPS origin. Public hosting is not configured or verified here. A reviewer invitation is a bearer credential: anyone holding it can act as that reviewer. Store owner credentials separately from data backups.

## Backup and restore

Stop writes before copying a database out of a container:

```sh
docker compose stop
mkdir -m 700 backup
container=$(docker compose ps -aq approval-folio)
docker cp "$container:/data/approval.sqlite3" backup/source.sqlite3
chmod 600 backup/source.sqlite3
python3 scripts/backup.py backup/source.sqlite3 backup/approval.sqlite3
docker compose start
```

The script creates a consistent SQLite backup with mode 0600, runs integrity checking, and refuses to overwrite a destination. Protect both copies: they contain uploaded files, review notes and access records. The SQLite backup API also supports a live local database; copying a live database file directly does not.

Restore into a new empty volume while the destination service is stopped. Copy the backup to `/data/approval.sqlite3`, set its owner to UID/GID 10001 and permissions 0600, and set the data directory owner to 10001. Start the service with the original owner key. Check exact file downloads, history and current decisions before accepting new writes. Never restore over a running database or the sole original backup.

## Reproduce container acceptance

```sh
docker build -t approval-folio-acceptance:local .
python scripts/container_acceptance.py
```

Run the test using the environment with `requirements.txt` installed. It uses disposable volumes and containers, checks PDF parsing within the container, restart, private backup, restore to a new volume, new-version reset, stale decision rejection and revoked access, then removes its test resources. An optional build secret `pip_ca` may supply a trusted CA bundle in environments with a private certificate authority; TLS verification stays enabled.

# JobPulse database migrations

Create or safely upgrade the local/demo database with:

```powershell
python -m src.db.init_db
```

This command handles empty and already-versioned databases. For a pre-Alembic
SQLite database it validates the immutable M0 physical schema, creates a
consistent backup, stamps `d8cf04cfe08c`, and upgrades to head. Unknown or
drifted schemas fail closed before any mutation.

Stop every process that can read or write the SQLite file before running a
migration. The local launcher skips migration when it detects a running
backend. Existing backup paths are never overwritten.

File-based SQLite migrations hold `<database>.migration.lock` from the first
revision read through backup, upgrade/restore, and final head verification.
Concurrent launchers therefore serialize instead of restoring stale backups.

Use `python -m alembic upgrade head` directly only for an empty or already
versioned database. Never stamp an unknown schema by hand.

For isolated Alembic checks, set `ALEMBIC_DATABASE_URL` to a temporary
database. Programmatic migration calls pass an explicit URL that takes
precedence over this environment variable.

The current container startup contract assumes one application replica. A
multi-replica deployment must run migrations once in a dedicated release job
before application replicas start.

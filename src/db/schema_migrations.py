"""Safe schema bootstrap for local/demo databases.

Pre-Alembic SQLite databases are only stamped after their physical schema is
proven to match the immutable M0 baseline. A consistent backup is created
before any existing database is upgraded and restored automatically if the
migration fails.
"""

from __future__ import annotations

from contextlib import closing, nullcontext
from dataclasses import dataclass
from datetime import UTC, datetime
import errno
from functools import lru_cache
import os
from pathlib import Path
import re
import sqlite3
from tempfile import TemporaryDirectory
import time

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url


BASELINE_REVISION = "d8cf04cfe08c"
PROJECT_ROOT = Path(__file__).resolve().parents[2]

BASELINE_COLUMNS = {
    "application": (
        "id", "job_id", "status", "applied_at", "updated_at", "notes"
    ),
    "application_event": (
        "id", "application_id", "event_type", "from_status", "to_status",
        "round", "scheduled_at", "occurred_at", "is_correction",
        "correction_reason", "note",
    ),
    "company": ("id", "name", "industry", "category", "website"),
    "crawl_log": (
        "id", "source", "status", "count", "error", "started_at", "finished_at"
    ),
    "job": (
        "id", "company", "title", "location", "salary", "jd", "requirement",
        "apply_url", "source", "source_url", "job_category", "graduation_year",
        "education", "experience", "collected_at", "published_at", "deadline",
        "last_verified_at", "is_valid", "is_intern", "is_fresh", "status",
    ),
    "subscription": ("id", "keyword", "company", "location", "created_at"),
    "user_job_action": (
        "id", "job_id", "action_type", "created_at", "ended_at"
    ),
}

_IN_LIST_PATTERN = re.compile(r"\b(not\s+in|in)\s*\(([^()]*)\)", re.IGNORECASE)
_STRING_LITERAL_PATTERN = re.compile(r"('(?:''|[^'])*')")


class SchemaMismatchError(RuntimeError):
    """Raised before mutation when an unversioned schema is not the M0 baseline."""


class MigrationLockTimeoutError(RuntimeError):
    """Raised when another process keeps the SQLite migration lock too long."""


@dataclass(frozen=True)
class MigrationResult:
    action: str
    previous_revision: str | None
    current_revision: str
    backup_path: Path | None = None


class _SQLiteMigrationLock:
    """Small cross-platform advisory lock held for the whole migration."""

    def __init__(self, path: Path, *, timeout_seconds: float = 60.0):
        self.path = path
        self.timeout_seconds = timeout_seconds
        self._handle = None

    def _try_acquire(self) -> None:
        assert self._handle is not None
        self._handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(self._handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(
                self._handle.fileno(),
                fcntl.LOCK_EX | fcntl.LOCK_NB,
            )

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a+b")
        if self.path.stat().st_size == 0:
            self._handle.write(b"\0")
            self._handle.flush()

        deadline = time.monotonic() + self.timeout_seconds
        contention_errors = {errno.EACCES, errno.EAGAIN, errno.EDEADLK}
        try:
            while True:
                try:
                    self._try_acquire()
                    return self
                except OSError as exc:
                    if exc.errno not in contention_errors:
                        raise
                    if time.monotonic() >= deadline:
                        raise MigrationLockTimeoutError(
                            "Another process is migrating this SQLite database; "
                            f"timed out waiting for {self.path}."
                        ) from exc
                    time.sleep(0.05)
        except BaseException:
            self._handle.close()
            self._handle = None
            raise

    def __exit__(self, _exc_type, _exc_value, _traceback):
        assert self._handle is not None
        try:
            self._handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        finally:
            self._handle.close()
            self._handle = None


def _alembic_config(database_url: str) -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    config.attributes["database_url"] = database_url
    return config


def _sqlite_path(database_url: str) -> Path:
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or not url.database:
        raise SchemaMismatchError(
            "Automatic pre-Alembic stamping is only supported for file-based SQLite."
        )
    if url.database == ":memory:":
        raise SchemaMismatchError("In-memory SQLite cannot be backed up for migration.")
    path = Path(url.database)
    return path if path.is_absolute() else (PROJECT_ROOT / path).resolve()


def _normalized_database_url(database_url: str) -> str:
    url = make_url(database_url)
    if (
        url.get_backend_name() == "sqlite"
        and url.database
        and url.database != ":memory:"
    ):
        path = Path(url.database)
        if not path.is_absolute():
            path = (PROJECT_ROOT / path).resolve()
        return url.set(database=path.as_posix()).render_as_string(
            hide_password=False
        )
    return database_url


def _canonical_sql(value) -> str | None:
    if value is None:
        return None
    sql = str(value).strip()

    def _normalize_unquoted(segment: str) -> str:
        segment = re.sub(r"\s+", " ", segment.lower())
        return re.sub(r"\s*([(),=<>])\s*", r"\1", segment)

    parts = _STRING_LITERAL_PATTERN.split(sql)
    sql = "".join(
        part if index % 2 else _normalize_unquoted(part)
        for index, part in enumerate(parts)
    )

    def _sort_in_values(match: re.Match) -> str:
        operator = re.sub(r"\s+", " ", match.group(1).lower())
        values = sorted(
            item.strip()
            for item in match.group(2).split(",")
        )
        return f"{operator}({','.join(values)})"

    sql = _IN_LIST_PATTERN.sub(_sort_in_values, sql)
    return sql.strip()


def _schema_fingerprint(database_url: str) -> dict:
    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        with engine.connect() as connection:
            sqlite_objects = tuple(
                (
                    row.type,
                    row.name,
                    row.tbl_name,
                    _canonical_sql(row.sql),
                )
                for row in connection.execute(
                    text(
                        "SELECT type, name, tbl_name, sql FROM sqlite_master "
                        "WHERE type IN ('table', 'index', 'view', 'trigger') "
                        "AND name NOT LIKE 'sqlite_%' "
                        "AND name != 'alembic_version' "
                        "ORDER BY type, name"
                    )
                ).all()
            )
        table_names = sorted(
            set(inspector.get_table_names()) - {"alembic_version"}
        )
        tables = {}
        for table in table_names:
            columns = tuple(
                (
                    column["name"],
                    column["type"]._type_affinity.__name__,
                    bool(column["nullable"]),
                    _canonical_sql(column.get("default")),
                    int(column.get("primary_key") or 0),
                )
                for column in inspector.get_columns(table)
            )
            indexes = tuple(
                sorted(
                    (
                        index["name"],
                        tuple(index["column_names"]),
                        bool(index["unique"]),
                        _canonical_sql(
                            index.get("dialect_options", {}).get("sqlite_where")
                        ),
                    )
                    for index in inspector.get_indexes(table)
                )
            )
            checks = tuple(
                sorted(
                    (
                        check.get("name") or "",
                        _canonical_sql(check.get("sqltext")),
                    )
                    for check in inspector.get_check_constraints(table)
                )
            )
            foreign_keys = tuple(
                sorted(
                    (
                        foreign_key.get("name") or "",
                        tuple(foreign_key["constrained_columns"]),
                        foreign_key.get("referred_schema") or "",
                        foreign_key["referred_table"],
                        tuple(foreign_key["referred_columns"]),
                        tuple(sorted(foreign_key.get("options", {}).items())),
                    )
                    for foreign_key in inspector.get_foreign_keys(table)
                )
            )
            uniques = tuple(
                sorted(
                    (
                        constraint.get("name") or "",
                        tuple(constraint["column_names"]),
                    )
                    for constraint in inspector.get_unique_constraints(table)
                )
            )
            primary_key = inspector.get_pk_constraint(table)
            tables[table] = {
                "columns": columns,
                "indexes": indexes,
                "checks": checks,
                "foreign_keys": foreign_keys,
                "uniques": uniques,
                "primary_key": (
                    primary_key.get("name") or "",
                    tuple(primary_key.get("constrained_columns") or ()),
                ),
            }

        return {
            "table_names": tuple(table_names),
            "views": tuple(sorted(inspector.get_view_names())),
            # SQLAlchemy's inspector intentionally omits some SQLite semantics,
            # including index COLLATE / sort order and table STRICT / WITHOUT
            # ROWID clauses. The canonical sqlite_master DDL closes those gaps.
            "sqlite_objects": sqlite_objects,
            "tables": tables,
        }
    finally:
        engine.dispose()


@lru_cache(maxsize=1)
def _baseline_schema_fingerprint() -> dict:
    with TemporaryDirectory(prefix="jobpulse-m0-baseline-") as temp_dir:
        database_path = Path(temp_dir) / "baseline.db"
        database_url = f"sqlite:///{database_path.as_posix()}"
        command.upgrade(_alembic_config(database_url), BASELINE_REVISION)
        return _schema_fingerprint(database_url)


def _schema_differences(database_url: str) -> list[str]:
    expected = _baseline_schema_fingerprint()
    actual = _schema_fingerprint(database_url)
    differences: list[str] = []
    for key in ("table_names", "views", "sqlite_objects"):
        if actual[key] != expected[key]:
            differences.append(f"{key} differs from the immutable M0 baseline")
    for table in sorted(set(expected["tables"]) | set(actual["tables"])):
        if actual["tables"].get(table) != expected["tables"].get(table):
            differences.append(
                f"{table} definition differs from the immutable M0 baseline"
            )
    return differences


def assert_pre_alembic_baseline(database_url: str) -> None:
    """Fail closed unless an unversioned database exactly matches M0."""

    differences = _schema_differences(database_url)
    if differences:
        raise SchemaMismatchError(
            "Unversioned database does not match the M0 baseline; no changes made. "
            + " | ".join(differences)
        )


def _backup_sqlite(source: Path, destination: Path) -> None:
    source = source.resolve()
    destination = destination.resolve()
    if source == destination:
        raise ValueError("Backup path must differ from the database path.")
    if not source.is_file():
        raise FileNotFoundError(f"SQLite source database does not exist: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(
            destination,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
    except FileExistsError as exc:
        raise FileExistsError(
            "Backup destination already exists; refusing to overwrite: "
            f"{destination}"
        ) from exc
    else:
        os.close(descriptor)
    try:
        with closing(sqlite3.connect(source)) as source_connection:
            with closing(sqlite3.connect(destination)) as destination_connection:
                source_connection.backup(destination_connection)
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def _restore_sqlite(source: Path, destination: Path) -> None:
    """Restore a migration backup while explicitly releasing Windows handles."""

    source = source.resolve()
    destination = destination.resolve()
    if source == destination:
        raise ValueError("Backup path must differ from the database path.")
    if not source.is_file():
        raise FileNotFoundError(f"SQLite backup does not exist: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(source)) as source_connection:
        with closing(sqlite3.connect(destination)) as destination_connection:
            source_connection.backup(destination_connection)


def _current_revision(database_url: str) -> tuple[bool, str | None, set[str]]:
    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        if "alembic_version" not in tables:
            return False, None, tables
        with engine.connect() as connection:
            revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one_or_none()
        return True, revision, tables - {"alembic_version"}
    finally:
        engine.dispose()


def _upgrade_to_head(config: Config) -> None:
    command.upgrade(config, "head")


def upgrade_database(
    database_url: str,
    *,
    backup_path: Path | None = None,
) -> MigrationResult:
    """Upgrade a database to head without blindly stamping unknown schemas."""

    database_url = _normalized_database_url(database_url)
    config = _alembic_config(database_url)
    head = ScriptDirectory.from_config(config).get_current_head()
    is_sqlite = make_url(database_url).get_backend_name() == "sqlite"
    sqlite_path = _sqlite_path(database_url) if is_sqlite else None
    if sqlite_path is not None:
        lock_path = Path(f"{sqlite_path}.migration.lock")
        migration_lock = _SQLiteMigrationLock(lock_path)
    else:
        migration_lock = nullcontext()

    # The lock must cover the first revision read, backup, migration, optional
    # restore, and final verification. Otherwise a losing process could restore
    # its stale backup after another process has already reached head.
    with migration_lock:
        versioned, revision, tables = _current_revision(database_url)
        if versioned and revision == head:
            return MigrationResult("already_current", revision, head)

        created_backup: Path | None = None
        if tables:
            if not versioned:
                if not is_sqlite:
                    raise SchemaMismatchError(
                        "Unversioned non-SQLite databases require an explicit, "
                        "operator-reviewed baseline migration."
                    )
                assert_pre_alembic_baseline(database_url)
            if is_sqlite:
                assert sqlite_path is not None
                timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
                created_backup = backup_path or sqlite_path.with_name(
                    f"{sqlite_path.name}.pre-migration-{timestamp}.bak"
                )
                _backup_sqlite(sqlite_path, created_backup)

        try:
            if tables and not versioned:
                command.stamp(config, BASELINE_REVISION)
                revision = BASELINE_REVISION
            _upgrade_to_head(config)
            final_versioned, final_revision, _ = _current_revision(database_url)
            if not final_versioned or final_revision != head:
                raise RuntimeError(
                    "Database migration returned without reaching the expected "
                    f"revision {head}; found {final_revision!r}."
                )
        except Exception:
            if created_backup is not None:
                assert sqlite_path is not None
                _restore_sqlite(created_backup, sqlite_path)
            raise

        action = "created" if not tables else "upgraded"
        return MigrationResult(action, revision, head, created_backup)

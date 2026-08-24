"""Alembic upgrade/downgrade contracts for the M1 public data model."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import multiprocessing
from pathlib import Path
from queue import Empty
import shutil
from threading import Event, Lock

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from src.db.schema_migrations import (
    BASELINE_COLUMNS,
    SchemaMismatchError,
    upgrade_database,
)
import src.db.schema_migrations as schema_migrations


ROOT = Path(__file__).resolve().parents[1]
BASELINE_REVISION = "d8cf04cfe08c"


def _upgrade_in_child_process(database_url, started, result_queue):
    """Picklable Windows-spawn worker for the cross-process lock contract."""

    started.set()
    try:
        result = upgrade_database(database_url)
    except BaseException as exc:  # pragma: no cover - surfaced in parent
        result_queue.put(("error", repr(exc)))
    else:
        result_queue.put((result.action, result.current_revision))


def _alembic_config(database_path: Path) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.set_main_option(
        "sqlalchemy.url",
        f"sqlite:///{database_path.as_posix()}",
    )
    return config


def test_m1_migration_preserves_existing_company_and_is_repeatable(tmp_path):
    database_path = tmp_path / "migration.db"
    config = _alembic_config(database_path)

    command.upgrade(config, BASELINE_REVISION)
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO company (name, industry, category, website) "
                "VALUES (:name, :industry, :category, :website)"
            ),
            {
                "name": "既有公司",
                "industry": "制造",
                "category": "央国企",
                "website": "https://example.com",
            },
        )
    engine.dispose()

    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    inspector = inspect(engine)
    assert {
        "recruitment_campaign",
        "observed_position_ref",
        "source_snapshot",
        "company_change_event",
    }.issubset(inspector.get_table_names())
    assert {"registry_id", "aliases", "status", "first_verified_at"}.issubset(
        {column["name"] for column in inspector.get_columns("company")}
    )
    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT name, aliases, status FROM company WHERE name = '既有公司'")
        ).one()
    assert row.name == "既有公司"
    assert json.loads(row.aliases) == []
    assert row.status == "candidate"
    engine.dispose()

    command.check(config)
    command.downgrade(config, BASELINE_REVISION)
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    inspector = inspect(engine)
    assert "source_snapshot" not in inspector.get_table_names()
    assert "registry_id" not in {
        column["name"] for column in inspector.get_columns("company")
    }
    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT name FROM company WHERE name = '既有公司'")
        ).scalar_one() == "既有公司"
    engine.dispose()

    command.upgrade(config, "head")
    command.check(config)


def test_known_pre_alembic_database_is_backed_up_stamped_and_upgraded(tmp_path):
    database_path = tmp_path / "pre-alembic.db"
    config = _alembic_config(database_path)
    command.upgrade(config, BASELINE_REVISION)

    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO company (name, industry) "
                "VALUES ('旧库公司', '制造')"
            )
        )
        connection.execute(text("DROP TABLE alembic_version"))
    engine.dispose()

    backup_path = tmp_path / "pre-alembic.backup.db"
    result = upgrade_database(
        f"sqlite:///{database_path.as_posix()}",
        backup_path=backup_path,
    )

    assert result.action == "upgraded"
    assert result.previous_revision == BASELINE_REVISION
    assert result.backup_path == backup_path
    assert backup_path.exists()
    # sqlite3.Connection context managers do not close handles on Windows.
    # A round-trip rename proves the migration helper released the backup.
    released_path = backup_path.with_name("released.backup.db")
    backup_path.rename(released_path)
    released_path.rename(backup_path)

    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT name FROM company WHERE name = '旧库公司'")
        ).scalar_one() == "旧库公司"
        assert connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one() == "8418f8d1585a"
    assert "source_snapshot" in inspect(engine).get_table_names()
    engine.dispose()


def test_unknown_unversioned_schema_is_rejected_without_mutation(tmp_path):
    database_path = tmp_path / "drifted.db"
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE unexpected (id INTEGER PRIMARY KEY)"))
    engine.dispose()

    with pytest.raises(SchemaMismatchError):
        upgrade_database(f"sqlite:///{database_path.as_posix()}")

    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    assert inspect(engine).get_table_names() == ["unexpected"]
    engine.dispose()


def test_pre_alembic_guard_rejects_partial_index_predicate_drift(tmp_path):
    database_path = tmp_path / "predicate-drift.db"
    config = _alembic_config(database_path)
    command.upgrade(config, BASELINE_REVISION)
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    with engine.begin() as connection:
        connection.execute(text("DROP INDEX idx_app_one_active_per_job"))
        connection.execute(
            text(
                "CREATE UNIQUE INDEX idx_app_one_active_per_job "
                "ON application (job_id)"
            )
        )
        connection.execute(text("DROP TABLE alembic_version"))
    engine.dispose()
    backup_path = tmp_path / "predicate-drift.backup.db"

    with pytest.raises(SchemaMismatchError):
        upgrade_database(
            f"sqlite:///{database_path.as_posix()}",
            backup_path=backup_path,
        )

    assert not backup_path.exists()
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    assert "alembic_version" not in inspect(engine).get_table_names()
    engine.dispose()


def test_pre_alembic_guard_preserves_string_literal_case(tmp_path):
    database_path = tmp_path / "literal-case-drift.db"
    config = _alembic_config(database_path)
    command.upgrade(config, BASELINE_REVISION)
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    with engine.begin() as connection:
        connection.execute(text("DROP INDEX idx_app_one_active_per_job"))
        connection.execute(
            text(
                "CREATE UNIQUE INDEX idx_app_one_active_per_job "
                "ON application (job_id) WHERE status NOT IN "
                "('rejected','WITHDRAWN','no_response',"
                "'offer_accepted','offer_declined')"
            )
        )
        connection.execute(text("DROP TABLE alembic_version"))
    engine.dispose()

    with pytest.raises(SchemaMismatchError):
        upgrade_database(f"sqlite:///{database_path.as_posix()}")

    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    assert "alembic_version" not in inspect(engine).get_table_names()
    engine.dispose()


def test_pre_alembic_guard_rejects_index_collation_drift(tmp_path):
    database_path = tmp_path / "index-collation-drift.db"
    config = _alembic_config(database_path)
    command.upgrade(config, BASELINE_REVISION)
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    with engine.begin() as connection:
        connection.execute(text("DROP INDEX idx_job_dedup"))
        connection.execute(
            text(
                "CREATE UNIQUE INDEX idx_job_dedup ON job "
                "(source, company, title COLLATE NOCASE, location)"
            )
        )
        connection.execute(text("DROP TABLE alembic_version"))
    engine.dispose()

    with pytest.raises(SchemaMismatchError):
        upgrade_database(f"sqlite:///{database_path.as_posix()}")

    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    assert "alembic_version" not in inspect(engine).get_table_names()
    engine.dispose()


def test_failed_pre_alembic_upgrade_restores_the_backup(tmp_path, monkeypatch):
    database_path = tmp_path / "restore-on-failure.db"
    config = _alembic_config(database_path)
    command.upgrade(config, BASELINE_REVISION)
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO company (name) VALUES ('必须保留')"))
        connection.execute(text("DROP TABLE alembic_version"))
    engine.dispose()

    def _fail_upgrade(*_args, **_kwargs):
        raise RuntimeError("simulated migration failure")

    monkeypatch.setattr("src.db.schema_migrations._upgrade_to_head", _fail_upgrade)
    backup_path = tmp_path / "restore-on-failure.backup.db"

    with pytest.raises(RuntimeError, match="simulated migration failure"):
        upgrade_database(
            f"sqlite:///{database_path.as_posix()}",
            backup_path=backup_path,
        )

    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    inspector = inspect(engine)
    assert "alembic_version" not in inspector.get_table_names()
    assert "source_snapshot" not in inspector.get_table_names()
    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT name FROM company")
        ).scalar_one() == "必须保留"
    engine.dispose()
    assert backup_path.exists()


def test_existing_backup_is_never_overwritten(tmp_path):
    database_path = tmp_path / "backup-collision.db"
    config = _alembic_config(database_path)
    command.upgrade(config, BASELINE_REVISION)
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE alembic_version"))
    engine.dispose()

    backup_path = tmp_path / "existing.backup.db"
    backup_path.write_bytes(b"existing backup must survive")

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        upgrade_database(
            f"sqlite:///{database_path.as_posix()}",
            backup_path=backup_path,
        )

    assert backup_path.read_bytes() == b"existing backup must survive"
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    assert "alembic_version" not in inspect(engine).get_table_names()
    engine.dispose()


def test_concurrent_sqlite_migrations_are_serialized(tmp_path, monkeypatch):
    database_path = tmp_path / "concurrent.db"
    config = _alembic_config(database_path)
    command.upgrade(config, BASELINE_REVISION)
    database_url = f"sqlite:///{database_path.as_posix()}"

    real_upgrade = schema_migrations._upgrade_to_head
    first_upgrade_entered = Event()
    release_first_upgrade = Event()
    unexpected_second_upgrade = Event()
    calls_lock = Lock()
    call_count = 0

    def _delayed_upgrade(alembic_config):
        nonlocal call_count
        with calls_lock:
            call_count += 1
            current_call = call_count
        if current_call == 1:
            first_upgrade_entered.set()
        else:
            unexpected_second_upgrade.set()
        assert release_first_upgrade.wait(5), "test did not release first migration"
        real_upgrade(alembic_config)

    monkeypatch.setattr(schema_migrations, "_upgrade_to_head", _delayed_upgrade)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(upgrade_database, database_url)
        assert first_upgrade_entered.wait(5), "first migration never started"
        second = executor.submit(upgrade_database, database_url)
        assert not unexpected_second_upgrade.wait(0.25)
        release_first_upgrade.set()
        first_result = first.result(timeout=10)
        second_result = second.result(timeout=10)

    assert first_result.action == "upgraded"
    assert second_result.action == "already_current"
    assert call_count == 1
    engine = create_engine(database_url)
    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one() == "8418f8d1585a"
    assert "source_snapshot" in inspect(engine).get_table_names()
    engine.dispose()


def test_sqlite_migration_lock_blocks_another_process(tmp_path):
    database_path = tmp_path / "cross-process.db"
    config = _alembic_config(database_path)
    command.upgrade(config, BASELINE_REVISION)
    database_url = f"sqlite:///{database_path.as_posix()}"
    context = multiprocessing.get_context("spawn")
    started = context.Event()
    result_queue = context.Queue()
    process = context.Process(
        target=_upgrade_in_child_process,
        args=(database_url, started, result_queue),
    )
    lock_path = Path(f"{database_path}.migration.lock")

    with schema_migrations._SQLiteMigrationLock(
        lock_path,
        timeout_seconds=10,
    ):
        process.start()
        assert started.wait(10), "child process did not start"
        with pytest.raises(Empty):
            result_queue.get(timeout=0.25)

    outcome = result_queue.get(timeout=15)
    process.join(timeout=15)
    assert process.exitcode == 0
    assert outcome == ("upgraded", "8418f8d1585a")


def test_repository_database_copy_can_reach_head_without_losing_m0_counts(tmp_path):
    source_path = ROOT / "data" / "jobpulse.db"
    if not source_path.exists():
        pytest.skip("Repository demo database is not present in this checkout")

    database_path = tmp_path / "jobpulse-copy.db"
    shutil.copy2(source_path, database_path)
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = create_engine(database_url)
    inspector = inspect(engine)
    m0_tables = set(BASELINE_COLUMNS)
    if not m0_tables.issubset(inspector.get_table_names()):
        engine.dispose()
        pytest.skip("Repository database is not an M0/M1 demo database")
    with engine.connect() as connection:
        before = {
            table: connection.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar_one()
            for table in sorted(m0_tables)
        }
    engine.dispose()

    upgrade_database(database_url, backup_path=tmp_path / "repository-copy.bak")

    engine = create_engine(database_url)
    with engine.connect() as connection:
        after = {
            table: connection.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar_one()
            for table in sorted(m0_tables)
        }
        revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
    engine.dispose()

    assert after == before
    assert revision == "8418f8d1585a"

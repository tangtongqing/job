"""Static contracts that keep database migrations safe during startup."""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def _read_project_file(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def _powershell_section(script: str, start: str, end: str) -> str:
    """Return one top-level section, with useful failures when markers move."""
    start_index = script.index(start)
    end_index = script.index(end, start_index)
    return script[start_index:end_index]


def test_docker_image_contains_alembic_assets_and_writable_data_directory():
    dockerfile = _read_project_file("Dockerfile")

    alembic_config = re.search(r"(?mi)^COPY\s+alembic\.ini\s+\./\s*$", dockerfile)
    alembic_scripts = re.search(r"(?mi)^COPY\s+alembic\s+\./alembic\s*$", dockerfile)
    data_directory = re.search(r"(?m)\bmkdir\s+-p\s+/app/data\b", dockerfile)
    command = re.search(r"(?mi)^CMD\b", dockerfile)

    assert alembic_config, "Docker image must include alembic.ini"
    assert alembic_scripts, "Docker image must include the Alembic scripts directory"
    assert data_directory, "Docker image must create the SQLite data directory"
    assert command, "Docker image must define its startup command"
    assert max(alembic_config.start(), alembic_scripts.start(), data_directory.start()) < command.start()


def test_docker_startup_migrates_before_launching_the_api():
    dockerfile = _read_project_file("Dockerfile")
    command = dockerfile[dockerfile.index("CMD") :]

    migration = "python -m src.db.init_db"
    api = "exec uvicorn"
    assert migration in command
    assert api in command
    assert command.index(migration) < command.index("&&") < command.index(api)


def test_backend_mode_checks_health_and_port_before_migrating():
    script = _read_project_file("start.ps1")
    backend = _powershell_section(
        script,
        'if ($Mode -eq "Backend")',
        'if ($Mode -eq "Frontend")',
    )

    health_check = backend.index('Test-Url "$BackendUrl/health"')
    occupied_port_check = backend.index("Test-Port 8100")
    migration = backend.index("Initialize-Backend")

    assert health_check < occupied_port_check < migration
    assert "database migration was skipped" in backend


def test_all_mode_only_migrates_after_backend_health_and_port_checks():
    script = _read_project_file("start.ps1")
    all_mode = script[script.index('Write-Step "Checking local prerequisites ..."') :]

    health_check = all_mode.index('$backendRunning = Test-Url "$BackendUrl/health"')
    occupied_port_check = all_mode.index(
        "if (-not $backendRunning -and (Test-Port 8100))"
    )
    guarded_migration = re.search(
        r"if\s*\(\s*-not\s+\$backendRunning\s*\)\s*\{\s*"
        r"Initialize-Backend\s*\}",
        all_mode,
    )

    assert guarded_migration, "All mode must migrate only when no healthy backend exists"
    assert health_check < occupied_port_check < guarded_migration.start()


def test_spawned_backend_skips_the_migration_already_run_by_all_mode():
    script = _read_project_file("start.ps1")

    assert "[switch]$SkipDatabaseMigration" in script
    assert re.search(
        r"if\s*\(\s*-not\s+\$SkipDatabaseMigration\s*\)\s*\{"
        r".*?python\s+-m\s+src\.db\.init_db.*?\}",
        script,
        flags=re.DOTALL,
    ), "Initialize-Backend must honor the skip-migration switch"

    launcher = _powershell_section(
        script,
        "function Start-ServiceTerminal",
        "Set-Location $ProjectRoot",
    )
    assert re.search(
        r"if\s*\(\s*\$ServiceMode\s+-eq\s+\"Backend\"\s*\)\s*\{"
        r"\s*\$arguments\s*\+=\s*\" -SkipDatabaseMigration\"\s*\}",
        launcher,
    ), "The child Backend terminal must not repeat the parent migration"

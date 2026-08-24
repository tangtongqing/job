[CmdletBinding()]
param(
    [ValidateSet("All", "Backend", "Frontend")]
    [string]$Mode = "All",
    [switch]$SkipBootstrap,
    [switch]$SkipDatabaseMigration,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$WebRoot = Join-Path $ProjectRoot "web"
$BackendUrl = "http://127.0.0.1:8100"
$FrontendUrl = "http://127.0.0.1:3100"
$LocalApiUrl = "$BackendUrl/api/v1"

function Write-Step([string]$Message) {
    Write-Host "[JobPulse] $Message" -ForegroundColor Cyan
}

function Assert-Command([string]$Name, [string]$InstallHint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name was not found. $InstallHint"
    }
}

function Test-Url([string]$Url) {
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
    }
    catch {
        return $false
    }
}

function Test-Port([int]$Port) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $asyncResult = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        if (-not $asyncResult.AsyncWaitHandle.WaitOne(500)) {
            return $false
        }
        $client.EndConnect($asyncResult)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Close()
    }
}

function Wait-ForUrl([string]$Name, [string]$Url, [int]$TimeoutSeconds = 60) {
    Write-Step "Waiting for $Name at $Url ..."
    for ($attempt = 0; $attempt -lt $TimeoutSeconds; $attempt++) {
        if (Test-Url $Url) {
            Write-Host "[JobPulse] $Name is ready." -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds 1
    }
    Write-Warning "$Name did not become ready within $TimeoutSeconds seconds. Check its terminal for details."
    return $false
}

function Initialize-Backend {
    Assert-Command "python" "Install Python 3.10 or newer, then reopen this terminal."

    if (-not $SkipBootstrap) {
        & python -c "import fastapi, sqlalchemy, uvicorn" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Step "Installing backend dependencies (first run only) ..."
            & python -m pip install -e ".[dev]"
            if ($LASTEXITCODE -ne 0) {
                throw "Backend dependency installation failed."
            }
        }
    }

    if (-not $SkipDatabaseMigration) {
        Write-Step "Checking and upgrading the local database schema ..."
        & python -m src.db.init_db
        if ($LASTEXITCODE -ne 0) {
            throw "Database migration or initialization failed."
        }
    }
}

function Initialize-Frontend {
    Assert-Command "node" "Install Node.js 22.13 or newer, then reopen this terminal."
    Assert-Command "npm" "Install Node.js 22.13 or newer, then reopen this terminal."

    $nextExecutable = Join-Path $WebRoot "node_modules\.bin\next.cmd"
    if (-not $SkipBootstrap -and -not (Test-Path $nextExecutable)) {
        Write-Step "Installing frontend dependencies (first run only) ..."
        Push-Location $WebRoot
        try {
            & npm install
            if ($LASTEXITCODE -ne 0) {
                throw "Frontend dependency installation failed."
            }
        }
        finally {
            Pop-Location
        }
    }
}

function Start-ServiceTerminal([string]$ServiceMode) {
    $shellCommand = Get-Command "pwsh" -ErrorAction SilentlyContinue
    if (-not $shellCommand) {
        $shellCommand = Get-Command "powershell.exe" -ErrorAction Stop
    }

    $arguments = "-NoExit -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Mode $ServiceMode -SkipBootstrap"
    if ($ServiceMode -eq "Backend") {
        $arguments += " -SkipDatabaseMigration"
    }
    Start-Process -FilePath $shellCommand.Source -ArgumentList $arguments -WorkingDirectory $ProjectRoot | Out-Null
}

Set-Location $ProjectRoot

if ($Mode -eq "Backend") {
    $Host.UI.RawUI.WindowTitle = "JobPulse Backend :8100"
    if (Test-Url "$BackendUrl/health") {
        Write-Host "[JobPulse] Backend is already running; database migration was skipped." -ForegroundColor Yellow
        exit 0
    }
    if (Test-Port 8100) {
        throw "Port 8100 is already in use. Stop the existing process before migrating or starting the backend."
    }
    Initialize-Backend
    Write-Step "Starting backend on $BackendUrl ..."
    & python -m uvicorn src.main:app --host 127.0.0.1 --port 8100 --reload
    exit $LASTEXITCODE
}

if ($Mode -eq "Frontend") {
    $Host.UI.RawUI.WindowTitle = "JobPulse Frontend :3100"
    Initialize-Frontend
    $env:NEXT_PUBLIC_API_BASE_URL = $LocalApiUrl
    Set-Location $WebRoot
    Write-Step "Starting frontend on $FrontendUrl (local API: $LocalApiUrl) ..."
    & npm run dev -- --webpack --hostname 127.0.0.1 --port 3100
    exit $LASTEXITCODE
}

Write-Step "Checking local prerequisites ..."
$backendRunning = Test-Url "$BackendUrl/health"
$frontendRunning = Test-Url $FrontendUrl

if (-not $backendRunning -and (Test-Port 8100)) {
    throw "Port 8100 is already in use by another process. Close it and run start.cmd again."
}
if (-not $frontendRunning -and (Test-Port 3100)) {
    throw "Port 3100 is already in use by another process. Close it and run start.cmd again."
}

if (-not $backendRunning) {
    Initialize-Backend
}
if (-not $frontendRunning) {
    Initialize-Frontend
}

if ($backendRunning) {
    Write-Host "[JobPulse] Backend is already running." -ForegroundColor Yellow
}
else {
    Write-Step "Opening the backend terminal ..."
    Start-ServiceTerminal "Backend"
}

if ($frontendRunning) {
    Write-Host "[JobPulse] Frontend is already running." -ForegroundColor Yellow
}
else {
    Write-Step "Opening the frontend terminal ..."
    Start-ServiceTerminal "Frontend"
}

$backendReady = Wait-ForUrl "Backend" "$BackendUrl/health"
$frontendReady = Wait-ForUrl "Frontend" $FrontendUrl

if ($backendReady -and $frontendReady) {
    Write-Host ""
    Write-Host "JobPulse is ready:" -ForegroundColor Green
    Write-Host "  Product: $FrontendUrl/dashboard"
    Write-Host "  Website: $FrontendUrl"
    Write-Host "  API docs: $BackendUrl/docs"
    Write-Host ""
    Write-Host "To stop it, press Ctrl+C in both service terminals."

    if (-not $NoBrowser) {
        Start-Process "$FrontendUrl/dashboard"
    }
}
else {
    exit 1
}

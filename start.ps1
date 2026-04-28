$ErrorActionPreference = 'Stop'

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PidDir = Join-Path $RootDir '.run'
$BackendPidFile = Join-Path $PidDir 'backend.pid'
$FrontendPidFile = Join-Path $PidDir 'frontend.pid'
$BackendLog = Join-Path $PidDir 'backend.log'
$FrontendLog = Join-Path $PidDir 'frontend.log'

New-Item -ItemType Directory -Path $PidDir -Force | Out-Null
Remove-Item $BackendPidFile, $FrontendPidFile, $BackendLog, $FrontendLog -Force -ErrorAction SilentlyContinue

function Start-LoggedProcess {
    param(
        [string]$Name,
        [string]$WorkingDir,
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$LogFile,
        [string]$PidFile
    )

    $process = Start-Process -FilePath $FilePath -ArgumentList $Arguments -WorkingDirectory $WorkingDir -RedirectStandardOutput $LogFile -RedirectStandardError $LogFile -PassThru
    Set-Content -Path $PidFile -Value $process.Id
    return $process
}

function Watch-Log {
    param(
        [string]$Title,
        [string]$Path
    )

    Write-Host ""
    Write-Host "===== $Title ====="
    if (-not (Test-Path $Path)) {
        New-Item -ItemType File -Path $Path -Force | Out-Null
    }

    Get-Content -Path $Path -Wait -Tail 0
}

Write-Host '========================================'
Write-Host 'Starting AI Kanban Platform...'
Write-Host '========================================'
Write-Host ''

Write-Host '[1/2] Starting Backend Service (FastAPI)...'
$backend = Start-LoggedProcess -Name 'backend' -WorkingDir (Join-Path $RootDir 'backend') -FilePath 'python' -Arguments @('-m', 'uvicorn', 'app.main:app', '--reload') -LogFile $BackendLog -PidFile $BackendPidFile
Write-Host "Backend PID: $($backend.Id)"

Write-Host '[2/2] Starting Frontend Service (Vue 3 + Vite)...'
$frontend = Start-LoggedProcess -Name 'frontend' -WorkingDir (Join-Path $RootDir 'frontend') -FilePath 'npm' -Arguments @('run', 'dev') -LogFile $FrontendLog -PidFile $FrontendPidFile
Write-Host "Frontend PID: $($frontend.Id)"

Write-Host ''
Write-Host 'Both services are running in this window.'
Write-Host 'Frontend URL: http://localhost:5173'
Write-Host 'Backend URL: http://localhost:8000'
Write-Host 'Logs are saved in: ' $PidDir
Write-Host 'Press Ctrl+C to stop this window. Use stop.bat to terminate processes cleanly.'

# Stream both logs into this console
$backendJob = Start-Job -ScriptBlock { param($p) Get-Content -Path $p -Wait -Tail 0 } -ArgumentList $BackendLog
$frontendJob = Start-Job -ScriptBlock { param($p) Get-Content -Path $p -Wait -Tail 0 } -ArgumentList $FrontendLog

try {
    while (-not $backend.HasExited -or -not $frontend.HasExited) {
        Start-Sleep -Seconds 1
    }
} finally {
    Stop-Job $backendJob, $frontendJob -Force -ErrorAction SilentlyContinue | Out-Null
    Remove-Job $backendJob, $frontendJob -Force -ErrorAction SilentlyContinue | Out-Null
}

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
$docker = if ($dockerCommand) {
    $dockerCommand.Source
} else {
    "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
}

if (-not (Test-Path $docker)) {
    throw "Docker CLI was not found. Install Docker Desktop or add docker.exe to PATH."
}

$dockerDesktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
& $docker info *> $null
if ($LASTEXITCODE -ne 0) {
    if (Test-Path $dockerDesktop) {
        Write-Host "Starting Docker Desktop..."
        Start-Process -FilePath $dockerDesktop -WindowStyle Hidden
    }

    for ($i = 1; $i -le 24; $i++) {
        Start-Sleep -Seconds 5
        & $docker info *> $null
        if ($LASTEXITCODE -eq 0) {
            break
        }
    }
}

& $docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Desktop is installed, but the Docker daemon is not running. Open Docker Desktop manually, wait until it is ready, then rerun this script."
}

& $docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d

Write-Host ""
Write-Host "Production stack is starting."
Write-Host "Local URL: http://localhost/"
Write-Host "LAN URL:   http://192.168.1.14/"
Write-Host ""
Write-Host "Use 'docker compose -f docker-compose.prod.yml logs -f' to follow logs."

# One-command start for Windows (PowerShell 5.1+). Usage: start.cmd [-NoBrowser]
param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

$Url = 'http://localhost:8080'
$Ollama = 'http://localhost:11434'
$Models = @('qwen3:8b', 'bge-m3')

function Step($m) { Write-Host "==> $m" -ForegroundColor Cyan }
function Fail($m) { Write-Host "xx $m" -ForegroundColor Red; exit 1 }
function Test-Url($u) { try { Invoke-RestMethod -Uri $u -TimeoutSec 3 | Out-Null; return $true } catch { return $false } }

Step 'Checking Docker'
docker info *> $null
if ($LASTEXITCODE -ne 0) { Fail 'Docker is not running. Start Docker Desktop and run start.cmd again.' }

Step 'Checking Ollama'
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
  Fail 'Ollama is not installed. Get it from https://ollama.com/download and run start.cmd again.'
}
if (-not (Test-Url "$Ollama/api/tags")) {
  Step 'Starting Ollama in the background'
  Start-Process -FilePath 'ollama' -ArgumentList 'serve' -WindowStyle Hidden
  for ($i = 0; $i -lt 30 -and -not (Test-Url "$Ollama/api/tags"); $i++) { Start-Sleep -Seconds 1 }
  if (-not (Test-Url "$Ollama/api/tags")) { Fail 'Ollama did not start within 30 s.' }
}

$installed = (Invoke-RestMethod -Uri "$Ollama/api/tags").models | ForEach-Object { $_.name }
foreach ($m in $Models) {
  if ($installed -contains $m -or $installed -contains "$($m):latest") { Step "Model $m already installed" }
  else { Step "Pulling model $m (one time)"; ollama pull $m; if ($LASTEXITCODE -ne 0) { Fail "ollama pull $m failed" } }
}

Step 'Starting containers (first start builds images and takes 10-20 min)'
docker compose up -d --build --wait
if ($LASTEXITCODE -ne 0) { Fail 'docker compose up failed. See: docker compose logs' }

Step 'Waiting for the api'
for ($i = 0; $i -lt 120 -and -not (Test-Url "$Url/api/v1/health"); $i++) { Start-Sleep -Seconds 1 }
if (-not (Test-Url "$Url/api/v1/health")) { Fail 'The api did not become healthy in 120 s. See: docker compose logs api' }

Step "rag-fun is running at $Url"
if (-not $NoBrowser) { Start-Process $Url }

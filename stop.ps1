$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot
docker compose stop
Write-Host 'rag-fun stopped. Data is kept; start.cmd starts it again.'

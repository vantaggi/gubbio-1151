# Setup Environment Script per Gubbio 1151 (Game Boy Advance / Butano Engine)
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "   GUBBIO 1151: SETUP AMBIENTE DI COMPILAZIONE GBA   " -ForegroundColor Yellow
Write-Host "======================================================" -ForegroundColor Cyan

# 1. Verifica Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd) {
    Write-Host "[OK] Python rilevato: $($pythonCmd.Source)" -ForegroundColor Green
} else {
    Write-Host "[!] Python non rilevato nel PATH." -ForegroundColor Red
}

# 2. Verifica Git
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if ($gitCmd) {
    Write-Host "[OK] Git rilevato: $($gitCmd.Source)" -ForegroundColor Green
} else {
    Write-Host "[!] Git non trovato." -ForegroundColor Red
}

# 3. Verifica devkitARM
if ($env:DEVKITARM -or (Test-Path "C:\devkitPro\devkitARM")) {
    Write-Host "[OK] devkitARM rilevato." -ForegroundColor Green
} else {
    Write-Host "[INFO] devkitPro/devkitARM non rilevato. Per compilare la ROM .gba nativa, scarica l'installer da https://devkitpro.org/wiki/Getting_Started" -ForegroundColor Yellow
}

# 4. Clone Butano Engine (se non presente)
$butanoDir = Join-Path $PSScriptRoot "..\..\butano"
if (-not (Test-Path $butanoDir)) {
    Write-Host "[INFO] Clonazione di Butano Engine nella directory PROGETTI..." -ForegroundColor Cyan
    git clone --depth 1 https://github.com/GValiente/butano.git $butanoDir
    Write-Host "[OK] Butano Engine clonato in $butanoDir" -ForegroundColor Green
} else {
    Write-Host "[OK] Butano Engine trovato in $butanoDir" -ForegroundColor Green
}

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "Setup completato!" -ForegroundColor Green

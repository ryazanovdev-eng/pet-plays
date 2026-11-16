[CmdletBinding()]
param(
    [switch]$SkipBoot
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$projectFile = Join-Path $root 'project.godot'
$logDir = Join-Path $root '.godot'
$logFile = Join-Path $logDir 'check.log'

if (-not (Test-Path -LiteralPath $projectFile)) {
    Write-Host 'project.godot не найден: Godot-проект ещё не создан.' -ForegroundColor Yellow
    exit 1
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$godot = Join-Path $root 'tools\godot.cmd'
$output = @()
$output += & $godot -Headless -Import 2>&1
$importCode = $LASTEXITCODE

if (-not $SkipBoot) {
    $output += & $godot -Headless -QuitAfter 5 2>&1
    $bootCode = $LASTEXITCODE
} else {
    $bootCode = 0
}

$output | ForEach-Object { Write-Host $_ }
$output | Out-File -FilePath $logFile -Encoding utf8

$text = $output | Out-String
$errors = @($text -split "`r?`n" | Where-Object { $_ -match 'SCRIPT ERROR|Parse Error|ERROR:' })

Write-Host ''
if ($errors.Count -gt 0) {
    Write-Host "Найдено ошибок: $($errors.Count)" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    Write-Host "Полный лог: $logFile"
    exit 1
}

if ($importCode -ne 0 -or $bootCode -ne 0) {
    Write-Host "Godot завершился с кодом import=$importCode boot=$bootCode" -ForegroundColor Red
    Write-Host "Полный лог: $logFile"
    exit 1
}

Write-Host 'OK: импорт и запуск главной сцены прошли без ошибок.' -ForegroundColor Green
Write-Host "Лог: $logFile"
exit 0

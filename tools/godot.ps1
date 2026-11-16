[CmdletBinding()]
param(
    [switch]$Editor,
    [switch]$Headless,
    [switch]$Import,
    [switch]$Version,
    [int]$QuitAfter = 0,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Extra
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$gameExe = $env:GODOT_BIN
if (-not $gameExe) { $gameExe = 'D:\godot\Godot_v4.7.2-stable_win64.exe' }
$consoleExe = $env:GODOT_CONSOLE
if (-not $consoleExe) { $consoleExe = 'D:\godot\Godot_v4.7.2-stable_win64_console.exe' }

if ($Version) {
    & $gameExe --version
    exit $LASTEXITCODE
}

if (-not (Test-Path -LiteralPath $gameExe)) {
    Write-Error "Godot не найден: $gameExe. Задай переменную окружения GODOT_BIN."
}
if (-not (Test-Path -LiteralPath $consoleExe)) {
    $consoleExe = $gameExe
}

$exe = $gameExe
if ($Headless -or $Import) { $exe = $consoleExe }

$godotArgs = @('--path', $root)
if ($Editor) { $godotArgs += '--editor' }
if ($Headless) { $godotArgs += '--headless' }
if ($Import) { $godotArgs += '--import' }
if ($QuitAfter -gt 0) { $godotArgs += @('--quit-after', "$QuitAfter") }
if ($Extra) { $godotArgs += $Extra }

& $exe @godotArgs
exit $LASTEXITCODE

$ErrorActionPreference = 'Stop'

$root = $env:WORKTREE_PATH
if (-not $root) { $root = Split-Path -Parent $PSScriptRoot }

& (Join-Path $root 'tools\godot.cmd')

<#
.SYNOPSIS
  Launch a goal through the ADE using Cursor Agent CLI.

.EXAMPLE
  ./scripts/ade/goal.ps1 "Implementa autenticacion OAuth"          # interactive, approvals stay on
  ./scripts/ade/goal.ps1 "Implementa autenticacion OAuth" -Plan    # read-only planning first (plan mode)
  ./scripts/ade/goal.ps1 "Revisa los cambios" -Headless            # non-interactive (-p); still no --force

.NOTES
  Never passes --force/--yolo: shell commands still go through Cursor's approval settings and
  the ADE guard hook (.cursor/hooks.json). Review the output before approving destructive steps.
#>
param(
    [Parameter(Mandatory = $true, Position = 0)][string]$Goal,
    [switch]$Plan,
    [switch]$Headless,
    [string]$Model
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "../..")
if (-not (Get-Command agent -ErrorAction SilentlyContinue)) {
    throw "Cursor Agent CLI ('agent') not found on PATH. Install/login: https://cursor.com/cli"
}

$prompt = @"
Use the ADE orchestrator skill (.cursor/skills/orchestrator/SKILL.md) for this goal.
Classify it, state the route, run only the needed roles, respect approval gates, and finish with the Definition of Done report.

GOAL: $Goal
"@

$args_ = @("--workspace", $root)
if ($Plan) { $args_ += "--plan" }
if ($Headless) { $args_ += "-p" }
if ($Model) { $args_ += @("--model", $Model) }
$args_ += $prompt

& agent @args_
exit $LASTEXITCODE

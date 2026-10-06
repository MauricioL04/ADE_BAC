<#
.SYNOPSIS
  Verify the ADE framework is healthy and ready to accept a project brief.

.DESCRIPTION
  Runs the mechanical checks that must pass before starting a real project:
  tests, verification, hook installation status, and PROJECT.md presence.
  Prints the next steps. Never modifies the repository.

.EXAMPLE
  pwsh scripts/ade/kickoff.ps1
  pwsh scripts/ade/kickoff.ps1 -Fix   # also runs the user-hook installer and audit scrub
#>
param([switch]$Fix)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "../..")
$results = New-Object System.Collections.Generic.List[object]

function Check([string]$name, [scriptblock]$block) {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"   # native stderr must not turn into a terminating error
    $global:LASTEXITCODE = 0
    try {
        $output = & $block 2>&1
        $status = if ($LASTEXITCODE -eq 0) { "PASS" } else { "FAIL" }
    } catch {
        $status = "FAIL"; $output = $_.Exception.Message
    } finally {
        $ErrorActionPreference = $prev
    }
    $results.Add([pscustomobject]@{ Name = $name; Status = $status; Output = ($output | Out-String).Trim() })
}

Push-Location $root
try {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        throw "python is not on PATH; the ADE tooling and hooks require Python 3.11+"
    }

    Check "framework tests" { python -m unittest discover -s tests -q }
    Check "verify.py (build/lint/type/tests/secrets)" { python scripts/ade/verify.py }
    Check "user-hook fallback (empty Cursor windows)" { python scripts/ade/install_cursor_hooks.py --show }
    Check "PROJECT.md brief present" {
        if (-not (Test-Path (Join-Path $root "PROJECT.md"))) { $global:LASTEXITCODE = 1; "missing PROJECT.md" }
        else { "found" }
    }

    if ($Fix) {
        Check "install user-hook fallback" { python scripts/ade/install_cursor_hooks.py --install-user }
        Check "scrub legacy audit bodies"  { python scripts/ade/log_interaction.py --scrub }
    }

    "`nADE KICKOFF REPORT`n"
    $results | Format-Table -AutoSize Name, Status | Out-String | Write-Output
    $failed = $results | Where-Object { $_.Status -eq "FAIL" }
    if ($failed) {
        "Failures:"
        $failed | ForEach-Object { "  - $($_.Name): $($_.Output)" }
        exit 1
    }

    @"
Framework is healthy. Next steps:

  1) Fill PROJECT.md (sections 1-6 minimum).
  2) In Cursor chat: 'Use the orchestrator skill for the goal in PROJECT.md'.
     From terminal:  ./scripts/ade/goal.ps1 "<goal>" [-Plan]
  3) Spec-driven feature? Use Spec Kit: /speckit-specify, /speckit-plan, /speckit-tasks, /speckit-implement.
  4) The audit log records role and character count per interaction (git-ignored by default).
"@
} finally {
    Pop-Location
}

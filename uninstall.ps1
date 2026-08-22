$ErrorActionPreference = "Stop"

$KitRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$GlobalAgents = Join-Path $HOME ".codex\AGENTS.md"
$GlobalHarness = Join-Path $HOME ".codex\playbook-harness"
$SkillsDir = Join-Path $HOME ".agents\skills"
$SkillsSourceRoot = Join-Path $KitRoot ".agents\skills"

$begin = "<!-- BEGIN AI_AGENT_PLAYBOOK_KIT -->"
$end = "<!-- END AI_AGENT_PLAYBOOK_KIT -->"

if (Test-Path $GlobalAgents) {
    $current = Get-Content -Raw -Encoding UTF8 $GlobalAgents
    $pattern = "(?s)\s*" + [regex]::Escape($begin) + ".*?" + [regex]::Escape($end) + "\s*"
    $updated = [regex]::Replace($current, $pattern, "`r`n")
    Set-Content -Path $GlobalAgents -Value $updated.Trim() -Encoding UTF8
    Write-Host "Removed kit section from $GlobalAgents"
}

Get-ChildItem -Path $SkillsSourceRoot -Directory | ForEach-Object {
    $skillName = $_.Name
    $target = Join-Path $SkillsDir $skillName
    if (Test-Path $target) {
        Remove-Item -Recurse -Force $target
        Write-Host "Removed skill '$skillName'"
    }
}

if (Test-Path -LiteralPath $GlobalHarness) {
    Remove-Item -LiteralPath $GlobalHarness -Recurse -Force
    Write-Host "Removed playbook harness"
}

Write-Host "Uninstall complete."

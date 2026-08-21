$ErrorActionPreference = "Stop"

$GlobalAgents = Join-Path $HOME ".codex\AGENTS.md"
$SkillsDir = Join-Path $HOME ".agents\skills"
$Skills = @(
    "ai-agent-development-playbook",
    "human-readable-code",
    "human-centered-project-builder",
    "guide-ppt-creator"
)

$begin = "<!-- BEGIN AI_AGENT_PLAYBOOK_KIT -->"
$end = "<!-- END AI_AGENT_PLAYBOOK_KIT -->"

if (Test-Path $GlobalAgents) {
    $current = Get-Content -Raw -Encoding UTF8 $GlobalAgents
    $pattern = "(?s)\s*" + [regex]::Escape($begin) + ".*?" + [regex]::Escape($end) + "\s*"
    $updated = [regex]::Replace($current, $pattern, "`r`n")
    Set-Content -Path $GlobalAgents -Value $updated.Trim() -Encoding UTF8
    Write-Host "Removed kit section from $GlobalAgents"
}

foreach ($skill in $Skills) {
    $target = Join-Path $SkillsDir $skill
    if (Test-Path $target) {
        Remove-Item -Recurse -Force $target
        Write-Host "Removed skill '$skill'"
    }
}

Write-Host "Uninstall complete."

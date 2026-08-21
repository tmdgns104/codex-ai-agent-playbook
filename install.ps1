param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$KitRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$GlobalCodexDir = Join-Path $HOME ".codex"
$GlobalAgents = Join-Path $GlobalCodexDir "AGENTS.md"
$SourceAgents = Join-Path $KitRoot ".codex\AGENTS.md"

$SkillsDir = Join-Path $HOME ".agents\skills"
$SkillsSourceRoot = Join-Path $KitRoot ".agents\skills"

New-Item -ItemType Directory -Force -Path $GlobalCodexDir | Out-Null
New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null

$begin = "<!-- BEGIN AI_AGENT_PLAYBOOK_KIT -->"
$end = "<!-- END AI_AGENT_PLAYBOOK_KIT -->"

$sourceText = Get-Content -Raw -Encoding UTF8 $SourceAgents
$startIndex = $sourceText.IndexOf($begin)
$endIndex = $sourceText.IndexOf($end)

if ($startIndex -lt 0 -or $endIndex -lt 0) {
    throw "Source AGENTS.md marker not found."
}

$kitBlock = $sourceText.Substring($startIndex, ($endIndex - $startIndex) + $end.Length)

if (Test-Path $GlobalAgents) {
    $current = Get-Content -Raw -Encoding UTF8 $GlobalAgents
    $pattern = "(?s)" + [regex]::Escape($begin) + ".*?" + [regex]::Escape($end)

    if ($current -match $pattern) {
        $updated = [regex]::Replace(
            $current,
            $pattern,
            [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $kitBlock }
        )
        Set-Content -Path $GlobalAgents -Value $updated -Encoding UTF8
        Write-Host "Updated kit section in $GlobalAgents"
    }
    else {
        Add-Content -Path $GlobalAgents -Value ("`r`n`r`n" + $kitBlock) -Encoding UTF8
        Write-Host "Appended kit section to existing $GlobalAgents"
    }
}
else {
    Copy-Item $SourceAgents $GlobalAgents
    Write-Host "Installed $GlobalAgents"
}

Get-ChildItem -Path $SkillsSourceRoot -Directory | ForEach-Object {
    $skillName = $_.Name
    $source = $_.FullName
    $target = Join-Path $SkillsDir $skillName

    if (Test-Path $target) {
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $backup = "$target.backup-$stamp"
        Copy-Item -Recurse -Force $target $backup
        Write-Host "Backed up existing skill '$skillName' to $backup"
        Remove-Item -Recurse -Force $target
    }

    Copy-Item -Recurse -Force $source $target
    Write-Host "Installed skill '$skillName' to $target"
}

Write-Host ""
Write-Host "Installation complete."
Write-Host "Start a new Codex session and try:"
Write-Host '$ai-agent-development-playbook'
Write-Host '$human-readable-code'
Write-Host '$human-centered-project-builder'
Write-Host '$guide-ppt-creator'
Write-Host '$codex-long-run'
Write-Host '$codex-task-router'

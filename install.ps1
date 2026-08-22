param(
    [switch]$Force,
    [switch]$SkipVerify
)

$ErrorActionPreference = "Stop"

$KitRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$GlobalCodexDir = Join-Path $HOME ".codex"
$GlobalAgents = Join-Path $GlobalCodexDir "AGENTS.md"
$SourceAgents = Join-Path $KitRoot ".codex\AGENTS.md"

$SkillsDir = Join-Path $HOME ".agents\skills"
$SkillsSourceRoot = Join-Path $KitRoot ".agents\skills"

$BackupBase = Join-Path $GlobalCodexDir "playbook-backups"
$script:RunBackup = $null

$begin = "<!-- BEGIN AI_AGENT_PLAYBOOK_KIT -->"
$end = "<!-- END AI_AGENT_PLAYBOOK_KIT -->"

function Get-RunBackup {
    if (-not $script:RunBackup) {
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $script:RunBackup = Join-Path $BackupBase $stamp
        New-Item -ItemType Directory -Force -Path $script:RunBackup | Out-Null
    }
    return $script:RunBackup
}

function Get-DirectoryFingerprint {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }

    $root = (Get-Item -LiteralPath $Path).FullName.TrimEnd([char[]]"\/")
    $parts = New-Object System.Collections.Generic.List[string]

    Get-ChildItem -LiteralPath $Path -Recurse -File |
        Sort-Object FullName |
        ForEach-Object {
            $relative = $_.FullName.Substring($root.Length).TrimStart([char[]]"\/")
            $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
            $parts.Add("$relative=$hash")
        }

    $joined = [string]::Join("`n", $parts)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($joined)
    $sha = [System.Security.Cryptography.SHA256]::Create()

    try {
        return ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace("-", "")
    }
    finally {
        $sha.Dispose()
    }
}

function Test-DirectoryEqual {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Target
    )

    if (-not (Test-Path -LiteralPath $Target)) {
        return $false
    }

    return (Get-DirectoryFingerprint -Path $Source) -eq (Get-DirectoryFingerprint -Path $Target)
}

New-Item -ItemType Directory -Force -Path $GlobalCodexDir | Out-Null
New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null

$sourceText = Get-Content -Raw -Encoding UTF8 $SourceAgents
$startIndex = $sourceText.IndexOf($begin)
$endIndex = $sourceText.IndexOf($end)

if ($startIndex -lt 0 -or $endIndex -lt 0 -or $endIndex -lt $startIndex) {
    throw "Source AGENTS.md marker not found or invalid."
}

$kitBlock = $sourceText.Substring($startIndex, ($endIndex - $startIndex) + $end.Length)
$pattern = "(?s)" + [regex]::Escape($begin) + ".*?" + [regex]::Escape($end)

if (Test-Path -LiteralPath $GlobalAgents) {
    $current = Get-Content -Raw -Encoding UTF8 $GlobalAgents

    if ($current -match $pattern) {
        $updated = [regex]::Replace(
            $current,
            $pattern,
            [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $kitBlock }
        )
    }
    else {
        $updated = $current.TrimEnd() + "`r`n`r`n" + $kitBlock + "`r`n"
    }

    if ($Force -or $updated -ne $current) {
        $backupRoot = Get-RunBackup
        Copy-Item -LiteralPath $GlobalAgents -Destination (Join-Path $backupRoot "AGENTS.md") -Force
        Set-Content -LiteralPath $GlobalAgents -Value $updated -Encoding UTF8
        Write-Host "UPDATED  $GlobalAgents"
    }
    else {
        Write-Host "OK       $GlobalAgents"
    }
}
else {
    Copy-Item -LiteralPath $SourceAgents -Destination $GlobalAgents
    Write-Host "INSTALLED $GlobalAgents"
}

# V6 and earlier placed timestamp backups inside ~/.agents/skills. Those folders can
# be discovered as duplicate skills, so move them outside the skill discovery path.
Get-ChildItem -LiteralPath $SkillsDir -Directory -Filter "*.backup-*" -ErrorAction SilentlyContinue |
    ForEach-Object {
        $legacyRoot = Join-Path (Get-RunBackup) "legacy-skill-backups"
        New-Item -ItemType Directory -Force -Path $legacyRoot | Out-Null
        Move-Item -LiteralPath $_.FullName -Destination (Join-Path $legacyRoot $_.Name) -Force
        Write-Host "MOVED    legacy backup $($_.Name)"
    }

Get-ChildItem -LiteralPath $SkillsSourceRoot -Directory | ForEach-Object {
    $skillName = $_.Name
    $source = $_.FullName
    $target = Join-Path $SkillsDir $skillName

    $same = Test-DirectoryEqual -Source $source -Target $target
    if ($same -and -not $Force) {
        Write-Host "OK       skill '$skillName'"
    }
    else {
        if (Test-Path -LiteralPath $target) {
            $skillsBackupRoot = Join-Path (Get-RunBackup) "skills"
            New-Item -ItemType Directory -Force -Path $skillsBackupRoot | Out-Null
            Copy-Item -LiteralPath $target -Destination (Join-Path $skillsBackupRoot $skillName) -Recurse -Force
            Remove-Item -LiteralPath $target -Recurse -Force
            Write-Host "BACKUP   skill '$skillName'"
        }

        Copy-Item -LiteralPath $source -Destination $target -Recurse -Force
        Write-Host "INSTALLED skill '$skillName'"
    }
}

Write-Host ""
Write-Host "Installation complete."

if ($script:RunBackup) {
    Write-Host "Backup: $script:RunBackup"
}

if (-not $SkipVerify) {
    $verifyScript = Join-Path $KitRoot "verify-install.ps1"
    if (-not (Test-Path -LiteralPath $verifyScript)) {
        throw "verify-install.ps1 not found."
    }

    Write-Host ""
    & $verifyScript
    if ($LASTEXITCODE -ne 0) {
        throw "Global installation verification failed."
    }
}

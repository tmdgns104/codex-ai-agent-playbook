$ErrorActionPreference = "Stop"

$KitRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$GlobalAgents = Join-Path $HOME ".codex\AGENTS.md"
$SourceAgents = Join-Path $KitRoot ".codex\AGENTS.md"
$SkillsDir = Join-Path $HOME ".agents\skills"
$SkillsSourceRoot = Join-Path $KitRoot ".agents\skills"

$begin = "<!-- BEGIN AI_AGENT_PLAYBOOK_KIT -->"
$end = "<!-- END AI_AGENT_PLAYBOOK_KIT -->"
$failed = $false

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

Write-Host "Codex AI Agent Playbook - global verification"
Write-Host ""

if (-not (Test-Path -LiteralPath $GlobalAgents)) {
    Write-Host "FAIL     global AGENTS.md missing: $GlobalAgents"
    $failed = $true
}
else {
    $sourceText = Get-Content -Raw -Encoding UTF8 $SourceAgents
    $installedText = Get-Content -Raw -Encoding UTF8 $GlobalAgents

    $startIndex = $sourceText.IndexOf($begin)
    $endIndex = $sourceText.IndexOf($end)

    if ($startIndex -lt 0 -or $endIndex -lt 0 -or $endIndex -lt $startIndex) {
        Write-Host "FAIL     source AGENTS.md markers invalid"
        $failed = $true
    }
    else {
        $kitBlock = $sourceText.Substring($startIndex, ($endIndex - $startIndex) + $end.Length)
        if ($installedText.Contains($kitBlock)) {
            Write-Host "PASS     global AGENTS.md playbook block"
        }
        else {
            Write-Host "DRIFT    global AGENTS.md playbook block differs from repository"
            $failed = $true
        }
    }
}

Get-ChildItem -LiteralPath $SkillsSourceRoot -Directory | ForEach-Object {
    $skillName = $_.Name
    $source = $_.FullName
    $target = Join-Path $SkillsDir $skillName

    if (-not (Test-Path -LiteralPath $target)) {
        Write-Host "MISSING  skill '$skillName'"
        $failed = $true
    }
    else {
        $sourceHash = Get-DirectoryFingerprint -Path $source
        $targetHash = Get-DirectoryFingerprint -Path $target

        if ($sourceHash -eq $targetHash) {
            Write-Host "PASS     skill '$skillName'"
        }
        else {
            Write-Host "DRIFT    skill '$skillName'"
            $failed = $true
        }
    }
}

$legacyBackups = @(
    Get-ChildItem -LiteralPath $SkillsDir -Directory -Filter "*.backup-*" -ErrorAction SilentlyContinue
)

if ($legacyBackups.Count -gt 0) {
    Write-Host ""
    Write-Host "WARN     legacy backup folders remain inside skill discovery path:"
    $legacyBackups | ForEach-Object { Write-Host "         $($_.FullName)" }
    $failed = $true
}

Write-Host ""

if ($failed) {
    Write-Host "RESULT   FAIL"
    exit 1
}

Write-Host "RESULT   PASS"
exit 0

---
name: powershell-windows
description: PowerShell과 CMD의 quoting, Windows path, execution policy, exit code 차이 때문에 script가 실패할 때 사용합니다.
---

# PowerShell / Windows

Windows shell 차이를 명시적으로 다뤄 같은 명령이 CMD와 PowerShell에서 다르게 동작하는 문제를 줄입니다.

## When to use

- PowerShell script, execution policy, quoting/escaping 문제
- Windows 경로와 공백, backslash 처리 문제
- `%ERRORLEVEL%`, `$LASTEXITCODE`, process exit code 판단 문제
- UTF-8/BOM 때문에 script나 설정 파일 해석이 달라질 때

## Workflow

1. 실제 shell이 CMD인지 PowerShell인지 먼저 확정합니다.
2. 경로·quote·escape·환경변수 문법을 해당 shell 기준으로 확인합니다.
3. 실행 정책이나 encoding을 필요한 범위에서만 수정합니다.
4. 명령의 stdout/stderr와 exit code를 분리해서 확인합니다.
5. 같은 Windows 환경에서 재실행 Evidence를 남깁니다.

## Boundaries

- Git commit/push/PR 자체는 `github-ops` 영역입니다.
- Linux shell 일반론이나 CI workflow 설계를 대신하지 않습니다.
- 시스템 전역 execution policy를 불필요하게 완화하지 않습니다.

## Evidence

사용한 shell, 정확한 command, exit code, path/encoding 조건과 재현 결과를 기록합니다.

## Stop / Handoff

관리자 권한, machine-wide policy 변경, credential 또는 외부 write가 필요하면 자동 진행하지 않습니다.

## Source / Provenance

- source_id: `v8.3-internal`
- license: `repository`
- provenance: V8.3 Candidate Review와 실제 Windows 운영 문제를 일반화해 새로 작성한 internal-original Skill입니다.

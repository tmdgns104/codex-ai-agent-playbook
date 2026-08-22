---
name: security-review
description: 인증, 권한, secret, 외부 입력, API 경계처럼 보안 영향이 있는 변경을 focused review할 때 사용합니다.
---

# Security Review

이 Skill은 보안 영향이 있는 변경에서만 사용합니다. 단순 문구 수정이나 보안 경계와 무관한 일반 리팩터링에는 사용하지 않습니다.

## 확인 순서

1. 변경된 신뢰 경계를 찾습니다.
2. 인증(authentication)과 권한(authorization)을 분리해서 확인합니다.
3. 외부 입력이 validation/normalization 없이 위험한 sink로 전달되는지 봅니다.
4. secret, token, password, 개인정보가 코드·로그·에러·테스트 fixture에 노출되는지 봅니다.
5. SQL/command/template/path 같은 injection 경계를 확인합니다.
6. 보안 관련 동작이 실패할 때 기본값이 안전한지 확인합니다.
7. 보안 변경을 증명할 focused test 또는 실행 Evidence가 있는지 확인합니다.

## 우선 확인 항목

- hard-coded credential 또는 secret
- 인증 우회 가능성
- 객체/리소스 단위 권한 누락
- 사용자 입력 기반 SQL/command/path/template 조립
- 민감정보 로그/에러 노출
- 위험한 기본 권한 확대
- 파일 업로드의 크기/종류/경로 검증 누락
- CORS/CSRF/session/cookie 설정 변경
- dependency 또는 외부 서비스 추가로 생긴 신뢰 경계

## Evidence

발견 사항은 가능하면 다음 형태로 남깁니다.

```text
위치
영향
재현 또는 공격 조건
근거
최소 수정 방향
검증 방법
```

확인하지 않은 취약점을 확정적으로 보고하지 않습니다.

## Stop / Handoff

다음은 자동 수정으로 밀어붙이지 않습니다.

- credential 사용
- 외부 권한 변경
- production 보안 설정 변경
- 데이터 접근 범위 확대
- destructive security migration

이 경우 STRICT profile과 Human Gate를 요구합니다.

## Source

ECC의 `security-review` 패턴을 참고했지만 Claude/특정 프레임워크 가정을 제거하고 Codex Playbook의 최소 Context/Evidence 정책에 맞게 재작성했습니다.

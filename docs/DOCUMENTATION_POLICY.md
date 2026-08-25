# 문서 작성 정책

이 저장소의 사용자·개발자 대상 문서는 **한국어를 기본 언어**로 작성합니다.

## 기본 원칙

1. README, 사용 가이드, 개발일지, 연구기록, 트러블슈팅 기록, 설계 설명은 한국어로 작성합니다.
2. 새로 추가하거나 갱신하는 설명 문장은 가능한 한 한국어로 통일합니다.
3. 코드, 명령어, 파일 경로, Git 브랜치명, commit SHA, Skill ID, 상태 enum, 테스트 이름처럼 실제 동작 계약에 사용되는 식별자는 원문을 유지합니다.
4. 외부 프로젝트·제품·라이브러리의 고유명사는 정확성을 위해 원문 표기를 유지할 수 있습니다.
5. 영어 기술 용어가 필요한 경우 한국어 설명을 함께 제공해 초보자도 의미를 따라갈 수 있게 합니다.
6. 문서는 현재 Repository Source of Truth와 검증 Evidence를 기준으로 최신화합니다.
7. 아직 원격에 반영되지 않은 로컬 Evidence는 원격 완료 상태와 구분해 명시합니다.
8. 실패·보류·REJECTED 결과도 삭제하지 않고 원인과 재발 방지까지 기록합니다.

## 문서와 코드 식별자의 구분

예를 들어 다음 식별자는 번역하지 않습니다.

```text
BENCHMARK_READY
REFERENCE_ONLY
REJECTED
STRICT
UNVERIFIED
v8.3-expert-skill-catalog
evaluation/external-skills/inspections.json
```

대신 주변 설명을 한국어로 작성합니다.

```text
BENCHMARK_READY
→ 실제 upstream 경로·내용·라이선스를 검사했고 다음 benchmark 단계로 진행 가능한 후보

REJECTED
→ 현재 고정 revision 기준으로 경로 부재, 라이선스 문제 등으로 후보에서 제외
```

이 규칙은 문서 가독성을 높이면서도 코드·테스트·자동화와의 이름 불일치를 막기 위한 것입니다.

## 최신화 원칙

문서의 숫자나 상태를 갱신할 때는 다음 우선순위를 따릅니다.

```text
실제 Git 상태
→ 실제 테스트 결과
→ 실제 생성 Artifact
→ Audit / Quality Gate 결과
→ 문서
```

LLM이나 Agent의 자기보고만으로 PASS 또는 완료 상태를 기록하지 않습니다.

## 적용 범위

이 정책은 앞으로 이 저장소에 추가하거나 갱신하는 문서에 적용합니다.

- `README.md`
- `README_KO.md`
- `docs/`
- `docs/history/`
- 버전 변경 기록
- Task 설명 중 사람이 읽는 설명 부분
- GitHub에서 제공하는 프로젝트 설명성 문서

기존 문서에서 영어 설명이 발견되면 기능 변경과 충돌하지 않는 범위에서 순차적으로 한국어로 정리합니다.

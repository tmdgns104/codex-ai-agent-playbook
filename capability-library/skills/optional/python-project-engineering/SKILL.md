---
name: python-project-engineering
description: pyproject.toml, package layout, virtual environment, entry point처럼 Python 프로젝트 구조와 실행 경계를 정리할 때 사용합니다.
---

# Python Project Engineering

Python 프로젝트가 실행·테스트·패키징 가능한 최소 구조를 갖추도록 정리합니다. 작은 프로젝트에 불필요한 계층을 강제하지 않습니다.

## When to use

- `pyproject.toml`, package/src layout, entry point를 정리할 때
- 가상환경과 interpreter가 서로 달라 재현성이 깨질 때
- test/lint/type 도구 위치와 package boundary를 일관되게 만들 때

## Workflow

1. 현재 실행 경로, interpreter, package import 경계를 확인합니다.
2. `pyproject.toml`과 실제 source/test layout의 불일치를 찾습니다.
3. 현재 규모에 필요한 최소 구조만 선택합니다.
4. entry point와 개발·테스트 명령이 같은 환경을 사용하게 맞춥니다.
5. import, test 또는 package build 중 가장 가까운 Evidence로 확인합니다.

## Boundaries

- dependency version upgrade 자체는 `dependency-upgrade` 영역입니다.
- FastAPI framework 구현이나 Python typing 전문 수정은 다루지 않습니다.
- 작은 script 하나를 이유로 src layout이나 packaging을 강제하지 않습니다.

## Evidence

변경한 구조, 사용한 interpreter/command, import 또는 test/build 결과와 남은 제약을 기록합니다.

## Stop / Handoff

패키지 공개, 외부 registry write, dependency 대규모 변경이 필요하면 해당 권한/전문 Skill로 넘깁니다.

## Source / Provenance

- source_id: `v8.3-internal`
- license: `repository`
- provenance: V8.3 Candidate Review에서 정의한 경계를 기반으로 새로 작성한 internal-original Skill입니다. Agent Skills 표준은 package 형식 참고에만 사용했습니다.

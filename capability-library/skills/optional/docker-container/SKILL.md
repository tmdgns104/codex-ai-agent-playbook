---
name: docker-container
description: Dockerfile 작성·검토, image 크기, build cache, multi-stage build, non-root, secret 노출처럼 container build 품질을 개선할 때 사용합니다.
---

# Docker Container

Container 작업은 **작고, 재현 가능하고, 최소 권한으로 실행되는 image**를 만드는 데 집중합니다. Kubernetes나 cloud deployment 전체 설계까지 자동으로 확장하지 않습니다.

## 언제 사용

- Dockerfile 작성·리뷰
- container image가 지나치게 큼
- build cache가 자주 깨짐
- multi-stage build 적용
- root 실행 / secret 포함 / 불필요한 build tool 제거
- `.dockerignore`, entrypoint, healthcheck 검토

## 기본 흐름

1. Repository의 runtime, build output, package manager를 확인합니다.
2. build stage와 runtime stage를 분리할 가치가 있는지 판단합니다.
3. dependency manifest를 source보다 먼저 복사해 cache 재사용을 높입니다.
4. final image에는 실행에 필요한 artifact만 남깁니다.
5. 가능한 경우 non-root user와 최소 권한을 사용합니다.
6. `.dockerignore`에서 `.git`, local cache, secret, 불필요한 build output을 제외합니다.
7. mutable `latest`나 불필요하게 큰 base image 사용을 검토합니다.
8. Repository가 가진 build/lint/scan 명령을 우선 실행합니다.
9. 실제 image build가 가능하면 build 성공과 runtime smoke path를 확인합니다.

## 원칙

- 보안 > 재현성 > 미세한 image size 절감
- base/runtime 선택은 언어와 native dependency 호환성을 먼저 봄
- Alpine을 무조건 최선으로 간주하지 않음
- shell-form CMD보다 signal 전달이 명확한 exec form을 선호
- secret을 Dockerfile `ARG`/`ENV`나 image layer에 넣지 않음
- cache 최적화 때문에 dependency correctness를 희생하지 않음

## 하지 말 것

- `chmod -R 777` 같은 광범위 권한으로 문제 우회
- build toolchain 전체를 final image에 남김
- `.env`, credential, private key를 image에 copy
- digest/version을 실제 확인하지 않고 가짜 pin 값을 작성
- 단순 Dockerfile 개선을 production 배포 작업으로 확대

## Evidence

최소 기록:

```text
검토한 Dockerfile/build context
변경 이유
실행한 build/lint/scan command
exit code
image/runtime 확인 결과
남은 compatibility/security gap
```

## Stop / Handoff

- registry push, cloud deployment, credential 사용은 별도 Permission/Human Gate 대상입니다.
- container 내부 애플리케이션 성능 병목은 `performance-profiling`으로 분리합니다.
- secret/auth boundary 문제가 발견되면 `security-review`를 고려합니다.

## Source

MIT 라이선스 `JayRHa/AgentSkills`의 `dockerfile-pro`에서 multi-stage, cache ordering, non-root, secret isolation, reproducible build 패턴을 참고했습니다. 특정 image/version을 강제하지 않고 Repository 환경과 V8.1 Gate 정책에 맞게 재작성했습니다.

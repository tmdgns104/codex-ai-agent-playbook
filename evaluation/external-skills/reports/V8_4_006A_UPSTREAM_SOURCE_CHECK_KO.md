# V8.4-006A Codex CLI Upstream Source Check

확인일: 2026-08-26

대상 upstream: `openai/codex` commit `a26f1806a4f4b8cfec2ea1be129963815a61e58c`

## 확인 내용

`codex-rs/exec/src/cli.rs` 기준으로 `codex exec`의 text 입력은 positional `PROMPT`이며,
PROMPT가 있는 상태에서 stdin이 pipe되면 stdin 내용은 별도 channel이 아니라 `<stdin>`
block으로 prompt에 append된다.

`codex-rs/utils/cli/src/shared_options.rs` 기준으로 별도 초기 첨부는 `--image`가 있고,
`--add-dir`는 primary workspace 옆에 추가 writable directory를 허용하는 옵션이다.
`--add-dir`를 model input context injection으로 해석할 근거는 없다.

검사한 CLI surface에는 V8.4가 요구하는 별도 verified text-context input/attachment가 없다.

## V8.4 판정

- `SEPARATE_VERIFIED_CONTEXT_V1`: **unsupported**
- `transport_conformance`: **false 유지**
- production context launch: **비활성 유지**

이번 source check는 006A의 simulation-only 분류와 같은 결론을 독립적으로 지지한다.
다만 사용자의 로컬 Codex binary 자체를 실행한 것은 아니므로, 향후 실제 probe가 필요하면
먼저 `codex --version`과 `codex exec --help`를 Evidence로 고정해야 한다.

Responses API 또는 다른 app-server adapter가 structured input을 제공하더라도 그것은 현재
`codex exec` adapter와 다른 transport다. 해당 경로 채택은 Architecture 변경으로 별도
검토해야 하며 이번 Task에서 자동 채택하지 않는다.

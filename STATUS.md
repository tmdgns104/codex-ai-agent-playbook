# Repository Status

- Updated: 2026-08-25
- Stable release: **V8.2 on `main`**
- Experimental branch: **`v8.3-expert-skill-catalog`**
- V8.4 state: **Experimental / Release Candidate**
- Global rollout: **NOT APPROVED**

## Current decision

V8.3 benchmark work and V8.4-001~006 implementation/verification are complete. The
V8.4 components remain an isolated experimental control plane and are not connected to
the existing launcher, Registry, global AGENTS, or an actual Codex transport.

Global rollout is not approved because:

1. Separate verified context transport has not been tested with an actual Codex backend.
2. Native Codex vs Current Playbook vs Adapted Context has not been compared under the
   frozen V8.4 contract.
3. V8.3 used one model and fixed fixtures; its promising adapted-context result is not
   sufficient generalization evidence.
4. The checked-in `kd-sympy` and `kd-citation-management` compiler outputs remain
   `DRAFT` and are not automatically approved.
5. V8.4-006A and V8.4-007 are not implemented.

## Version status

| Workstream | Status | Notes |
|---|---|---|
| V8.2 stable runtime | COMPLETE / RELEASED | `main`; existing install/update path |
| V8.3 benchmark | COMPLETE | Wave 1 and Wave 2 Evidence preserved separately |
| V8.4-001 | COMPLETE | Adapted context architecture design |
| V8.4-002 | COMPLETE | Versioned opt-in transport decision; real binding disabled |
| V8.4-003 | COMPLETE | Contract schemas, canonical hash, validator, fake backend |
| V8.4-004 | COMPLETE | Deterministic offline compiler; outputs remain `DRAFT` |
| V8.4-005 | COMPLETE | Selector and budget planner in shadow mode |
| V8.4-006 | COMPLETE | Session materializer/coordinator with fake backend only |
| V8.4-006A | NOT IMPLEMENTED | Actual Codex transport verification prohibited/not started |
| V8.4-007 | NOT IMPLEMENTED | Native/Current/Adapted controlled comparison not started |
| Global rollout | NOT APPROVED | Human Gate remains closed |

## Evidence snapshot

- V8.3 Wave 1: 2 PASS / 18 FAIL across 20 slots.
- V8.3 Wave 2: 8 PASS / 12 FAIL across 20 slots.
- V8.3 Wave 2 adapted-playbook: 5 PASS / 0 FAIL across 5 fixtures.
- V8.3 Wave 2 raw external vs adapted loaded context: 54,704 vs 2,799 UTF-8 bytes.
- V8.4-006 final cumulative regression: 245 PASS / 0 FAIL.
- V8.4 tests used schemas, deterministic fixtures, and a pure fake backend. They did not
  execute Codex, an LLM, Ollama, or a benchmark.

The V8.3 Wave 2 outcome is promising but not causal proof of context quality. Wave 2 also
changed validator/output-contract behavior, and all runs used one fixed model/configuration
and fixed fixtures.

The separate DNN practical experiment is not V8.3/V8.4 mainline acceptance Evidence. Its
worktree changes remain preserved in `stash@{0}` and are intentionally untouched by this
release-candidate documentation task.

## Repository hygiene

- V8.3 Evidence and V8.4-001~006 task/report artifacts are protected and unchanged.
- No obsolete zero-byte or clearly temporary benchmark artifact was found during the RC
  review; nothing was deleted.
- No DNN file was restored, modified, or deleted.
- No global installation or rollout action is authorized by this status.

## Next approved work

No next task starts automatically. A separate Human Gate is required before either:

1. V8.4-006A actual transport conformance work, or
2. V8.4-007 controlled Native/Current/Adapted comparison.

See [docs/V8.4_RELEASE_CANDIDATE_STATUS.md](docs/V8.4_RELEASE_CANDIDATE_STATUS.md)
for the release-candidate boundary, blockers, and rollback direction.

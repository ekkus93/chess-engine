#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_SPEC_2026-08-10.md"
TODO = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_TODO_2026-08-10.md"
CC = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md"


def replace_section(path: Path, start: str, end: str, replacement: str) -> None:
    text = path.read_text()
    a = text.index(start)
    b = text.index(end, a)
    path.write_text(text[:a] + replacement.rstrip() + "\n\n---\n\n" + text[b:])


spec_sc003 = r'''## 5. SC-003 — Replace CC-004's unverifiable promotion blocker with executable evidence

### 5.1 Defect and evidence-driven correction

CC-004's `documented blocker` disposition rested on an unverifiable prose claim that a bounded real-engine search found no legal route to a promotion-eligible position. SC-003 first converted that claim into a reproducible real-JNI probe rather than trusting the prose.

The probe itself disproved the blocker. Temporary evidence commit `8c4b8977fd202b8d84f3b8c1ef567c07041eec04` ran permanent evidence workflow `31447725972`, job `93645421851`, and preserved artifact `9085181028`. The bounded search used the real JNI `ChessEngine`, White as the human side, at most 12 human turns, beam width 24, branch cap 10, and the app-equivalent opponent policy of opening-book move when available and otherwise exact depth-1 search. It found:

```text
HUMAN_PATH=a2a3 a3a4 a4a5 b2b3 e2e3 a5a6 b3b4 c2c3 g2g3 a6b7
FOUND_MOVE=b7a8b
RESULT=FOUND
```

Therefore the old `documented blocker` is false and must not be preserved as the active disposition. SC-003 does not weaken or tune the probe to recover that blocker.

### 5.2 Final disposition — `ui-driven-path-built`

The discovered legal path makes a fixture seam unnecessary. SC-003 adds permanent instrumentation coverage starting from the normal production setup flow instead of adding any test-only FEN/position injection surface:

1. launch the real `MainActivity` and set engine depth 1 through the production setup control;
2. start the real high-level `ChessGame` session;
3. replay the discovered human path exclusively through real board-square taps, waiting for each real Rust engine reply;
4. reach `b7` with all four legal promotion moves (`b7a8q`, `b7a8r`, `b7a8b`, `b7a8n`);
5. tap `b7` then `a8` to open the real production promotion dialog;
6. tap the real **Bishop** choice; and
7. assert the authoritative post-move snapshot records `b7a8b`, the FEN contains a white bishop on `a8`, and the promotion-choice state is cleared.

No production/native position-loading API, Kotlin chess-rule logic, general FEN-loading feature, or ownership-model change is added. The temporary probe test/workflow were removed before the clean permanent source validation.

### 5.3 Tests and evidence

- The temporary real-JNI probe run `31447725972` / job `93645421851` / artifact `9085181028` is retained as historical evidence that the prior blocker was false and that the legal UI path was discovered empirically.
- Permanent Android run `31448304672` on exact source/test SHA `99a5ffd277db22c8a3d383e0206dfa6c010e4506` completed successfully.
- API-35 job `93647206317` compiled and ran the full connected suite, including `PromotionEndToEndInstrumentedTest`, successfully.
- Host-JVM JNI job `93647206339` and Android lint/unit job `93647206354` also completed successfully on that exact SHA.
- The obsolete temporary promotion probe test/workflow are absent from the validated source tree.
- CC-004's historical section is corrected provenance-preservingly: it records that its original blocker was later disproved and that SC-003 supplied the missing executable E2E coverage.
'''

replace_section(SPEC, "## 5. SC-003", "## 6. SC-004", spec_sc003)

todo_sc003 = r'''# SC-003: Replace CC-004's unverifiable promotion blocker with executable evidence

## SC-003.1 Fix

- [x] Checked the architectural boundary first: `ChessGame` has no arbitrary position/FEN injection and adding one solely for testing would expand production/native API surface, so no seam was added.
- [x] Converted the old blocker claim into a real, bounded, artifact-backed JNI search instead of accepting its prose assertion.
- [x] Evidence run `31447725972`, job `93645421851`, artifact `9085181028` disproved the blocker by finding a legal route within the original 12-human-turn bound.
- [x] Preserved discovered path: `a2a3 a3a4 a4a5 b2b3 e2e3 a5a6 b3b4 c2c3 g2g3 a6b7`, followed by promotion move `b7a8b`.
- [x] **Disposition reached:** `ui-driven-path-built`. The evidence made a fixture seam unnecessary and made `artifact-backed-blocker` factually invalid.

N/A — `seam-built`: no test-only or production position-injection seam was needed or added.

N/A — `artifact-backed-blocker`: the preserved real-JNI search found a promotion path, so retaining the blocker would be false.

- [x] Added `PromotionEndToEndInstrumentedTest`: normal production setup at depth 1, real board taps for the discovered path, real engine replies, real promotion dialog, Bishop tap, and authoritative `b7a8b`/white-bishop-on-`a8` snapshot assertions.
- [x] Temporary promotion probe test/workflow removed before clean permanent Android validation.

## SC-003.2 Tests

- [x] Historical discovery evidence: run `31447725972`, job `93645421851`, artifact `9085181028`; `RESULT=FOUND`, `FOUND_MOVE=b7a8b`.
- [x] Permanent Android source/test validation: run `31448304672` on exact SHA `99a5ffd277db22c8a3d383e0206dfa6c010e4506`, all three jobs successful.
- [x] API-35 connected job `93647206317` passed the full instrumentation suite including the real-flow promotion E2E test.
- [x] Host-JVM JNI job `93647206339` and Android lint/unit job `93647206354` also passed on the same SHA.
'''
replace_section(TODO, "# SC-003:", "# SC-004:", todo_sc003)

cc004 = r'''# CC-004: Fix AR-011 — add missing end-to-end promotion test — superseded by second-corrections SC-003

## CC-004.1 Historical disposition and correction

- [x] **Original CC-004 disposition:** `documented blocker`. CC-004 recorded that an unpreserved temporary JNI search had found no promotion path within 12 human turns and therefore did not add the requested E2E test.
- [x] **SC-003 correction:** the original blocker was not independently verifiable, so SC-003 reproduced it as an artifact-backed real-JNI search instead of trusting the prose.
- [x] That preserved search disproved the blocker: run `31447725972`, job `93645421851`, artifact `9085181028` found human path `a2a3 a3a4 a4a5 b2b3 e2e3 a5a6 b3b4 c2c3 g2g3 a6b7` and promotion move `b7a8b`.
- [x] **Current disposition:** `ui-driven-path-built`. Because a legal normal-start route exists, SC-003 added a real production-flow instrumentation test rather than a test-only position seam.
- [x] No production/native FEN or position-loading API and no Kotlin chess-rule logic were added.

## CC-004.2 Executable evidence added by SC-003

- [x] `PromotionEndToEndInstrumentedTest` starts from the real setup screen at depth 1, drives every human move through board taps, waits for the real Rust engine replies, opens the production promotion dialog through `b7` → `a8`, taps Bishop, and verifies authoritative move `b7a8b` with a white bishop on `a8`.
- [x] Permanent Android run `31448304672` on exact SHA `99a5ffd277db22c8a3d383e0206dfa6c010e4506` passed all three jobs; API-35 job `93647206317` executed the connected E2E test successfully.
- [x] The original CC-004 blocker remains documented above only as historical provenance; it is no longer treated as valid evidence or the active disposition.
'''
replace_section(CC, "# CC-004:", "# CC-005:", cc004)

subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=ROOT, check=True)
subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], cwd=ROOT, check=True)
subprocess.run(["git", "add", str(SPEC.relative_to(ROOT)), str(TODO.relative_to(ROOT)), str(CC.relative_to(ROOT))], cwd=ROOT, check=True)
subprocess.run(["git", "commit", "-m", "docs(android): record real promotion E2E correction"], cwd=ROOT, check=True)
subprocess.run(["git", "push", "origin", "HEAD:master"], cwd=ROOT, check=True)

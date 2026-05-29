# STRATEGY8 TODO

## Goal

Make the engine play **stronger practical chess from middlegame to conversion** by improving:

- **development and castling discipline**
- **king safety prioritization in heavy-piece phases**
- **winning-side conversion clarity**
- **endgame plan selection (king activation, passer push, simplification)**
- **move ordering and evaluation consistency for safe initiative**
- **regression coverage driven by recent depth-3 self-play**

This pass should build on `docs/STRATEGY7_TODO.md` and `docs/ENDGAME1_TODO.md`, not replace them. The latest depth-3 self-play transcript in `tmp/self_play_d3d3_until_end.txt` reached a natural finish, but still showed practical drift: early tempo loss, delayed king safety discipline, and occasional conversion inefficiency.

---

## Scope rules

- Keep legal move generation and board-rule correctness unchanged unless a regression reveals a direct bug.
- Preserve the public `Board` API where possible.
- Prefer structural evaluation, move ordering, and root-choice improvements over hard-coded move bans.
- Do not introduce randomness to fake stronger play.
- Define every major strategic change via tests plus transcript-backed positions.
- Every major phase must end with:

  ```bash
  python -m ruff check chess_game tests
  python -m mypy chess_game
  python -m pylint chess_game
  python -m pytest tests -q
  ```

- For AI-heavy phases, also run:

  ```bash
  python -m pytest tests/test_ai.py tests/test_ai_quality.py tests/test_ai_search.py tests/test_alpha_beta_pruning.py -q
  ```

- For phases that materially change strategic behavior, save at least one self-play transcript under `tmp/`.

---

# Task 0: Re-establish STRATEGY8 baseline from fresh self-play

## 0.1 Review the latest depth-3 self-play game

- [x] Review `tmp/self_play_d3d3_until_end.txt`.
- [x] Record:
  - [x] final result
  - [x] move count
  - [x] first opening tempo-loss sequence by either side
  - [x] first king-safety neglect sequence in a heavy-piece position
  - [x] first point where winning side had a cleaner simplification than chosen
  - [x] first point where repeated checks/maneuvers replaced a stronger plan

## 0.2 Create STRATEGY8 baseline artifact

- [x] Create `tmp/strategy8_baseline_positions.txt`.
- [x] Include at least 6 transcript-backed probe positions:
  - [x] opening development vs repeated knight/bishop/queen moves
  - [x] castling urgency vs side-pawn/edge play
  - [x] king safety under queen+rook pressure
  - [x] winning-side simplification opportunity
  - [x] passed-pawn push vs side activity
  - [x] anti-drift choice when ahead
- [x] Record current `evaluate()` and `get_best_move()` outputs for each probe.

## 0.3 Define measurable STRATEGY8 success criteria

- [x] Specify success metrics such as:
  - [x] fewer repeated non-forcing piece moves in opening/middlegame
  - [x] earlier castling when center is unstable
  - [x] fewer king-exposure decisions in queen+rook phases
  - [x] faster conversion after reaching clear advantage
  - [x] fewer low-value checks in won positions
  - [x] stronger endgame plan consistency around passer support

## 0.4 Phase note

- [x] Task 0 complete note
  - Baseline artifact: `tmp/strategy8_baseline_positions.txt`.
  - Captured six transcript-backed probes with current `evaluate()` and depth-3 `get_best_move()`.
  - Logged first tempo-loss, king-safety neglect, and conversion drift snapshots to anchor Tasks 1-4.

---

# Task 1: Opening discipline (development and castling priorities)

## 1.1 Add opening-discipline regressions

- [x] Add tests where engine should prefer development over repeated piece maneuvers.
- [x] Cover:
  - [x] avoiding same-piece move repetition before broad development
  - [x] developing minor pieces before early queen drift
  - [x] castling sooner when central files are opening

## 1.2 Add anti-tempo-loss heuristics

- [x] Audit current opening guidance and identify missing tempo-loss penalties.
- [x] Add/adjust scoring for:
  - [x] undeveloped back-rank minors
  - [x] repeated non-forcing minor-piece cycles
  - [x] queen development without tactical reason
  - [x] king still in center after castling windows open

## 1.3 Add opening move-order/root tie-break nudges

- [x] Prefer quiet moves that improve development and king safety.
- [x] Demote quiet moves that repeat with no tactical gain.
- [x] Ensure near-equal roots pick development+castling coherent plans.

## 1.4 Phase note

- [x] Task 1 complete note
  - Added `tests/test_ai_strategy8_regressions.py` for transcript-backed opening discipline checks.
  - Tuned `opening_move_ordering.py` to demote follow-up quiet queen redeploys and minor-piece retreats while king safety/development is unsettled.
  - Increased opening root tiebreak weight in `ai_search_helpers.py` so near-equal roots more strongly favor development/castling coherence.

---

# Task 2: King safety under heavy-piece pressure

## 2.1 Add king-safety regressions from transcript motifs

- [x] Add tests where side must prioritize king shelter over side activity.
- [x] Cover:
  - [x] preventing immediate file/diagonal invasion
  - [x] creating luft before speculative activity
  - [x] defending mating-net squares before pawn grabs

## 2.2 Expand safety evaluation signals

- [x] Audit king-safety scoring in `evaluation.py` and supporting guidance modules.
- [x] Add/tighten heuristics for:
  - [x] open/semi-open file pressure near king
  - [x] queen+rook battery lines against king zone
  - [x] overloaded defenders around king and promotion lanes
  - [x] unsafe king walks when tactical pressure is active

## 2.3 Strengthen safety-aware ordering and root behavior

- [x] Boost moves that directly reduce king danger.
- [x] Demote moves that ignore top threats.
- [x] In near-equal roots, prefer plans with lower king-exposure risk.

## 2.4 Phase note

- [x] Task 2 complete note
  - Added STRATEGY8 king-safety regressions in `tests/test_ai_defensive_strategy.py` for luft/defensive-priority behavior under queen+rook pressure.
  - Strengthened heavy-piece danger profiling in `defensive_priorities.py` and increased defense response weights in `threat_awareness.py` and `ai_search_helpers.py`.
  - Tightened activation gates for new heavy-invasion danger terms to preserve search speed and pre-existing strategy regressions.

---

# Task 3: Winning-side conversion discipline

## 3.1 Add conversion regressions for "cleanest win"

- [x] Add tests where winning side should choose practical simplification over drift.
- [x] Cover:
  - [x] favorable queen trades
  - [x] favorable rook trades
  - [x] eliminating opponent counterplay before side-pawn grabs
  - [x] forcing king cut-off before pawn race

## 3.2 Expand conversion heuristics

- [x] Audit `conversion_guidance.py` and downstream root tie-break hooks.
- [x] Add/tighten scoring for:
  - [x] conversion speed with safety preserved
  - [x] counterplay suppression priority
  - [x] main-passer support over secondary objectives
  - [x] avoiding perpetual-check risk while ahead

## 3.3 Add anti-drift rules for clearly better side

- [x] Demote repeated checks with no net gain.
- [x] Demote piece shuffles that do not improve mate, trade, or passer outcomes.
- [x] Prefer progress moves that change practical result.

## 3.4 Phase note

- [x] Task 3 complete note
  - Added STRATEGY8 conversion regression coverage in `tests/test_ai_strategy8_regressions.py` for simplification-vs-drift choice.
  - Tightened conversion anti-drift penalties in `conversion_guidance.py` to increase preference for practical conversion progress while ahead.

---

# Task 4: Endgame plan coherence (king activation, passer, simplification)

## 4.1 Add endgame-plan regressions

- [x] Add tests where engine should follow coherent plan in simplified positions.
- [x] Cover:
  - [x] king centralization over passive waiting
  - [x] supporting main passer over side play
  - [x] choosing simplification when it preserves winning race
  - [x] avoiding non-forcing checks that lose tempi

## 4.2 Tighten endgame plan guidance integration

- [x] Audit interactions among:
  - [x] `simple_endgame_guidance.py`
  - [x] `low_material_race_guidance.py`
  - [x] `low_material_coordination_guidance.py`
  - [x] `endgame_choice_guidance.py`
- [x] Remove conflicts that produce mixed or oscillating plan signals.

## 4.3 Add root-choice preference for coherent plan continuity

- [x] In near-equal endgame roots, prefer moves that continue strongest existing plan.
- [x] Avoid root choices that switch theaters without tactical justification.

## 4.4 Phase note

- [x] Task 4 complete note
  - Added STRATEGY8 endgame coherence regression in `tests/test_ai_strategy8_regressions.py` to prefer passer-file support over theater switching.
  - Tightened `endgame_choice_guidance.py` with a practical theater-switch penalty when clearly better and already committed to a passer plan.

---

# Task 5: Move ordering and evaluation consistency pass

## 5.1 Build consistency matrix for key motifs

- [x] Create `tmp/strategy8_consistency_audit.txt`.
- [x] For each motif, verify alignment between evaluation, quiet ordering, and root tie-break:
  - [x] development/castling
  - [x] king safety
  - [x] conversion discipline
  - [x] passer urgency
  - [x] anti-drift

## 5.2 Resolve contradictory incentives

- [x] Fix cases where evaluation rewards a plan but ordering/root demotes it (or vice versa).
- [x] Keep fixes narrow and motif-gated to avoid regressions in unrelated phases.

## 5.3 Add targeted consistency regressions

- [x] Add tests proving same strategic preference survives:
  - [x] static eval probe
  - [x] best-move choice at practical depth
  - [x] root tie-break among near-equal candidates

## 5.4 Phase note

- [x] Task 5 complete note
  - Added consistency audit artifact at `tmp/strategy8_consistency_audit.txt` with aligned eval/order/root snapshots for opening, king-safety, and endgame motifs.
  - Added STRATEGY8 consistency regression in `tests/test_ai_strategy8_regressions.py` validating aligned static eval, move ordering, and root best move for a king-safety motif.

---

# Task 6: Search stability for practical play

## 6.1 Add practical anti-oscillation regressions

- [x] Add tests where engine should avoid harmless repetition while better.
- [x] Add tests where engine should allow repetition while worse if it preserves best result.

## 6.2 Tune selective-search hooks for practical priorities

- [x] Audit selective extensions/reductions tied to checks, passers, and king threats.
- [x] Ensure forcing defensive/conversion lines are not pruned away too aggressively.
- [x] Avoid widening search in non-critical decorative lines.

## 6.3 Validate no timing regressions in depth-critical tests

- [x] Run existing timing-sensitive AI tests.
- [x] If needed, narrow heuristic activation gates rather than removing strategic logic.

## 6.4 Phase note

- [x] Task 6 complete note
  - Added anti-oscillation regression coverage in `tests/test_ai_strategy8_regressions.py` for repetition policy behavior (better side penalized, worse side repetition tolerated).
  - Tuned `ai_search_helpers.py` selective extension gating to avoid decorating undo/repetition moves with extra depth unless they are genuinely forcing/critical.
  - Confirmed no timing regressions on depth-critical search tests during the full Task 6 validation gate.

---

# Task 7: Transcript-driven review loop expansion

## 7.1 Generate fresh STRATEGY8 review games

- [ ] Save at least two fresh transcripts under `tmp/`:
  - [ ] one balanced depth-3 self-play game
  - [ ] one seeded continuation from a problematic baseline position

## 7.2 Extract new practical misses

- [ ] Create `tmp/strategy8_review.txt`.
- [ ] Record first recurring misses in:
  - [ ] opening discipline
  - [ ] king safety
  - [ ] conversion discipline
  - [ ] endgame plan coherence

## 7.3 Promote misses to regression tests

- [ ] Add/extend STRATEGY8-focused regression tests in appropriate test modules.
- [ ] Ensure each miss has at least one deterministic test that fails before fix and passes after.

## 7.4 Phase note

- [ ] Task 7 complete note

---

# Task 8: Final acceptance and closeout

## 8.1 Full validation gate

- [ ] Run and pass:
  - [ ] `python -m ruff check chess_game tests`
  - [ ] `python -m mypy chess_game`
  - [ ] `python -m pylint chess_game`
  - [ ] `python -m pytest tests -q`
  - [ ] `python -m pytest tests/test_ai.py tests/test_ai_quality.py tests/test_ai_search.py tests/test_alpha_beta_pruning.py -q`

## 8.2 Acceptance self-play

- [ ] Run at least one full depth-3 vs depth-3 self-play to natural termination.
- [ ] Save transcript in `tmp/strategy8_task8_acceptance_*.txt`.
- [ ] Verify practical improvements against Task 0 success criteria.

## 8.3 Document final outcome

- [ ] Update this file with completion notes per task.
- [ ] Summarize residual weaknesses and recommended STRATEGY9 candidates.

## 8.4 Phase note

- [ ] Task 8 complete note

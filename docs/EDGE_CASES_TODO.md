# Edge Case Tests TODO

## Overview
Strengthen test coverage for chess engine edge cases. Focus on scenarios that expose subtle bugs.

---

## Category 1: Castling Edge Cases

### T1.1 Castling when rook was captured on original square
**Scenario**: Opponent captures white's kingside rook on h1, then white attempts kingside castling.
**Expected**: Castling forbidden (rook no longer on h1).

**Test cases**:
- [x] Black captures h1 rook, white cannot castle kingside
- [x] Verify rook removal clears castling right
- [x] Verify castling right clears if rook moves elsewhere

---

### T1.2 Castling when opponent's piece occupies rook's original square
**Scenario**: Black pawn on h1 (illegal but for testing), white attempts kingside castling.
**Expected**: Castling blocked by piece in path.

**Test cases**:
- [x] Path check includes opponent pieces
- [x] Castling blocked if enemy piece on destination square

---

### T1.3 Castling when only one rook remains on back rank
**Scenario**: One rook moved, other rook remains. Attempt castling with remaining rook.
**Expected**: Castling forbidden (castling rights cleared when any rook moves).

**Test cases**:
- [x] Queenside: kingside rook moved, queenside rook remains
- [x] Kingside: queenside rook moved, kingside rook remains

---

### T1.4 Castling when rook moved and replaced on original square
**Scenario**: Rook moves from h1, then another rook replaces it. White castles kingside.
**Expected**: Castling forbidden (original rook moved).

**Test cases**:
- [x] Verify castling right clears when original rook leaves
- [x] Replacement rook doesn't restore castling right

---

## Category 2: En Passant Edge Cases

### T2.1 Multiple en passant targets
**Scenario**: Two pawns make double steps in same turn.
**Expected**: Should never happen in legal play; verify engine doesn't allow.

**Test cases**:
- [ ] Verify only one en_passant_target at a time
- [ ] Capture uses correct target square

---

### T2.2 En passant when pawn to be captured moved before
**Scenario**: White pawn at e5, black pawn at d7. Black moves d7-d5. White tries en passant on d5.
**Expected**: En passant available (standard case).

**Test cases**:
- [ ] Verify standard en passant works
- [ ] Verify capture removes pawn from original square

---

### T2.3 En passant when opponent makes non-pawn move
**Scenario**: Black plays d7-d5, then white plays Nf3 (non-pawn move).
**Expected**: En passant expires (must be used immediately).

**Test cases**:
- [ ] en_passant_target cleared after any move
- [ ] Cannot capture en passant after opponent's non-pawn move

---

### T2.4 En passant with checking scenarios
**Scenario**: En passant capture that would leave king in check.
**Expected**: En passant illegal.

**Test cases**:
- [ ] En passant blocked if destination square attacked
- [ ] En passant blocked if path through attacked square
- [ ] En passant blocked if after capture, king in check

---

### T2.5 En passant from starting position
**Scenario**: Standard opening position, white plays e2-e4, black responds d7-d5, white plays e5d6 (en passant).
**Expected**: Valid en passant capture.

**Test cases**:
- [ ] Full game scenario: e2e4 d7d5 e5d6
- [ ] Verify pawn removed from e5
- [ ] Verify white pawn lands on d6

---

## Category 3: Promotion Edge Cases

### T3.1 Promotion when in check
**Scenario**: Pawn on 7th rank, king in check. Pawn promotes.
**Expected**: Must resolve check first; promotion move illegal if leaves king in check.

**Test cases**:
- [ ] Promotion that doesn't resolve check is illegal
- [ ] Promotion to piece that blocks check is legal
- [ ] Promotion to piece that captures checking piece is legal

---

### T3.2 Promotion that would leave king in check
**Scenario**: Pawn promotes to a piece that doesn't block check.
**Expected**: Illegal move.

**Test cases**:
- [ ] Verify move simulation checks king safety after promotion
- [ ] All promotion types validated for legality

---

### T3.3 Promotion from non-standard pawn positions
**Scenario**: Pawn promoted before reaching last rank (impossible in legal play).
**Expected**: Should not be reachable in normal play; verify engine rejects.

**Test cases**:
- [ ] Verify pawn cannot promote before last rank
- [ ] Promotion only on rank 1 (white) or rank 8 (black)

---

### T3.4 All promotion piece types
**Scenario**: Test all four promotion choices.
**Expected**: Queen, rook, bishop, knight all work; king rejected.

**Test cases**:
- [ ] Promotion to queen (explicit and default)
- [ ] Promotion to rook
- [ ] Promotion to bishop
- [ ] Promotion to knight
- [ ] Promotion to king (rejected)

---

### T3.5 Promotion with en passant on same turn
**Scenario**: Impossible (promotion requires reaching last rank, en passant requires adjacent pawn).
**Expected**: Not applicable; just verify logic doesn't break.

**Test cases**:
- [ ] No interaction needed between promotion and en passant

---

## Category 4: King Safety & Pinning Edge Cases

### T4.1 Absolute pin: pinned piece cannot move
**Scenario**: King on e1, rook on e2, bishop on a8. White bishop on h1 pins rook.
**Expected**: Rook cannot move (would expose king).

**Test cases**:
- [ ] Pinned rook cannot move forward
- [ ] Pinned rook cannot move backward
- [ ] Pinned rook cannot move sideways
- [ ] Pinned rook can be captured

---

### T4.2 Relative pin: pinned piece can move
**Scenario**: Queen on d1, bishop on d4, rook on d7. White rook on h3 pins queen.
**Expected**: Queen can move (not protecting king).

**Test cases**:
- [ ] Relatively pinned piece can move
- [ ] Relative pin doesn't prevent movement

---

### T4.3 Double pin: impossible situation
**Scenario**: King pinned in two directions simultaneously.
**Expected**: Cannot happen in legal play; verify engine handles gracefully.

**Test cases**:
- [ ] Engine doesn't crash on double pin
- [ ] At least one pinned piece can move

---

### T4.4 King move into pin
**Scenario**: King moves to square where it becomes pinned.
**Expected**: King move legal (pinning doesn't affect legality of being pinned).

**Test cases**:
- [ ] King can move into pin
- [ ] King can move out of pin

---

## Category 5: Checkmate & Stalemate Edge Cases

### T5.1 Checkmate with pinned king
**Scenario**: King can't move because all squares attacked, but king is pinned.
**Expected**: Checkmate (no legal moves).

**Test cases**:
- [ ] Checkmate detected even if king pinned
- [ ] No legal moves = checkmate if in check

---

### T5.2 Stalemate with pinned king
**Scenario**: Not in check, but only moves expose king to check.
**Expected**: Stalemate (no legal moves, not in check).

**Test cases**:
- [ ] Stalemate detected when all moves expose king
- [ ] Not in check + zero legal moves = stalemate

---

### T5.3 Checkmate with promotion
**Scenario**: Forced mate involves pawn promotion.
**Expected**: Mate detected after promotion.

**Test cases**:
- [ ] Promotion followed by mate
- [ ] Promotion move counted as legal move

---

### T5.4 Stalemate after promotion
**Scenario**: Pawn promotes to create stalemate.
**Expected**: Game ends in stalemate.

**Test cases**:
- [ ] Promotion creates stalemate position
- [ ] Stalemate detected after promotion

---

## Category 6: Corner & Edge Cases

### T6.1 Corner square interactions
**Scenario**: Piece on a1, a8, h1, h8.
**Expected**: Movement rules apply normally.

**Test cases**:
- [ ] Rook from corner moves along edge only
- [ ] Bishop from corner has limited range
- [ ] Knight from corner has 2 moves
- [ ] King from corner has 3 moves

---

### T6.2 Edge file interactions (a and h files)
**Scenario**: Piece on a-file or h-file.
**Expected**: Movement rules apply normally.

**Test cases**:
- [ ] Rook from edge cannot move off board
- [ ] Bishop from edge has limited range
- [ ] Knight from edge has reduced moves

---

### T6.3 Edge rank interactions (1 and 8 ranks)
**Scenario**: Piece on rank 1 or rank 8.
**Expected**: Movement rules apply normally.

**Test cases**:
- [ ] White pawn on rank 1 cannot move forward
- [ ] Black pawn on rank 8 cannot move forward
- [ ] Edge rank pawn promotion scenarios

---

## Category 7: Complex Sequences

### T7.1 Long forcing sequence
**Scenario**: 5+ moves of forced checks leading to mate.
**Expected**: All moves legal, mate detected.

**Test cases**:
- [ ] Forced mate sequence (e.g., Scholar's Mate)
- [ ] All intermediate checks handled
- [ ] Mate detected at correct time

---

### T7.2 Draw by stalemate
**Scenario**: Intentional stalemate sequence.
**Expected**: Game ends in stalemate.

**Test cases**:
- [ ] Stalemate sequence from opening
- [ ] Stalemate detected correctly

---

### T7.3 Complex en passant sequence
**Scenario**: Multiple en passant captures in a game.
**Expected**: Each en passant valid, state updates correctly.

**Test cases**:
- [ ] First en passant capture
- [ ] Second en passant capture
- [ ] State resets correctly between captures

---

## Category 8: Castling Safety Edge Cases

### T8.1 Castling through discovered check
**Scenario**: King castles while piece behind it is giving check.
**Expected**: Castling forbidden if king passes through or ends on attacked square.

**Test cases**:
- [ ] Cannot castle if square behind king attacked
- [ ] Check detection includes discovered attacks

---

### T8.2 Castling when king and rook both attacked
**Scenario**: Both king and rook under attack during castling.
**Expected**: Castling forbidden.

**Test cases**:
- [ ] Castling blocked if king square attacked
- [ ] Castling blocked if destination attacked
- [ ] Castling blocked if path through attacked square

---

## Category 9: Board State Edge Cases

### T9.1 Impossible board states
**Scenario**: Two kings of same color, no king of other color.
**Expected**: Engine should handle gracefully (not crash).

**Test cases**:
- [ ] Engine doesn't crash with missing king
- [ ] Engine doesn't crash with extra king

---

### T9.2 Missing pieces
**Scenario**: All pawns captured, only major pieces remain.
**Expected**: Engine handles normal play.

**Test cases**:
- [ ] Play continues with few pieces
- [ ] No crashes with minimal pieces

---

### T9.3 Full board occupancy
**Scenario**: Maximum pieces on board (starting position).
**Expected**: All movement rules work correctly.

**Test cases**:
- [ ] All piece types move correctly from starting position
- [ ] Path blocking works with full board

---

## Category 10: Turn & Color Edge Cases

### T10.1 Alternating turns
**Scenario**: Many moves, verify turn alternation.
**Expected**: White, black, white, black...

**Test cases**:
- [ ] Turn alternates correctly after each move
- [ ] 100 moves later, correct side to move

---

### T10.2 Color confusion attacks
**Scenario**: Attempt to move opponent's piece.
**Expected**: Move rejected.

**Test cases**:
- [ ] Cannot move opponent's piece
- [ ] Cannot capture own piece

---

### T10.3 Pawn direction confusion
**Scenario**: White pawn moving "down" (increasing row), black pawn moving "up".
**Expected**: White moves toward row 0, black moves toward row 7.

**Test cases**:
- [ ] White pawn forward = row - 1
- [ ] Black pawn forward = row + 1
- [ ] White pawn capture = row - 1
- [ ] Black pawn capture = row + 1

---

## Category 11: Path Blocking Edge Cases

### T11.1 Rook path: adjacent blocking
**Scenario**: Rook has piece immediately adjacent in path.
**Expected**: Move blocked.

**Test cases**:
- [ ] Rook blocked by piece on immediate square
- [ ] Rook blocked by piece on any square in path

---

### T11.2 Bishop path: diagonal blocking
**Scenario**: Bishop with piece on diagonal path.
**Expected**: Move blocked.

**Test cases**:
- [ ] Bishop blocked by piece on diagonal
- [ ] Bishop blocked by friendly piece
- [ ] Bishop blocked by enemy piece

---

### T11.3 Queen path: combined blocking
**Scenario**: Queen with blocking pieces in different directions.
**Expected**: Each direction checked independently.

**Test cases**:
- [ ] Queen blocked in rook direction
- [ ] Queen blocked in bishop direction
- [ ] Queen can move in unblocked directions

---

## Category 12: Knight & King Special Cases

### T12.1 Knight: all 8 squares
**Scenario**: Knight on center square, all 8 target squares available.
**Expected**: All 8 moves valid.

**Test cases**:
- [ ] Knight has 8 moves from center (if empty board)
- [ ] Knight jumps over all pieces

---

### T12.2 Knight: edge and corner
**Scenario**: Knight on edge or corner.
**Expected**: Fewer valid moves.

**Test cases**:
- [ ] Knight on a1 has 2 moves
- [ ] Knight on edge has 4-6 moves
- [ ] Knight on center has 8 moves

---

### T12.3 King: all directions
**Scenario**: King on center square.
**Expected**: 8 possible moves.

**Test cases**:
- [ ] King can move to all 8 adjacent squares
- [ ] King blocked by pieces
- [ ] King cannot move to attacked square

---

## Category 13: Interaction Between Rules

### T13.1 Castling + check
**Scenario**: Castling while in check.
**Expected**: Castling forbidden.

**Test cases**:
- [ ] Cannot castle while in check
- [ ] Cannot castle through check
- [ ] Cannot castle into check

---

### T13.2 En passant + check
**Scenario**: En passant capture while in check.
**Expected**: En passant must resolve check or be illegal.

**Test cases**:
- [ ] En passant that resolves check is legal
- [ ] En passant that doesn't resolve check is illegal

---

### T13.3 Promotion + check
**Scenario**: Promotion while in check.
**Expected**: Promotion must resolve check.

**Test cases**:
- [ ] Promotion resolving check is legal
- [ ] Promotion not resolving check is illegal

---

### T13.4 Pin + en passant
**Scenario**: Pawn pinned, but en passant available.
**Expected**: En passant can move pinned piece (not a regular move).

**Test cases**:
- [ ] En passant can be made even if "pinned"
- [ ] King safety still checked for en passant

---

## Category 14: Multiple Piece Types

### T14.1 All piece types from starting position
**Scenario**: Standard opening position, all pieces move once.
**Expected**: All pieces can move at least once.

**Test cases**:
- [x] All rooks, knights, bishops, queens can move
- [x] Both kings can move

---

### T14.2 Mixed piece interactions
**Scenario**: All piece types on board interacting.
**Expected**: Complex interactions handled correctly.

**Test cases**:
- [x] Pieces can capture each other
- [x] Pieces can block each other
- [x] Pieces can pin each other

---

## Category 15: Coordinate System Edge Cases

### T15.1 Boundary tests
**Scenario**: Moves on board boundaries.
**Expected**: All moves within bounds.

**Test cases**:
- [x] Move off board rejected
- [x] Edge squares move correctly
- [x] Corner squares move correctly

---

### T15.2 Round-trip conversion
**Scenario**: Convert coordinate to index and back.
**Expected**: Original coordinate recovered.

**Test cases**:
- [x] All 64 squares convert correctly
- [x] Index to algebraic is inverse

---

## Priority Matrix

| Priority | Categories | Estimated Tests |
|----------|-----------|-----------------|
| **High** | 1 (Castling), 2 (En passant), 3 (Promotion) | 15-20 |
| **Medium** | 4 (Pinning), 5 (Checkmate/Stalemate), 8 (Castling safety) | 20-30 |
| **Low** | 6-15 (Edge cases, interactions) | 30-50 |

---

## Implementation Notes

### Testing Approach
1. Use isolated board setups for each test
2. Clear board between tests
3. Use fixtures for common setups
4. Test both white and black perspectives

### Test Naming Convention
```
test_{category}_{scenario}_{expected_result}
```

Examples:
- `test_castling_rook_captured_forbidden`
- `test_en_passant_expired_after_nonpawn_move`
- `test_promotion_in_check_must_resolve`

### Verification Checklist
After adding tests:
- [ ] All tests pass
- [ ] No new lint errors
- [ ] No type errors
- [ ] Tests are readable
- [ ] Edge cases are actually tested (not just passing)

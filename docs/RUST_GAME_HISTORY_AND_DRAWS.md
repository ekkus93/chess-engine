# Rust Game History and Draw Semantics

This document defines the `chess-core` game-state, repetition-history, terminal-state, and draw contract introduced by Task 10.

## Position and game boundary

`Position` remains a history-free representation of one chess position. It owns board state, side to move, castling rights, en-passant state, clocks, and the canonical Zobrist repetition identity, but it does not own played moves or prior positions.

`Game` is the history-owning layer. It owns:

- the current `Position`;
- every played `Move` in chronological order;
- every canonical position hash from the root through the current position.

Mutable access to the underlying position is intentionally not exposed. All game moves pass through `Game::make_move`, so position state, played moves, and repetition history remain synchronized. Illegal moves and mismatched undo tokens are rejected before either position or history changes.

## Repetition history

The current repetition count is computed from the canonical Task 9 Zobrist key. Only the reversible history window is searched: at most the current halfmove clock plus the current position. Identities before the most recent pawn move or capture cannot contribute to a repetition claim.

The root position is counted once. Every successfully played move appends the resulting position key. `GameUndo` restores the exact previous position, move list, and hash history in last-in, first-out order.

## Status model

`GameStatus` distinguishes:

- `Ongoing`;
- `Checkmate { winner }`;
- `Stalemate`;
- `ClaimableDraw(reason)`;
- `AutomaticDraw(reason)`.

Claimable draws do not automatically prevent further play. A higher-level game controller may accept a valid claim. Automatic draws, checkmate, and stalemate are terminal and cause `Game::make_move` to reject further moves.

## Claimable draws

A draw is claimable when either condition is true:

- the current canonical position has occurred at least three times in known reversible history;
- the halfmove clock is at least 100, representing fifty moves by each side without a pawn move or capture.

`Game::draw_claims()` exposes both booleans independently. If both are available, `Game::status()` reports threefold repetition first while the complete claim set remains available through `DrawClaims`.

## Automatic draws

A draw is automatic when any of these conditions is true:

- the current canonical position has occurred at least five times;
- the halfmove clock is at least 150, representing seventy-five moves by each side without a pawn move or capture;
- the position is conservatively proven dead.

Checkmate and stalemate are evaluated before move-count and repetition draws. Therefore, a mating move remains checkmate even when it also reaches the seventy-five-move threshold.

## Conservative dead-position recognition

`Position::is_dead_position()` returns true only for material classes that this implementation proves cannot reach checkmate through any legal continuation:

- king against king;
- king and one bishop against king;
- king and one knight against king;
- bishops-only positions in which every bishop is confined to the same square color.

The detector deliberately returns false when the board contains a pawn, rook, or queen; a knight plus another minor piece; two knights; bishop versus knight; or bishops spanning both square colors. This avoids unsafe broad shortcuts such as treating every two-minor-piece position as an automatic draw.

## Search history

`Game::search_history()` creates a detached `SearchHistory` containing a copy of the root game hashes. Search code may push and pop line positions with opaque LIFO tokens. These operations cannot mutate the game’s move list or repetition history.

`SearchHistory::from_position()` supports searches that start from a standalone position with no known prior game history. Repetition counting uses the same reversible halfmove boundary as `Game`.

## Verification contract

Task 10 tests cover:

- exact move and hash-history recording and undo;
- LIFO mismatch rejection without mutation;
- illegal game moves leaving both position and history unchanged;
- checkmate and stalemate distinction;
- threefold-to-fivefold repetition transitions;
- exact 100- and 150-halfmove thresholds;
- checkmate precedence at the seventy-five-move threshold;
- conservative dead-position positive and negative fixtures;
- terminal game-move rejection;
- irreversible repetition-window boundaries;
- detached search-history push, pop, and mismatch behavior.

Task 11 may use `Game`, `Position`, and `SearchHistory` as authoritative rule-state inputs while expanding perft and differential validation.

## Root replacement

`Game::reset_to_starting()` replaces the game with a fresh standard starting position. `Game::set_position(Position)` establishes a caller-supplied validated position as a new root. Both operations clear the played-move list and replace position-hash history with exactly one root key. Prior repetition history is never merged into the new root, and old `GameUndo` tokens cannot be applied successfully after replacement.

These APIs are infallible because `Position` values are already structurally validated. They provide the explicit state-replacement semantics needed by future UCI `ucinewgame` and `position` handling without exposing mutable access to the internal position.
